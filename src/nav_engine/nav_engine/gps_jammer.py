#!/usr/bin/env python3
import copy

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus


class GpsJammerNode(Node):
    def __init__(self) -> None:
        super().__init__("gps_jammer")

        self.current_y_position = -5.0

        self.gps_sub = self.create_subscription(
            NavSatFix,
            "/drone/gps/clean",
            self.gps_callback,
            10,
        )
        self.odom_sub = self.create_subscription(
            Odometry,
            "/model/nav_drone/odometry",
            self.odom_callback,
            10,
        )
        self.gps_pub = self.create_publisher(
            NavSatFix,
            "/hardware/gps/fix",
            10,
        )

        self.get_logger().info("GPS jammer/degrader node started.")

    def odom_callback(self, msg: Odometry) -> None:
        self.current_y_position = msg.pose.pose.position.y

    def gps_callback(self, msg: NavSatFix) -> None:
        degraded_msg = copy.deepcopy(msg)

        # Demo rule:
        # entering y > 0.0 means the robot has moved into a GPS-denied zone.
        if self.current_y_position > 0.0:
            degraded_msg.status.status = NavSatStatus.STATUS_NO_FIX
            degraded_msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
            degraded_msg.position_covariance[0] = 15.0
            degraded_msg.position_covariance[4] = 15.0
            degraded_msg.position_covariance[8] = 25.0
        else:
            degraded_msg.status.status = NavSatStatus.STATUS_FIX
            degraded_msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
            degraded_msg.position_covariance[0] = 0.1
            degraded_msg.position_covariance[4] = 0.1
            degraded_msg.position_covariance[8] = 0.2

        self.gps_pub.publish(degraded_msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = GpsJammerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
