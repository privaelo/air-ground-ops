#!/usr/bin/env python3
import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class UgvMissionReceiverNode(Node):
    def __init__(self) -> None:
        super().__init__('ugv_mission_receiver_node')

        self.declare_parameter('input_topic', '/uav_1/mission_sim')
        self.declare_parameter('stats_log_period_sec', 2.0)

        self._input_topic = self.get_parameter('input_topic').value
        self._stats_log_period_sec = max(float(self.get_parameter('stats_log_period_sec').value), 0.5)

        self._received_count = 0
        self._accepted_count = 0
        self._rejected_count = 0

        self.create_subscription(String, self._input_topic, self._on_msg, 10)
        self.create_timer(self._stats_log_period_sec, self._log_stats)

        self.get_logger().info(
            f'ugv_mission_receiver_node started: input_topic={self._input_topic}'
        )

    def _validate(self, payload) -> bool:
        if not isinstance(payload, dict):
            return False
        if payload.get('msg_type') != 'mission_directive':
            return False
        if not isinstance(payload.get('mission_id'), str):
            return False
        if not isinstance(payload.get('priority'), int):
            return False

        target_xy = payload.get('target_xy')
        if not isinstance(target_xy, dict):
            return False
        if not isinstance(target_xy.get('x'), (int, float)):
            return False
        if not isinstance(target_xy.get('y'), (int, float)):
            return False

        if not isinstance(payload.get('timestamp_sec'), (int, float)):
            return False

        return True

    def _on_msg(self, msg: String) -> None:
        self._received_count += 1
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            self._rejected_count += 1
            return

        if not self._validate(payload):
            self._rejected_count += 1
            return

        self._accepted_count += 1

    def _log_stats(self) -> None:
        self.get_logger().info(
            'ugv_mission_receiver stats: '
            f'received={self._received_count}, '
            f'accepted={self._accepted_count}, '
            f'rejected={self._rejected_count}'
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = UgvMissionReceiverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
