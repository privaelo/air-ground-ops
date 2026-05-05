import json
import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class TargetObserverNode(Node):
    def __init__(self):
        super().__init__('target_observer_node')

        self.declare_parameter('uav_x', -2.0)
        self.declare_parameter('uav_y', 0.0)
        self.declare_parameter('detection_radius', 50.0)
        self.declare_parameter('publish_rate_hz', 1.0)

        # Targets declared as flat params: target_ids, target_xs, target_ys
        self.declare_parameter('target_ids', ['t1', 't2', 't3'])
        self.declare_parameter('target_xs', [8.0, -8.0, 8.0])
        self.declare_parameter('target_ys', [7.0, -7.0, -7.0])

        self._pub = self.create_publisher(String, 'targets', 10)

        rate = self.get_parameter('publish_rate_hz').value
        self.create_timer(1.0 / rate, self._observe)

    def _observe(self):
        uav_x = self.get_parameter('uav_x').value
        uav_y = self.get_parameter('uav_y').value
        radius = self.get_parameter('detection_radius').value

        ids = self.get_parameter('target_ids').value
        xs = self.get_parameter('target_xs').value
        ys = self.get_parameter('target_ys').value

        detected = []
        for tid, tx, ty in zip(ids, xs, ys):
            dist = math.hypot(tx - uav_x, ty - uav_y)
            if dist <= radius:
                detected.append({'id': tid, 'x': float(tx), 'y': float(ty)})

        msg = String()
        msg.data = json.dumps({'targets': detected})
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = TargetObserverNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
