#!/usr/bin/env python3
import random
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class NetworkSimulatorNode(Node):
    def __init__(self) -> None:
        super().__init__('network_simulator_node')

        self.declare_parameter('input_topic', '/uav_1/info')
        self.declare_parameter('output_topic', '/uav_1/info_sim')
        self.declare_parameter('drop_probability', 0.0)
        self.declare_parameter('delay_ms', 0.0)
        self.declare_parameter('blackout_start_sec', -1.0)
        self.declare_parameter('blackout_duration_sec', 0.0)
        self.declare_parameter('enable_stats_log', True)
        self.declare_parameter('stats_log_period_sec', 2.0)

        self._input_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        self._output_topic = self.get_parameter('output_topic').get_parameter_value().string_value
        self._drop_probability = self.get_parameter('drop_probability').get_parameter_value().double_value
        self._delay_ms = self.get_parameter('delay_ms').get_parameter_value().double_value
        self._blackout_start_sec = self.get_parameter('blackout_start_sec').get_parameter_value().double_value
        self._blackout_duration_sec = self.get_parameter('blackout_duration_sec').get_parameter_value().double_value
        self._enable_stats_log = self.get_parameter('enable_stats_log').get_parameter_value().bool_value
        self._stats_log_period_sec = self.get_parameter('stats_log_period_sec').get_parameter_value().double_value

        self._drop_probability = min(max(self._drop_probability, 0.0), 1.0)
        self._delay_ms = max(self._delay_ms, 0.0)
        self._blackout_duration_sec = max(self._blackout_duration_sec, 0.0)

        self._start_time_ns = self.get_clock().now().nanoseconds

        self._received_count = 0
        self._forwarded_count = 0
        self._dropped_count = 0
        self._blackout_dropped_count = 0
        self._probability_dropped_count = 0
        self._delayed_forward_count = 0

        self._pub = self.create_publisher(String, self._output_topic, 10)
        self._sub = self.create_subscription(String, self._input_topic, self._on_msg, 10)

        self._stats_timer = None
        if self._enable_stats_log:
            self._stats_timer = self.create_timer(self._stats_log_period_sec, self._log_stats)

        self.get_logger().info(
            'network_simulator_node started: '
            f'input={self._input_topic}, output={self._output_topic}, '
            f'drop_probability={self._drop_probability:.3f}, delay_ms={self._delay_ms:.1f}, '
            f'blackout_start_sec={self._blackout_start_sec:.2f}, '
            f'blackout_duration_sec={self._blackout_duration_sec:.2f}'
        )

    def _elapsed_sec(self) -> float:
        now_ns = self.get_clock().now().nanoseconds
        return (now_ns - self._start_time_ns) / 1e9

    def _in_blackout(self) -> bool:
        if self._blackout_start_sec < 0.0 or self._blackout_duration_sec <= 0.0:
            return False

        t = self._elapsed_sec()
        blackout_end = self._blackout_start_sec + self._blackout_duration_sec
        return self._blackout_start_sec <= t <= blackout_end

    def _on_msg(self, msg: String) -> None:
        self._received_count += 1

        if self._in_blackout():
            self._dropped_count += 1
            self._blackout_dropped_count += 1
            return

        if random.random() < self._drop_probability:
            self._dropped_count += 1
            self._probability_dropped_count += 1
            return

        delay_sec = self._delay_ms / 1000.0
        if delay_sec > 0.0:
            self._delayed_forward_count += 1
            timer = threading.Timer(delay_sec, self._publish_msg, args=(msg.data,))
            timer.daemon = True
            timer.start()
        else:
            self._publish_msg(msg.data)

    def _publish_msg(self, data: str) -> None:
        out = String()
        out.data = data
        self._pub.publish(out)
        self._forwarded_count += 1

    def _log_stats(self) -> None:
        self.get_logger().info(
            'network_simulator stats: '
            f'received={self._received_count}, '
            f'forwarded={self._forwarded_count}, '
            f'dropped={self._dropped_count}, '
            f'dropped_blackout={self._blackout_dropped_count}, '
            f'dropped_probability={self._probability_dropped_count}, '
            f'delayed_forward={self._delayed_forward_count}'
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = NetworkSimulatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
