import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction, ExecuteProcess
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


_UGV_CONFIGS = [
    {'name': 'ugv_1', 'x': '-10.0', 'y':   '0.0', 'z': '0.0'},
    {'name': 'ugv_2', 'x':  '10.0', 'y':   '0.0', 'z': '0.0'},
    {'name': 'ugv_3', 'x':   '0.0', 'y':  '-7.0', 'z': '0.0'},
]


def _make_ugv_sdf(template_path, robot_name):
    with open(template_path) as f:
        content = f.read().replace('ugv_1', robot_name)
    out_path = f'/tmp/{robot_name}.sdf'
    with open(out_path, 'w') as f:
        f.write(content)
    return out_path


def generate_launch_description():
    use_rviz = LaunchConfiguration('use_rviz')
    world_file = LaunchConfiguration('world_file')
    gz_args = LaunchConfiguration('gz_args')

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

    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')
    gz_launch = os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')

    bringup_share = get_package_share_directory('multi_robot_bringup')
    default_world_path = os.path.join(bringup_share, 'worlds', 'urban_obstacles.sdf')

    uav_share = get_package_share_directory('uav_description')
    uav_launch = os.path.join(uav_share, 'launch', 'uav.launch.py')

    ugv_share = get_package_share_directory('ugv_description')
    ugv_launch = os.path.join(ugv_share, 'launch', 'ugv.launch.py')
    ugv_sdf_template = os.path.join(ugv_share, 'models', 'ugv_diffdrive.sdf')

    comm_share = get_package_share_directory('comm_layer')
    network_launch = os.path.join(comm_share, 'launch', 'network_simulation.launch.py')

    start_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch),
        launch_arguments={'gz_args': gz_args}.items(),
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        output='screen',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
    )

    start_uav = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(uav_launch),
        launch_arguments={
            'namespace': 'uav_1',
            'use_rviz': use_rviz,
            'use_sim_time': 'true',
        }.items(),
    )

    # Build per-UGV state publishers, spawns, and bridges
    ugv_state_publishers = []
    spawn_actions = []
    bridge_actions = []

    for cfg in _UGV_CONFIGS:
        robot_name = cfg['name']
        sdf_path = _make_ugv_sdf(ugv_sdf_template, robot_name)

        ugv_state_publishers.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(ugv_launch),
                launch_arguments={
                    'namespace': robot_name,
                    'use_rviz': 'false',
                    'use_sim_time': 'true',
                }.items(),
            )
        )

        spawn_actions.append(
            ExecuteProcess(
                cmd=[
                    'ros2', 'run', 'ros_gz_sim', 'create',
                    '-name', robot_name,
                    '-file', sdf_path,
                    '-x', cfg['x'],
                    '-y', cfg['y'],
                    '-z', cfg['z'],
                ],
                output='screen',
            )
        )

        bridge_actions.append(
            Node(
                package='ros_gz_bridge',
                executable='parameter_bridge',
                name=f'{robot_name}_cmd_vel_bridge',
                output='screen',
                arguments=[
                    f'/model/{robot_name}/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist'
                ],
                remappings=[(f'/model/{robot_name}/cmd_vel', f'/{robot_name}/cmd_vel')],
            )
        )

        bridge_actions.append(
            Node(
                package='ros_gz_bridge',
                executable='parameter_bridge',
                name=f'{robot_name}_odom_bridge',
                output='screen',
                arguments=[
                    f'/model/{robot_name}/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry'
                ],
                remappings=[(f'/model/{robot_name}/odometry', f'/{robot_name}/odom')],
            )
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
        *ugv_state_publishers,

        TimerAction(period=2.5, actions=spawn_actions),
        TimerAction(period=3.0, actions=bridge_actions),

        # Mission communication stack (opt-in; off by default).
        TimerAction(period=3.5, actions=[mission_publisher]),
        TimerAction(period=3.5, actions=[mission_receiver]),
        TimerAction(period=3.5, actions=[network_sim]),
    ])
