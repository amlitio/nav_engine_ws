import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. Start Gazebo with the Warehouse World
        ExecuteProcess(
            cmd=['gz', 'sim', '-r', 'src/nav_engine/worlds/warehouse_gps_denied.sdf'],
            output='screen'
        ),

        # 2. Bridge Gazebo Topics to ROS 2
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/drone/camera/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
                '/drone/imu@sensor_msgs/msg/Imu@gz.msgs.IMU',
                '/drone/gps/clean@sensor_msgs/msg/NavSatFix@gz.msgs.NavSat',
                '/model/nav_drone/odometry@nav_msgs/msg/Odometry@gz.msgs.Odometry'
            ],
            output='screen'
        ),

        # 3. Start the Environment Degrader
        Node(
            package='nav_engine',
            executable='gps_jammer',
            name='gps_jammer',
            output='screen'
        ),

        # 4. Start the NavEngine Failover "Brain"
        Node(
            package='nav_engine',
            executable='nav_engine_fusion',
            name='nav_engine_fusion',
            output='screen'
        )
    ])
