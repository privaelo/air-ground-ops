from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction, ExecuteProcess
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    use_rviz = LaunchConfiguration('use_rviz')

    world_file = LaunchConfiguration('world_file')
    gz_args = LaunchConfiguration('gz_args')

    ugv_spawn_x = LaunchConfiguration('ugv_spawn_x')
    ugv_spawn_y = LaunchConfiguration('ugv_spawn_y')
    ugv_spawn_z = LaunchConfiguration('ugv_spawn_z')

    use_mission_comms = LaunchConfiguration('use_mission_comms')
    use_network_sim = LaunchConfiguration('use_network_sim')

    mission_topic_raw = LaunchConfiguration('mission_topic_raw')
    mission_topic_sim = LaunchConfiguration('mission_topic_sim')

    mission_publish_rate_hz = LaunchConfiguration('mission_publish_rate_hz')
    mission_target_x = LaunchConfiguration('mission_target_x')
    mission_target_y = LaunchConfiguration('mission_target_y')
    mission_priority = LaunchConfiguration('mission_priority')
    mission_id_prefix = LaunchConfiguration('mission_id_prefix')

    network_scenario = LaunchConfiguration('network_scenario')
    network_enabled = LaunchConfiguration('network_enabled')
    network_random_seed = LaunchConfiguration('network_random_seed')
    network_drop_probability = LaunchConfiguration('network_drop_probability')
    network_delay_ms = LaunchConfiguration('network_delay_ms')
    network_blackout_start_sec = LaunchConfiguration('network_blackout_start_sec')
    network_blackout_duration_sec = LaunchConfiguration('network_blackout_duration_sec')

    # Gazebo launcher
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')
    gz_launch = os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')

    bringup_share = get_package_share_directory('multi_robot_bringup')
    default_world_path = os.path.join(bringup_share, 'worlds', 'urban_obstacles.sdf')

    # UAV / UGV launchers (robot_state_publisher + optional RViz)
    uav_share = get_package_share_directory('uav_description')
    uav_launch = os.path.join(uav_share, 'launch', 'uav.launch.py')

    ugv_share = get_package_share_directory('ugv_description')
    ugv_launch = os.path.join(ugv_share, 'launch', 'ugv.launch.py')
    ugv_sdf = os.path.join(ugv_share, 'models', 'ugv_diffdrive.sdf')

    comm_share = get_package_share_directory('comm_layer')
    network_launch = os.path.join(comm_share, 'launch', 'network_simulation.launch.py')

    start_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch),
        launch_arguments={
            'gz_args': gz_args,
        }.items(),
    )

    # Bridge /clock
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        output='screen',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
    )

    # UAV state publisher (namespaced); RViz optional (bringup arg)
    start_uav = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(uav_launch),
        launch_arguments={
            'namespace': 'uav_1',
            'use_rviz': use_rviz,
            'use_sim_time': 'true',
        }.items(),
    )

    # UGV state publisher (namespaced); do not launch a second RViz instance
    start_ugv = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(ugv_launch),
        launch_arguments={
            'namespace': 'ugv_1',
            'use_rviz': 'false',
            'use_sim_time': 'true',
        }.items(),
    )

    # Spawn UGV from SDF (diff drive system)
    spawn_ugv = ExecuteProcess(
        cmd=[
            'ros2', 'run', 'ros_gz_sim', 'create',
            '-name', 'ugv_1',
            '-file', ugv_sdf,
            '-x', ugv_spawn_x,
            '-y', ugv_spawn_y,
            '-z', ugv_spawn_z,
        ],
        output='screen',
    )

    # Bridge cmd_vel ROS->GZ (ROS: /ugv_1/cmd_vel  <->  GZ: /model/ugv_1/cmd_vel)
    cmd_vel_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ugv_cmd_vel_bridge',
        output='screen',
        arguments=['/model/ugv_1/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist'],
        remappings=[('/model/ugv_1/cmd_vel', '/ugv_1/cmd_vel')],
    )

    # Bridge odometry GZ->ROS (GZ: /model/ugv_1/odometry -> ROS: /ugv_1/odom)
    odom_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ugv_odom_bridge',
        output='screen',
        arguments=['/model/ugv_1/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry'],
        remappings=[('/model/ugv_1/odometry', '/ugv_1/odom')],
    )

    mission_publisher = Node(
        package='comm_layer',
        executable='uav_mission_publisher_node',
        name='uav_mission_publisher_node',
        output='screen',
        parameters=[{
            'output_topic': mission_topic_raw,
            'publish_rate_hz': mission_publish_rate_hz,
            'target_x': mission_target_x,
            'target_y': mission_target_y,
            'priority': mission_priority,
            'mission_id_prefix': mission_id_prefix,
        }],
        condition=IfCondition(use_mission_comms),
    )

    mission_receiver = Node(
        package='comm_layer',
        executable='ugv_mission_receiver_node',
        name='ugv_mission_receiver_node',
        output='screen',
        parameters=[{
            'input_topic': mission_topic_sim,
            'stats_log_period_sec': 2.0,
        }],
        condition=IfCondition(use_mission_comms),
    )

    network_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(network_launch),
        launch_arguments={
            'input_topic': mission_topic_raw,
            'output_topic': mission_topic_sim,
            'scenario': network_scenario,
            'enabled': network_enabled,
            'random_seed': network_random_seed,
            'drop_probability': network_drop_probability,
            'delay_ms': network_delay_ms,
            'blackout_start_sec': network_blackout_start_sec,
            'blackout_duration_sec': network_blackout_duration_sec,
            'enable_stats_log': 'true',
            'stats_log_period_sec': '2.0',
        }.items(),
        condition=IfCondition(use_network_sim),
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_rviz', default_value='false'),

        DeclareLaunchArgument('world_file', default_value=default_world_path),
        DeclareLaunchArgument('gz_args', default_value=['-r ', world_file]),

        DeclareLaunchArgument('ugv_spawn_x', default_value='-2.0'),
        DeclareLaunchArgument('ugv_spawn_y', default_value='0.0'),
        DeclareLaunchArgument('ugv_spawn_z', default_value='0.0'),

        DeclareLaunchArgument('use_mission_comms', default_value='false'),
        DeclareLaunchArgument('use_network_sim', default_value='false'),

        DeclareLaunchArgument('mission_topic_raw', default_value='/uav_1/mission_raw'),
        DeclareLaunchArgument('mission_topic_sim', default_value='/uav_1/mission_sim'),

        DeclareLaunchArgument('mission_publish_rate_hz', default_value='1.0'),
        DeclareLaunchArgument('mission_target_x', default_value='8.0'),
        DeclareLaunchArgument('mission_target_y', default_value='0.0'),
        DeclareLaunchArgument('mission_priority', default_value='1'),
        DeclareLaunchArgument('mission_id_prefix', default_value='mission'),

        DeclareLaunchArgument('network_scenario', default_value='clean'),
        DeclareLaunchArgument('network_enabled', default_value='true'),
        DeclareLaunchArgument('network_random_seed', default_value='42'),
        DeclareLaunchArgument('network_drop_probability', default_value='-1.0'),
        DeclareLaunchArgument('network_delay_ms', default_value='-1.0'),
        DeclareLaunchArgument('network_blackout_start_sec', default_value='-1.0'),
        DeclareLaunchArgument('network_blackout_duration_sec', default_value='-1.0'),

        start_gazebo,
        clock_bridge,

        start_uav,
        start_ugv,

        TimerAction(period=2.5, actions=[spawn_ugv]),

        # Bridges can start before/after spawn; kept after for deterministic startup logs.
        TimerAction(period=3.0, actions=[cmd_vel_bridge]),
        TimerAction(period=3.0, actions=[odom_bridge]),

        # Mission communication stack (opt-in; off by default).
        TimerAction(period=3.5, actions=[mission_publisher]),
        TimerAction(period=3.5, actions=[mission_receiver]),
        TimerAction(period=3.5, actions=[network_sim]),
    ])
