#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <cv_bridge/cv_bridge.h>
#include <mutex>
#include <queue>

// Include the real ORB-SLAM3 System Header
#include "System.h" 

class MonoInertialNode : public rclcpp::Node {
public:
    MonoInertialNode(ORB_SLAM3::System* pSLAM) 
        : Node("orbslam3_mono_inertial"), mpSLAM(pSLAM) {
        
        // Quality of Service (QoS) profile for high-frequency sensor data
        rclcpp::QoS qos(rclcpp::KeepLast(10));
        qos.best_effort();

        // Subscriptions
        imu_sub_ = this->create_subscription<sensor_msgs::msg::Imu>(
            "/drone/imu", 1000, std::bind(&MonoInertialNode::ImuCallback, this, std::placeholders::_1));
            
        img_sub_ = this->create_subscription<sensor_msgs::msg::Image>(
            "/drone/camera/image_raw", qos, std::bind(&MonoInertialNode::ImageCallback, this, std::placeholders::_1));

        // Publisher for the visual odometry output
        odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>("/nav_engine/visual_odom", 10);
        
        RCLCPP_INFO(this->get_logger(), "ORB-SLAM3 Mono-Inertial Bridge Initialized.");
    }

private:
    ORB_SLAM3::System* mpSLAM;
    std::vector<ORB_SLAM3::IMU::Point> vImuMeas;
    std::mutex mImuMutex;

    void ImuCallback(const sensor_msgs::msg::Imu::SharedPtr msg) {
        std::lock_guard<std::mutex> lock(mImuMutex);
        double timestamp = msg->header.stamp.sec + msg->header.stamp.nanosec * 1e-9;
        
        // ORB-SLAM3 expects: acceleration (x,y,z), gyroscope (x,y,z), timestamp
        vImuMeas.push_back(ORB_SLAM3::IMU::Point(
            msg->linear_acceleration.x, msg->linear_acceleration.y, msg->linear_acceleration.z,
            msg->angular_velocity.x, msg->angular_velocity.y, msg->angular_velocity.z,
            timestamp));
    }

    void ImageCallback(const sensor_msgs::msg::Image::SharedPtr msg) {
        cv_bridge::CvImagePtr cv_ptr;
        try {
            cv_ptr = cv_bridge::toCvCopy(msg, sensor_msgs::image_encodings::MONO8);
        } catch (cv_bridge::Exception& e) {
            RCLCPP_ERROR(this->get_logger(), "cv_bridge exception: %s", e.what());
            return;
        }

        double timestamp = msg->header.stamp.sec + msg->header.stamp.nanosec * 1e-9;
        
        // Grab the IMU measurements that have accumulated since the last image
        std::vector<ORB_SLAM3::IMU::Point> vImuMeas_current;
        {
            std::lock_guard<std::mutex> lock(mImuMutex);
            vImuMeas_current = vImuMeas;
            vImuMeas.clear(); 
        }

        // Pass the image and IMU history to the SLAM engine
        Sophus::SE3f Tcw = mpSLAM->TrackMonocularInertial(cv_ptr->image, timestamp, vImuMeas_current);

        // If tracking is successful and we have a valid pose, publish it
        if (!Tcw.translation().hasNaN()) {
            PublishOdometry(Tcw, msg->header.stamp);
        }
    }

    void PublishOdometry(const Sophus::SE3f& Tcw, const builtin_interfaces::msg::Time& stamp) {
        nav_msgs::msg::Odometry odom;
        odom.header.stamp = stamp;
        odom.header.frame_id = "odom";
        odom.child_frame_id = "camera_link";

        Eigen::Quaternionf q = Tcw.unit_quaternion();
        Eigen::Vector3f t = Tcw.translation();
        
        odom.pose.pose.position.x = t.x();
        odom.pose.pose.position.y = t.y();
        odom.pose.pose.position.z = t.z();
        odom.pose.pose.orientation.w = q.w();
        odom.pose.pose.orientation.x = q.x();
        odom.pose.pose.orientation.y = q.y();
        odom.pose.pose.orientation.z = q.z();

        odom_pub_->publish(odom);
    }

    rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr img_sub_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    
    // In a real launch, these paths would be passed as ROS 2 parameters
    std::string vocab_path = "config/ORBvoc.txt";
    std::string settings_path = "config/drone_sensor.yaml";

    // Initialize the core ORB-SLAM3 System (Monocular-Inertial mode)
    // The 'true' flag enables the ORB-SLAM3 viewer GUI
    ORB_SLAM3::System SLAM(vocab_path, settings_path, ORB_SLAM3::System::IMU_MONOCULAR, true);

    auto node = std::make_shared<MonoInertialNode>(&SLAM);
    rclcpp::spin(node);
    
    // Clean shutdown
    SLAM.Shutdown();
    rclcpp::shutdown();
    return 0;
}
