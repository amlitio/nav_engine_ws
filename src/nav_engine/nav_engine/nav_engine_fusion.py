#!/usr/bin/env python3
import json
import os
from typing import Optional

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus


class NavEngineFusion(Node):
    def __init__(self) -> None:
        super().__init__("nav_engine_fusion")

        self.declare_parameter("gps_variance_threshold", 5.0)
        self.declare_parameter("state_file", "/tmp/nav_engine_state.json")

        self.gps_variance_threshold = float(
            self.get_parameter("gps_variance_threshold").value
        )
        self.state_file = str(self.get_parameter("state_file").value)

        self.active_source = "GPS"
        self.current_variance = 0.0
        self.last_gps_ok = False
        self.last_vslam_stamp: Optional[str] = None
        self.last_vslam_pose = {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "qx": 0.0,
            "qy": 0.0,
            "qz": 0.0,
            "qw": 1.0,
        }

        self.gps_sub = self.create_subscription(
            NavSatFix,
            "/hardware/gps/fix",
            self.gps_callback,
            10,
        )
        self.vslam_sub = self.create_subscription(
            Odometry,
            "/nav_engine/visual_odom",
            self.vslam_callback,
            10,
        )

        self.get_logger().info(
            f"NavEngine fusion started. "
            f"threshold={self.gps_variance_threshold:.2f}, "
            f"state_file={self.state_file}"
        )
        self.update_state_file()

    def _health(self) -> str:
        if not self.last_gps_ok and self.last_vslam_stamp is None:
            return "DEGRADED"
        if self.current_variance > (self.gps_variance_threshold * 2.0):
            return "DEGRADED"
        return "OPTIMAL"

    def update_state_file(self) -> None:
        state_dir = os.path.dirname(self.state_file)
        if state_dir:
            os.makedirs(state_dir, exist_ok=True)

        state = {
            "active_source": self.active_source,
            "gps_variance": float(self.current_variance),
            "gps_ok": bool(self.last_gps_ok),
            "health": self._health(),
            "last_vslam_stamp": self.last_vslam_stamp,
            "last_vslam_pose": self.last_vslam_pose,
        }

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f)

    def gps_callback(self, msg: NavSatFix) -> None:
        self.current_variance = float(
            msg.position_covariance[0] + msg.position_covariance[4]
        )

        gps_fix_ok = (
            msg.status.status >= NavSatStatus.STATUS_FIX
            and self.current_variance <= self.gps_variance_threshold
        )

        self.last_gps_ok = gps_fix_ok

        if gps_fix_ok:
            if self.active_source != "GPS":
                self.get_logger().info(
                    f"GPS recovered (variance={self.current_variance:.2f}). "
                    "Switching back to GPS."
                )
            self.active_source = "GPS"
        else:
            if self.active_source != "VSLAM (ORB-SLAM3)":
                self.get_logger().warn(
                    f"GPS denied/degraded (variance={self.current_variance:.2f}, "
                    f"status={msg.status.status}). Switching to VSLAM."
                )
            self.active_source = "VSLAM (ORB-SLAM3)"

        self.update_state_file()

    def vslam_callback(self, msg: Odometry) -> None:
        self.last_vslam_stamp = f"{msg.header.stamp.sec}.{msg.header.stamp.nanosec:09d}"
        self.last_vslam_pose = {
            "x": float(msg.pose.pose.position.x),
            "y": float(msg.pose.pose.position.y),
            "z": float(msg.pose.pose.position.z),
            "qx": float(msg.pose.pose.orientation.x),
            "qy": float(msg.pose.pose.orientation.y),
            "qz": float(msg.pose.pose.orientation.z),
            "qw": float(msg.pose.pose.orientation.w),
        }
        self.update_state_file()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = NavEngineFusion()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
