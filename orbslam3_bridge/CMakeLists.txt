cmake_minimum_required(VERSION 3.8)
project(orbslam3_bridge)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic -O3)
endif()

# Find ROS 2 packages
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(image_transport REQUIRED)

# Find System Dependencies for ORB-SLAM3
find_package(OpenCV REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(Pangolin REQUIRED) # Required if Viewer is enabled

# --- IMPORTANT: Set the path to your ORB-SLAM3 installation ---
# In our Dockerfile, we assume ORB-SLAM3 is built in /opt/ORB_SLAM3 or similar.
# Update this path if your ORB_SLAM3 directory is located elsewhere.
set(ORB_SLAM3_DIR "/usr/local/include/ORB_SLAM3" CACHE PATH "Path to ORB-SLAM3 source")
set(ORB_SLAM3_LIB_DIR "/usr/local/lib" CACHE PATH "Path to ORB-SLAM3 lib")

include_directories(
  include
  ${ORB_SLAM3_DIR}/include
  ${ORB_SLAM3_DIR}/include/CameraModels
  ${ORB_SLAM3_DIR}/Thirdparty/Sophus
  ${EIGEN3_INCLUDE_DIR}
)

# Create the Executable
add_executable(mono_inertial_node src/mono_inertial_node.cpp)

# Link ROS 2 dependencies
ament_target_dependencies(mono_inertial_node
  rclcpp
  sensor_msgs
  nav_msgs
  cv_bridge
  image_transport
)

# Link ORB-SLAM3 and OpenCV
target_link_libraries(mono_inertial_node
  ${OpenCV_LIBS}
  ${ORB_SLAM3_LIB_DIR}/libORB_SLAM3.so
  ${Pangolin_LIBRARIES}
)

# Install rules so 'ros2 run' and 'ros2 launch' can find the executable and configs
install(TARGETS
  mono_inertial_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)

ament_package()
