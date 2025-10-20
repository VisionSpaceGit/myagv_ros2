from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    gazebo_share = get_package_share_directory('gazebo_ros')
    bringup_share = get_package_share_directory('myagv_bringup')
    description_share = get_package_share_directory('myagv_description')
    ekf_share = get_package_share_directory('myagv_odometry')
    slam_share = get_package_share_directory('slam_gmapping')
    nav2_bringup_share = get_package_share_directory('nav2_bringup')

    world = LaunchConfiguration('world')
    entity_name = LaunchConfiguration('entity_name')
    ros2_control_config = LaunchConfiguration('ros2_control_config')
    use_sim_time = LaunchConfiguration('use_sim_time')
    slam = LaunchConfiguration('slam', default='true')
    slam_rviz = LaunchConfiguration('slam_rviz', default='false')

    gazebo_world = PathJoinSubstitution(
        # [gazebo_share, 'worlds', 'empty.world']
        [bringup_share, 'world', 'indoor_room.world']
    )
    
    default_ros2_control_config = PathJoinSubstitution(
        [bringup_share, 'config', 'myagv_ros2_control.yaml']
    )

    xacro_file = PathJoinSubstitution(
        [description_share, 'urdf', 'myagv_gazebo.urdf.xacro']
        # [description_share, 'urdf', 'myagv_gazebo_skid.urdf.xacro']
    )
    
    efk_file = PathJoinSubstitution(
        [ekf_share, 'config', 'ekf.yaml']
    )
    rviz_config = PathJoinSubstitution(
        [slam_share, 'rviz', 'gmapping.rviz']
    )
    nav2_params = PathJoinSubstitution(
        [bringup_share, 'config', 'nav2_params.yaml']
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

    diff_drive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'diff_drive_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '600',
        ],
        output='screen'
    )
    
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_node',
        output='screen',
        parameters=[
            efk_file,
            {'use_sim_time': use_sim_time},
        ],
    )

    slam_gmapping_node = Node(
        package='slam_gmapping',
        executable='slam_gmapping',
        name='slam_gmapping',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([nav2_bringup_share, 'launch', 'navigation_launch.py'])
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file': nav2_params,
            'autostart': 'true'
        }.items()
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
            on_exit=[diff_drive_controller_spawner]
        )
    )
    
    after_spawn_ekf = RegisterEventHandler(
        OnProcessExit(
            target_action=diff_drive_controller_spawner,
            on_exit=[ekf_node]
        )
    )
    
    after_slam_gzb = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            on_exit=[slam_gmapping_node]
        )
    )
    
    after_rivz_slam = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            on_exit=[rviz_node]
        )
    )
    
    # Temporary use for Gazebo odometry test
    tf2_static_w2m = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf2_world_to_map',
        arguments=['0', '0', '0', '0', '0', '0', 'world', 'map'],
        output='screen'
    )
    
    # tf2_static_m2o = Node(
    #     package='tf2_ros',
    #     executable='static_transform_publisher',
    #     name='static_tf2_map_to_odom',
    #     arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
    #     output='screen'
    # )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=gazebo_world,
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
        tf2_static_w2m,
        # tf2_static_m2o,
        robot_state_publisher,
        spawn_entity,
        after_spawn_jsb,
        after_jsb_wheels,
        after_spawn_ekf,
        after_slam_gzb,
        after_rivz_slam,
    ])
