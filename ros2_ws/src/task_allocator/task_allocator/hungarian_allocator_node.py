import json
import math

import numpy as np
from scipy.optimize import linear_sum_assignment

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import String


class HungarianAllocatorNode(Node):
    def __init__(self):
        super().__init__('hungarian_allocator_node')

        self.declare_parameter('ugv_names', ['ugv_1', 'ugv_2', 'ugv_3'])
        self.declare_parameter('publish_rate_hz', 1.0)

        self._ugv_names = self.get_parameter('ugv_names').value
        # Latest (x, y) per UGV; None until first odom arrives
        self._positions = {name: None for name in self._ugv_names}
        self._targets = []

        for name in self._ugv_names:
            self.create_subscription(
                Odometry,
                f'/{name}/odom',
                lambda msg, n=name: self._odom_cb(msg, n),
                10,
            )

        self.create_subscription(String, '/uav_1/targets', self._targets_cb, 10)

        self._pub = self.create_publisher(String, '/allocation/assignments', 10)

        rate = self.get_parameter('publish_rate_hz').value
        self.create_timer(1.0 / rate, self._allocate)

    def _odom_cb(self, msg: Odometry, name: str):
        p = msg.pose.pose.position
        self._positions[name] = (p.x, p.y)

    def _targets_cb(self, msg: String):
        data = json.loads(msg.data)
        self._targets = data.get('targets', [])

    def _allocate(self):
        # Wait until all UGV positions are known and targets are available
        positions = {n: p for n, p in self._positions.items() if p is not None}
        if not positions or not self._targets:
            return

        ugv_names = list(positions.keys())
        n_ugv = len(ugv_names)
        n_tgt = len(self._targets)
        n = max(n_ugv, n_tgt)

        # Build cost matrix (Euclidean distance), padded to square with zeros
        cost = np.zeros((n, n))
        for i, name in enumerate(ugv_names):
            ux, uy = positions[name]
            for j, tgt in enumerate(self._targets):
                cost[i, j] = math.hypot(tgt['x'] - ux, tgt['y'] - uy)

        row_ind, col_ind = linear_sum_assignment(cost)

        assignments = []
        for i, j in zip(row_ind, col_ind):
            if i < n_ugv and j < n_tgt:
                assignments.append({
                    'ugv': ugv_names[i],
                    'target_id': self._targets[j]['id'],
                    'target_x': self._targets[j]['x'],
                    'target_y': self._targets[j]['y'],
                    'cost': round(cost[i, j], 3),
                })

        total = round(sum(a['cost'] for a in assignments), 3)
        msg = String()
        msg.data = json.dumps({'assignments': assignments, 'total_cost': total})
        self._pub.publish(msg)
        self.get_logger().info(f'Assigned {len(assignments)} tasks, total cost {total}m')


def main(args=None):
    rclpy.init(args=args)
    node = HungarianAllocatorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
