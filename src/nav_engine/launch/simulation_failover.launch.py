import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch_ros.actions import Node

def generate_launch_description():
    # Get the path to the nav_engine package to find the world file
    nav_engine_dir = get_package_share_directory('nav_engine')
    orbslam3_bridge_dir = get_package_share_directory('orbslam3_bridge')
    
    world_file = os.path.join(nav_engine_dir, 'worlds', 'warehouse_gps_denied.sdf')
    
    return LaunchDescription([
        # 1. Start Gazebo Sim (Modern Ignition/Gazebo) with the warehouse world
        ExecuteProcess(
            cmd=['gz', 'sim', '-r', world_file],
            output='screen'
        ),

        # 2. Bridge Gazebo topics to ROS 2 topics
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

        # 3. Start the Real ORB-SLAM3 C++ Bridge
        Node(
            package='orbslam3_bridge',
            executable='mono_inertial_node',
            name='orbslam3_bridge_node',
            # Set the working directory so it finds the config files easily
            parameters=[{
                'vocab_file': os.path.join(orbslam3_bridge_dir, 'config', 'ORBvoc.txt'),
                'settings_file': os.path.join(orbslam3_bridge_dir, 'config', 'drone_sensor.yaml')
            }],
            output='screen'
        ),

        # 4. Start the Environment Degrader (The simulated GPS Jammer)
        Node(
            package='nav_engine',
            executable='gps_jammer',
            name='gps_jammer_node',
            output='screen'
        ),

        # 5. Start the NavEngine Failover "Brain"
        Node(
            package='nav_engine',
            executable='nav_engine_fusion',
            name='nav_engine_fusion_node',
            output='screen'
        )
    ])
