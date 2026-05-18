import pytest
import unittest

import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import launch_testing.markers

import rclpy
from launch_testing_ros import WaitForTopics
from geometry_msgs.msg import Twist
from std_msgs.msg import String


@pytest.mark.launch_test
def generate_test_description():
    uav_node = launch_ros.actions.Node(
        package='uav_observer',
        executable='target_observer_node',
        namespace='uav_1',
        parameters=[{
            'publish_rate_hz': 5.0,
            'detection_radius': 50.0,
        }],
        output='screen',
    )
    ugv_node = launch_ros.actions.Node(
        package='ugv_nav',
        executable='ugv_goal_follower_node',
        parameters=[{'ugv_name': 'ugv_1'}],
        output='screen',
    )
    return launch.LaunchDescription([
        uav_node,
        ugv_node,
        launch_testing.actions.ReadyToTest(),
    ])


@launch_testing.markers.keep_alive
class TestUAVUGVLink(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def test_uav_observer_publishes_targets(self):
        wt = WaitForTopics([('/uav_1/targets', String)], timeout=10.0)
        try:
            assert wt.wait(), 'No message on /uav_1/targets within 10 s'
        finally:
            wt.shutdown()

    def test_ugv_cmd_vel_publishes(self):
        wt = WaitForTopics([('/ugv_1/cmd_vel', Twist)], timeout=10.0)
        try:
            assert wt.wait(), 'No message on /ugv_1/cmd_vel within 10 s'
        finally:
            wt.shutdown()
