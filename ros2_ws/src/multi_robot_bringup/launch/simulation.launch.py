from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    use_rviz = LaunchConfiguration('use_rviz')

    # Gazebo launcher
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')
    gz_launch = os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')

    # UAV / UGV launchers (robot_state_publisher + optional RViz)
    uav_share = get_package_share_directory('uav_description')
    uav_launch = os.path.join(uav_share, 'launch', 'uav.launch.py')

    ugv_share = get_package_share_directory('ugv_description')
    ugv_launch = os.path.join(ugv_share, 'launch', 'ugv.launch.py')
    ugv_sdf = os.path.join(ugv_share, 'models', 'ugv_diffdrive.sdf')

    start_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch),
        launch_arguments={}.items(),
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

    # UGV state publisher (namespaced); we do NOT want a second RViz instance
    start_ugv = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(ugv_launch),
        launch_arguments={
            'namespace': 'ugv_1',
            'use_rviz': 'false',
            'use_sim_time': 'true',
        }.items(),
    )

    # Spawn UAV from its namespaced /robot_description
    spawn_uav = ExecuteProcess(
        cmd=[
            'ros2', 'run', 'ros_gz_sim', 'create',
            '-name', 'uav_1',
            '-topic', '/uav_1/robot_description',
        ],
        output='screen',
    )

    # Spawn UGV from SDF (diff drive system)
    spawn_ugv = ExecuteProcess(
        cmd=[
            'ros2', 'run', 'ros_gz_sim', 'create',
            '-name', 'ugv_1',
            '-file', ugv_sdf,
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

    return LaunchDescription([
        DeclareLaunchArgument('use_rviz', default_value='false'),

        start_gazebo,
        clock_bridge,

        start_uav,
        start_ugv,

        TimerAction(period=2.0, actions=[spawn_uav]),
        TimerAction(period=2.5, actions=[spawn_ugv]),

        # Bridges (start after spawn is fine; bridges can be up earlier too)
        TimerAction(period=3.0, actions=[cmd_vel_bridge]),
        TimerAction(period=3.0, actions=[odom_bridge]),
    ])