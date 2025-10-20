cmake_minimum_required(VERSION 3.8)
project(myagv_bringup)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch config world
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/cmd_vel_relay.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
