import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Odometry

class GpsJammerNode(Node):
    def __init__(self):
        super().__init__('gps_jammer')
        
        # Subscribe to perfect simulation GPS and ground truth Odometry
        self.gps_sub = self.create_subscription(NavSatFix, '/drone/gps/clean', self.gps_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, '/model/nav_drone/odometry', self.odom_callback, 10)
        
        # Publish the "Real World" noisy GPS to NavEngine
        self.gps_pub = self.create_publisher(NavSatFix, '/hardware/gps/fix', 10)
        
        self.current_y_position = -5.0 # Starts outside

    def odom_callback(self, msg):
        # Track the drone's position in the simulated world
        self.current_y_position = msg.pose.pose.position.y

    def gps_callback(self, msg):
        degraded_msg = msg
        
        # The Threshold: Y > 0 means the drone is inside the warehouse
        if self.current_y_position > 0.0:
            # Indoors: Spike the covariance to simulate signal bounce/loss
            degraded_msg.position_covariance[0] = 15.0 # High variance in X
            degraded_msg.position_covariance[4] = 15.0 # High variance in Y
            degraded_msg.status.status = -1 # NO_FIX
        else:
            # Outdoors: Perfect RTK-level fix
            degraded_msg.position_covariance[0] = 0.1
            degraded_msg.position_covariance[4] = 0.1
            degraded_msg.status.status = 1 # FIX

        self.gps_pub.publish(degraded_msg)

def main(args=None):
    rclpy.init(args=args)
    node = GpsJammerNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
