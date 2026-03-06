import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    nav_engine_dir = get_package_share_directory("nav_engine")
    orbslam3_bridge_dir = get_package_share_directory("orbslam3_bridge")

    default_world = os.path.join(nav_engine_dir, "worlds", "warehouse_gps_denied.sdf")
    default_vocab = os.path.join(orbslam3_bridge_dir, "config", "ORBvoc.txt")
    default_settings = os.path.join(orbslam3_bridge_dir, "config", "drone_sensor.yaml")

    world_arg = DeclareLaunchArgument("world", default_value=default_world)
    vocab_arg = DeclareLaunchArgument("vocab_file", default_value=default_vocab)
    settings_arg = DeclareLaunchArgument("settings_file", default_value=default_settings)
    api_port_arg = DeclareLaunchArgument("api_port", default_value="8000")
    state_file_arg = DeclareLaunchArgument(
        "state_file", default_value="/tmp/nav_engine_state.json"
    )
    gps_variance_threshold_arg = DeclareLaunchArgument(
        "gps_variance_threshold", default_value="5.0"
    )

    world = LaunchConfiguration("world")
    vocab_file = LaunchConfiguration("vocab_file")
    settings_file = LaunchConfiguration("settings_file")
    api_port = LaunchConfiguration("api_port")
    state_file = LaunchConfiguration("state_file")
    gps_variance_threshold = LaunchConfiguration("gps_variance_threshold")

    return LaunchDescription(
        [
            world_arg,
            vocab_arg,
            settings_arg,
            api_port_arg,
            state_file_arg,
            gps_variance_threshold_arg,

            ExecuteProcess(
                cmd=["gz", "sim", "-r", world],
                output="screen",
            ),

            Node(
                package="ros_gz_bridge",
                executable="parameter_bridge",
                arguments=[
                    "/drone/camera/image_raw@sensor_msgs/msg/Image@gz.msgs.Image",
                    "/drone/imu@sensor_msgs/msg/Imu@gz.msgs.IMU",
                    "/drone/gps/clean@sensor_msgs/msg/NavSatFix@gz.msgs.NavSat",
                    "/model/nav_drone/odometry@nav_msgs/msg/Odometry@gz.msgs.Odometry",
                ],
                output="screen",
            ),

            Node(
                package="orbslam3_bridge",
                executable="mono_inertial_node",
                name="orbslam3_bridge_node",
                parameters=[
                    {
                        "vocab_file": vocab_file,
                        "settings_file": settings_file,
                        "enable_viewer": False,
                    }
                ],
                output="screen",
            ),

            Node(
                package="nav_engine",
                executable="gps_jammer.py",
                name="gps_jammer_node",
                output="screen",
            ),

            Node(
                package="nav_engine",
                executable="nav_engine_fusion.py",
                name="nav_engine_fusion_node",
                parameters=[
                    {
                        "state_file": state_file,
                        "gps_variance_threshold": gps_variance_threshold,
                    }
                ],
                output="screen",
            ),

            ExecuteProcess(
                cmd=[
                    "python3",
                    "-m",
                    "nav_engine.navigation_api",
                    "--state-file",
                    state_file,
                    "--port",
                    api_port,
                ],
                output="screen",
            ),
        ]
    )
