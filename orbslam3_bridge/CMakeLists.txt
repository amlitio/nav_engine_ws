cmake_minimum_required(VERSION 3.8)
project(orbslam3_bridge)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic -O3)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(image_transport REQUIRED)
find_package(OpenCV REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(Pangolin REQUIRED)

set(ORB_SLAM3_DIR "/usr/local/include/ORB_SLAM3" CACHE PATH "Path to ORB-SLAM3 source tree")
set(ORB_SLAM3_LIB_DIR "/usr/local/lib" CACHE PATH "Path to ORB-SLAM3 libraries")

if(NOT EXISTS "${ORB_SLAM3_DIR}/include/System.h")
  message(FATAL_ERROR "ORB_SLAM3_DIR is invalid: ${ORB_SLAM3_DIR}")
endif()

if(NOT EXISTS "${ORB_SLAM3_LIB_DIR}/libORB_SLAM3.so")
  message(FATAL_ERROR "ORB_SLAM3 library not found in: ${ORB_SLAM3_LIB_DIR}")
endif()

add_executable(mono_inertial_node src/mono_inertial_node.cpp)

target_include_directories(mono_inertial_node PRIVATE
  include
  ${ORB_SLAM3_DIR}/include
  ${ORB_SLAM3_DIR}/include/CameraModels
  ${ORB_SLAM3_DIR}/Thirdparty/Sophus
  ${EIGEN3_INCLUDE_DIR}
)

ament_target_dependencies(mono_inertial_node
  rclcpp
  sensor_msgs
  nav_msgs
  cv_bridge
  image_transport
)

target_link_libraries(mono_inertial_node
  ${OpenCV_LIBS}
  ${ORB_SLAM3_LIB_DIR}/libORB_SLAM3.so
  ${Pangolin_LIBRARIES}
)

install(TARGETS mono_inertial_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)

ament_package()
