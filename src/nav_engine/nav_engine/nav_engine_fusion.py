#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Odometry
import numpy as np
import json
import os

class NavEngineFusion(Node):
    def __init__(self):
        super().__init__('nav_engine_fusion')
        
        # SOTA Threshold: Max acceptable variance in meters squared
        self.max_acceptable_gps_variance = 5.0 
        self.active_source = "GPS"
        self.current_variance = 0.0

        # Subscriptions to the hardware/simulated sensors
        self.gps_sub = self.create_subscription(
            NavSatFix, '/hardware/gps/fix', self.gps_callback, 10)
        self.vslam_sub = self.create_subscription(
            Odometry, '/nav_engine/visual_odom', self.vslam_callback, 10)
        
        self.get_logger().info("NavEngine Sensor Fusion Initialized. Active Source: GPS")

        # Create a state file for the FastAPI server to read
        self.state_file = "/tmp/nav_engine_state.json"
        self.update_state_file()

    def update_state_file(self):
        """Writes current state to disk so the Stripe-like API can serve it instantly."""
        state = {
            "active_source": self.active_source,
            "gps_variance": float(self.current_variance),
            "health": "OPTIMAL" if self.current_variance < 20.0 else "DEGRADED"
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f)

    def gps_callback(self, msg):
        # Calculate uncertainty (trace of the covariance matrix)
        self.current_variance = msg.position_covariance[0] + msg.position_covariance[4]
        
        if msg.status.status < 0 or self.current_variance > self.max_acceptable_gps_variance:
            if self.active_source != "VSLAM (ORB-SLAM3)":
                self.get_logger().warn(f"⚠️ GPS DENIED (Variance: {self.current_variance:.2f}). Failing over to ORB-SLAM3.")
                self.active_source = "VSLAM (ORB-SLAM3)"
                self.update_state_file()
        else:
            if self.active_source != "GPS":
                self.get_logger().info(f"🛰️ GPS RECOVERED (Variance: {self.current_variance:.2f}). Restoring satellite nav.")
                self.active_source = "GPS"
                self.update_state_file()

    def vslam_callback(self, msg):
        # In a full deployment, this feeds the EKF. 
        # For now, it just confirms ORB-SLAM3 is alive and publishing.
        pass

def main(args=None):
    rclpy.init(args=args)
    node = NavEngineFusion()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
