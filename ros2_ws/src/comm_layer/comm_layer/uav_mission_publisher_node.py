#!/usr/bin/env python3
import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class UavMissionPublisherNode(Node):
    def __init__(self) -> None:
        super().__init__('uav_mission_publisher_node')

        self.declare_parameter('output_topic', '/uav_1/mission_raw')
        self.declare_parameter('publish_rate_hz', 1.0)
        self.declare_parameter('target_x', 10.0)
        self.declare_parameter('target_y', 0.0)
        self.declare_parameter('priority', 1)
        self.declare_parameter('mission_id_prefix', 'mission')

        self._output_topic = self.get_parameter('output_topic').value
        self._publish_rate_hz = max(float(self.get_parameter('publish_rate_hz').value), 0.1)
        self._target_x = float(self.get_parameter('target_x').value)
        self._target_y = float(self.get_parameter('target_y').value)
        self._priority = int(self.get_parameter('priority').value)
        self._mission_id_prefix = str(self.get_parameter('mission_id_prefix').value)

        self._pub = self.create_publisher(String, self._output_topic, 10)
        self._seq = 0

        self.create_timer(1.0 / self._publish_rate_hz, self._publish_mission)

        self.get_logger().info(
            'uav_mission_publisher_node started: '
            f'output_topic={self._output_topic}, rate_hz={self._publish_rate_hz:.2f}, '
            f'target=({self._target_x:.2f}, {self._target_y:.2f}), priority={self._priority}'
        )

    def _publish_mission(self) -> None:
        self._seq += 1
        now_sec = self.get_clock().now().nanoseconds / 1e9

        payload = {
            'msg_type': 'mission_directive',
            'mission_id': f'{self._mission_id_prefix}-{self._seq}',
            'target_xy': {
                'x': self._target_x,
                'y': self._target_y,
            },
            'priority': self._priority,
            'timestamp_sec': now_sec,
        }

        msg = String()
        msg.data = json.dumps(payload)
        self._pub.publish(msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = UavMissionPublisherNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
