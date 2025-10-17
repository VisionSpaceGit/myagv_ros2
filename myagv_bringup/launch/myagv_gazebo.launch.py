from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    bringup_share = get_package_share_directory('myagv_bringup')
    description_share = get_package_share_directory('myagv_description')
    gazebo_share = get_package_share_directory('gazebo_ros')

    world = LaunchConfiguration('world')
    entity_name = LaunchConfiguration('entity_name')
    ros2_control_config = LaunchConfiguration('ros2_control_config')
    use_sim_time = LaunchConfiguration('use_sim_time')

    xacro_file = PathJoinSubstitution(
        [description_share, 'urdf', 'myagv_gazebo.urdf.xacro']
    )

    robot_description = ParameterValue(
        Command([
            'xacro ', xacro_file,
            ' ros2_control_config:=', ros2_control_config
        ]),
        value_type=str
    )

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([gazebo_share, 'launch', 'gazebo.launch.py'])
        ),
        launch_arguments={'world': world}.items()
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_description
        }],
        output='screen'
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', entity_name,
            '-topic', 'robot_description'
        ],
        output='screen'
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '600',
        ],
        output='screen'
    )

    wheel_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'wheel_velocity_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '600',
        ],
        output='screen'
    )

    after_spawn_jsb = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            on_exit=[joint_state_broadcaster_spawner]
        )
    )

    after_jsb_wheels = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[wheel_controller_spawner]
        )
    )

    default_world = PathJoinSubstitution(
        [gazebo_share, 'worlds', 'empty.world']
    )
    default_ros2_control_config = PathJoinSubstitution(
        [bringup_share, 'config', 'myagv_ros2_control.yaml']
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=default_world,
            description='Gazebo world file'
        ),
        DeclareLaunchArgument(
            'entity_name',
            default_value='myagv',
            description='Name of the spawned entity in Gazebo'
        ),
        DeclareLaunchArgument(
            'ros2_control_config',
            default_value=default_ros2_control_config,
            description='Path to ros2_control controller configuration'
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock if true'
        ),
        gazebo_launch,
        robot_state_publisher,
        spawn_entity,
        after_spawn_jsb,
        after_jsb_wheels
    ])
