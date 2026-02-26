#!/usr/bin/env python3
import random
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class NetworkSimulatorNode(Node):
    def __init__(self) -> None:
        super().__init__('network_simulator_node')

        self.declare_parameter('input_topic', '/uav_1/mission_raw')
        self.declare_parameter('output_topic', '/uav_1/mission_sim')
        self.declare_parameter('scenario', 'clean')
        self.declare_parameter('enabled', True)
        self.declare_parameter('random_seed', 42)

        # Negative values indicate "use scenario defaults".
        self.declare_parameter('drop_probability', -1.0)
        self.declare_parameter('delay_ms', -1.0)
        self.declare_parameter('blackout_start_sec', -1.0)
        self.declare_parameter('blackout_duration_sec', -1.0)

        self.declare_parameter('enable_stats_log', True)
        self.declare_parameter('stats_log_period_sec', 2.0)

        self._input_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        self._output_topic = self.get_parameter('output_topic').get_parameter_value().string_value

        self._scenario = self.get_parameter('scenario').get_parameter_value().string_value.strip().lower()
        self._enabled = self.get_parameter('enabled').get_parameter_value().bool_value
        self._random_seed = int(self.get_parameter('random_seed').value)

        self._drop_probability = self.get_parameter('drop_probability').get_parameter_value().double_value
        self._delay_ms = self.get_parameter('delay_ms').get_parameter_value().double_value
        self._blackout_start_sec = self.get_parameter('blackout_start_sec').get_parameter_value().double_value
        self._blackout_duration_sec = self.get_parameter('blackout_duration_sec').get_parameter_value().double_value

        self._enable_stats_log = self.get_parameter('enable_stats_log').get_parameter_value().bool_value
        self._stats_log_period_sec = self.get_parameter('stats_log_period_sec').get_parameter_value().double_value

        self._apply_scenario_defaults()

        self._drop_probability = min(max(self._drop_probability, 0.0), 1.0)
        self._delay_ms = max(self._delay_ms, 0.0)
        self._blackout_duration_sec = max(self._blackout_duration_sec, 0.0)

        self._rng = random.Random(self._random_seed)

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
            f'scenario={self._scenario}, enabled={self._enabled}, seed={self._random_seed}, '
            f'input={self._input_topic}, output={self._output_topic}, '
            f'drop_probability={self._drop_probability:.3f}, delay_ms={self._delay_ms:.1f}, '
            f'blackout_start_sec={self._blackout_start_sec:.2f}, '
            f'blackout_duration_sec={self._blackout_duration_sec:.2f}'
        )

    def _apply_scenario_defaults(self) -> None:
        presets = {
            'clean': {'drop_probability': 0.0, 'delay_ms': 0.0, 'blackout_start_sec': -1.0, 'blackout_duration_sec': 0.0},
            'drop': {'drop_probability': 0.35, 'delay_ms': 0.0, 'blackout_start_sec': -1.0, 'blackout_duration_sec': 0.0},
            'delay': {'drop_probability': 0.0, 'delay_ms': 250.0, 'blackout_start_sec': -1.0, 'blackout_duration_sec': 0.0},
            'blackout': {'drop_probability': 0.0, 'delay_ms': 0.0, 'blackout_start_sec': 8.0, 'blackout_duration_sec': 8.0},
        }

        if self._scenario not in presets:
            self.get_logger().warn(f'Unknown scenario "{self._scenario}"; falling back to clean')
            self._scenario = 'clean'

        preset = presets[self._scenario]

        if self._drop_probability < 0.0:
            self._drop_probability = preset['drop_probability']
        if self._delay_ms < 0.0:
            self._delay_ms = preset['delay_ms']
        if self._blackout_start_sec < 0.0:
            self._blackout_start_sec = preset['blackout_start_sec']
        if self._blackout_duration_sec < 0.0:
            self._blackout_duration_sec = preset['blackout_duration_sec']

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

        if not self._enabled:
            self._publish_msg(msg.data)
            return

        if self._in_blackout():
            self._dropped_count += 1
            self._blackout_dropped_count += 1
            return

        if self._rng.random() < self._drop_probability:
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
