from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    input_topic = LaunchConfiguration('input_topic')
    output_topic = LaunchConfiguration('output_topic')
    scenario = LaunchConfiguration('scenario')
    enabled = LaunchConfiguration('enabled')
    random_seed = LaunchConfiguration('random_seed')

    drop_probability = LaunchConfiguration('drop_probability')
    delay_ms = LaunchConfiguration('delay_ms')
    blackout_start_sec = LaunchConfiguration('blackout_start_sec')
    blackout_duration_sec = LaunchConfiguration('blackout_duration_sec')

    enable_stats_log = LaunchConfiguration('enable_stats_log')
    stats_log_period_sec = LaunchConfiguration('stats_log_period_sec')

    return LaunchDescription([
        DeclareLaunchArgument('input_topic', default_value='/uav_1/mission_raw'),
        DeclareLaunchArgument('output_topic', default_value='/uav_1/mission_sim'),
        DeclareLaunchArgument('scenario', default_value='clean'),
        DeclareLaunchArgument('enabled', default_value='true'),
        DeclareLaunchArgument('random_seed', default_value='42'),

        # Negative values mean "use scenario defaults".
        DeclareLaunchArgument('drop_probability', default_value='-1.0'),
        DeclareLaunchArgument('delay_ms', default_value='-1.0'),
        DeclareLaunchArgument('blackout_start_sec', default_value='-1.0'),
        DeclareLaunchArgument('blackout_duration_sec', default_value='-1.0'),

        DeclareLaunchArgument('enable_stats_log', default_value='true'),
        DeclareLaunchArgument('stats_log_period_sec', default_value='2.0'),
        Node(
            package='comm_layer',
            executable='network_simulator_node',
            name='network_simulator_node',
            output='screen',
            parameters=[{
                'input_topic': input_topic,
                'output_topic': output_topic,
                'scenario': scenario,
                'enabled': enabled,
                'random_seed': random_seed,
                'drop_probability': drop_probability,
                'delay_ms': delay_ms,
                'blackout_start_sec': blackout_start_sec,
                'blackout_duration_sec': blackout_duration_sec,
                'enable_stats_log': enable_stats_log,
                'stats_log_period_sec': stats_log_period_sec,
            }],
        ),
    ])
