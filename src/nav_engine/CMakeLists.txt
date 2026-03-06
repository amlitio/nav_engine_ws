cmake_minimum_required(VERSION 3.8)
project(nav_engine)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Install the Python package directory
ament_python_install_package(${PROJECT_NAME})

# Install the executable Python scripts
install(PROGRAMS
  ${PROJECT_NAME}/nav_engine_fusion.py
  ${PROJECT_NAME}/navigation_api.py
  ${PROJECT_NAME}/gps_jammer.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files and Gazebo worlds
install(DIRECTORY launch worlds
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
