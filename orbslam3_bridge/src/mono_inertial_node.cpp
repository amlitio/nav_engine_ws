#include <cmath>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

#include <Eigen/Core>
#include <Eigen/Geometry>
#include <builtin_interfaces/msg/time.hpp>
#include <cv_bridge/cv_bridge.h>
#include <nav_msgs/msg/odometry.hpp>
#include <opencv2/imgproc.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/image_encodings.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/imu.hpp>

#include "System.h"

class MonoInertialNode : public rclcpp::Node
{
public:
  MonoInertialNode()
  : Node("orbslam3_mono_inertial")
  {
    this->declare_parameter<std::string>("vocab_file", "");
    this->declare_parameter<std::string>("settings_file", "");
    this->declare_parameter<bool>("enable_viewer", false);

    const auto vocab_path = this->get_parameter("vocab_file").as_string();
    const auto settings_path = this->get_parameter("settings_file").as_string();
    const bool enable_viewer = this->get_parameter("enable_viewer").as_bool();

    if (vocab_path.empty() || settings_path.empty()) {
      throw std::runtime_error("vocab_file and settings_file parameters must be provided.");
    }

    slam_ = std::make_unique<ORB_SLAM3::System>(
      vocab_path,
      settings_path,
      ORB_SLAM3::System::IMU_MONOCULAR,
      enable_viewer);

    auto image_qos = rclcpp::SensorDataQoS();
    auto imu_qos = rclcpp::SensorDataQoS();

    imu_sub_ = this->create_subscription<sensor_msgs::msg::Imu>(
      "/drone/imu",
      imu_qos,
      std::bind(&MonoInertialNode::ImuCallback, this, std::placeholders::_1));

    img_sub_ = this->create_subscription<sensor_msgs::msg::Image>(
      "/drone/camera/image_raw",
      image_qos,
      std::bind(&MonoInertialNode::ImageCallback, this, std::placeholders::_1));

    odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>(
      "/nav_engine/visual_odom", 10);

    RCLCPP_INFO(this->get_logger(), "ORB-SLAM3 mono-inertial bridge initialized.");
  }

  ~MonoInertialNode() override
  {
    if (slam_) {
      slam_->Shutdown();
    }
  }

private:
  std::unique_ptr<ORB_SLAM3::System> slam_;
  std::vector<ORB_SLAM3::IMU::Point> imu_buffer_;
  std::mutex imu_mutex_;

  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr img_sub_;
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;

  static double ToSeconds(const builtin_interfaces::msg::Time & stamp)
  {
    return static_cast<double>(stamp.sec) +
           static_cast<double>(stamp.nanosec) * 1e-9;
  }

  void ImuCallback(const sensor_msgs::msg::Imu::SharedPtr msg)
  {
    std::lock_guard<std::mutex> lock(imu_mutex_);

    const double timestamp = ToSeconds(msg->header.stamp);

    imu_buffer_.emplace_back(
      msg->linear_acceleration.x,
      msg->linear_acceleration.y,
      msg->linear_acceleration.z,
      msg->angular_velocity.x,
      msg->angular_velocity.y,
      msg->angular_velocity.z,
      timestamp);
  }

  void ImageCallback(const sensor_msgs::msg::Image::SharedPtr msg)
  {
    cv_bridge::CvImageConstPtr cv_ptr;

    try {
      if (msg->encoding == sensor_msgs::image_encodings::MONO8) {
        cv_ptr = cv_bridge::toCvShare(msg, sensor_msgs::image_encodings::MONO8);
      } else {
        auto color_ptr = cv_bridge::toCvCopy(msg, sensor_msgs::image_encodings::BGR8);
        cv::Mat gray;
        cv::cvtColor(color_ptr->image, gray, cv::COLOR_BGR2GRAY);
        cv_ptr = cv_bridge::CvImage(msg->header, sensor_msgs::image_encodings::MONO8, gray).toCvCopy();
      }
    } catch (const cv_bridge::Exception & e) {
      RCLCPP_ERROR(this->get_logger(), "cv_bridge exception: %s", e.what());
      return;
    }

    std::vector<ORB_SLAM3::IMU::Point> imu_meas;
    {
      std::lock_guard<std::mutex> lock(imu_mutex_);
      imu_meas = imu_buffer_;
      imu_buffer_.clear();
    }

    const double timestamp = ToSeconds(msg->header.stamp);

    Sophus::SE3f Tcw = slam_->TrackMonocularInertial(
      cv_ptr->image,
      timestamp,
      imu_meas);

    const Eigen::Vector3f tcw = Tcw.translation();
    if (!std::isfinite(tcw.x()) || !std::isfinite(tcw.y()) || !std::isfinite(tcw.z())) {
      return;
    }

    Sophus::SE3f Twc = Tcw.inverse();
    PublishOdometry(Twc, msg->header.stamp);
  }

  void PublishOdometry(const Sophus::SE3f & Twc, const builtin_interfaces::msg::Time & stamp)
  {
    nav_msgs::msg::Odometry odom;
    odom.header.stamp = stamp;
    odom.header.frame_id = "odom";
    odom.child_frame_id = "camera_link";

    const Eigen::Vector3f t = Twc.translation();
    const Eigen::Quaternionf q = Twc.unit_quaternion();

    odom.pose.pose.position.x = static_cast<double>(t.x());
    odom.pose.pose.position.y = static_cast<double>(t.y());
    odom.pose.pose.position.z = static_cast<double>(t.z());

    odom.pose.pose.orientation.x = static_cast<double>(q.x());
    odom.pose.pose.orientation.y = static_cast<double>(q.y());
    odom.pose.pose.orientation.z = static_cast<double>(q.z());
    odom.pose.pose.orientation.w = static_cast<double>(q.w());

    odom_pub_->publish(odom);
  }
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  try {
    auto node = std::make_shared<MonoInertialNode>();
    rclcpp::spin(node);
  } catch (const std::exception & e) {
    RCLCPP_FATAL(rclcpp::get_logger("orbslam3_mono_inertial"), "Fatal error: %s", e.what());
  }

  rclcpp::shutdown();
  return 0;
}
