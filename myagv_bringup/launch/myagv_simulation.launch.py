from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node


def generate_launch_description():
    bringup_share = get_package_share_directory('myagv_bringup')

    use_sim_time = LaunchConfiguration('use_sim_time')
    world = LaunchConfiguration('world')
    entity_name = LaunchConfiguration('entity_name')
    ros2_control_config = LaunchConfiguration('ros2_control_config')
    params_file = LaunchConfiguration('params_file')
    rviz_config = LaunchConfiguration('rviz_config')

    default_world = PathJoinSubstitution(
        [bringup_share, 'world', 'indoor_room.world']
    )
    default_ros2_control_config = PathJoinSubstitution(
        [bringup_share, 'config', 'myagv_ros2_control.yaml']
    )
    default_nav2_params = PathJoinSubstitution(
        [bringup_share, 'config', 'nav2_params.yaml']
    )
    default_rviz_config = PathJoinSubstitution(
        [bringup_share, 'config', 'myagv_rviz.rviz']
    )

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_share, 'launch', 'myagv_gazebo.launch.py'])
        ),
        launch_arguments={
            'world': world,
            'entity_name': entity_name,
            'ros2_control_config': ros2_control_config,
            'use_sim_time': use_sim_time,
            'use_rviz': 'false',
        }.items(),
    )

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_share, 'launch', 'myagv_slam.launch.py'])
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
        }.items(),
    )

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_share, 'launch', 'myagv_nav2.launch.py'])
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file': params_file,
        }.items(),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock',
        ),
        DeclareLaunchArgument(
            'world',
            default_value=default_world,
            description='Gazebo world file',
        ),
        DeclareLaunchArgument(
            'entity_name',
            default_value='myagv',
            description='Gazebo entity name',
        ),
        DeclareLaunchArgument(
            'ros2_control_config',
            default_value=default_ros2_control_config,
            description='ros2_control configuration file',
        ),
        DeclareLaunchArgument(
            'params_file',
            default_value=default_nav2_params,
            description='Nav2 parameters file',
        ),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=default_rviz_config,
            description='RViz configuration file',
        ),
        gazebo_launch,
        slam_launch,
        nav2_launch,
        rviz_node,
    ])
