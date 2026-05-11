"""
Demo display node — run in a dedicated terminal during recording:
  ros2 run ugv_nav demo_display_node
"""
import json
import math

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import String

_ARRIVAL_RADIUS = 1.0
_W    = 48
_SEP  = '─' * _W
_DSEP = '═' * _W


def _dist(ax, ay, bx, by):
    return math.hypot(bx - ax, by - ay)


class DemoDisplayNode(Node):

    _ST_WAITING = 'waiting'
    _ST_RUNNING = 'running'
    _ST_DONE    = 'done'

    def __init__(self):
        super().__init__('demo_display_node')

        self.declare_parameter('ugv_names', ['ugv_1', 'ugv_2', 'ugv_3'])
        self._ugv_names = self.get_parameter('ugv_names').value

        self._state         = self._ST_WAITING
        self._poses         = {}
        self._targets       = []   # populated from /uav_1/targets OR assignment
        self._assignments   = {}
        self._arrived       = set()

        for name in self._ugv_names:
            self.create_subscription(
                Odometry, f'/{name}/odom',
                lambda msg, n=name: self._odom_cb(msg, n), 10,
            )
        self.create_subscription(String, '/uav_1/targets',      self._targets_cb, 10)
        self.create_subscription(String, '/allocation/assignments', self._assignment_cb, 10)

        self.create_timer(0.3, self._check_arrivals)

        print(f'\n{_DSEP}')
        print(f'  MRTA DEMO  ·  Hungarian Allocation')
        print(f'{_DSEP}')
        print(f'  Waiting for robots and targets...')

    # ── subscriptions ─────────────────────────────────────────────────────────

    def _odom_cb(self, msg: Odometry, name: str):
        p = msg.pose.pose.position
        self._poses[name] = (p.x, p.y, p.z)

    def _targets_cb(self, msg: String):
        data = json.loads(msg.data)
        targets = data.get('targets', [])
        if targets and not self._targets:
            self._targets = sorted(targets, key=lambda t: t['id'])

    def _assignment_cb(self, msg: String):
        if self._state != self._ST_WAITING:
            return

        data = json.loads(msg.data)
        assignments = {a['ugv']: a for a in data.get('assignments', [])}
        if not assignments:
            return
        if len(assignments) < len(self._ugv_names):
            return  # wait until all UGVs are assigned

        # If the targets topic was missed, reconstruct from the assignment payload.
        if not self._targets:
            seen = {}
            for a in assignments.values():
                if a['target_id'] not in seen:
                    seen[a['target_id']] = {'id': a['target_id'],
                                            'x': a['target_x'],
                                            'y': a['target_y']}
            self._targets = sorted(seen.values(), key=lambda t: t['id'])

        # Snapshot poses now — UGVs have barely moved yet (x, y, z).
        initial_poses = dict(self._poses)
        self._assignments = assignments
        self._state = self._ST_RUNNING

        self._print_initial_state(initial_poses)
        self._print_assignment()

    # ── display ───────────────────────────────────────────────────────────────

    def _print_initial_state(self, initial_poses: dict):
        print(f'\n{_DSEP}')
        print(f'  INITIAL STATE')
        print(f'{_SEP}')

        print(f'\n  Robots')
        for name in sorted(initial_poses):
            x, y, z = initial_poses[name]
            print(f'  {name}   ({x:+7.2f}, {y:+7.2f}, {z:+.2f})')

        print(f'\n  Targets')
        for t in self._targets:
            print(f'  {t["id"]}     ({t["x"]:+7.2f}, {t["y"]:+7.2f})')

        print(f'\n{_SEP}')
        print(f'  Cost matrix  (Euclidean distance, m)')
        print(f'{_SEP}')
        tids = [t['id'] for t in self._targets]
        print('           ' + ''.join(f'{tid:>8}' for tid in tids))
        for name in sorted(initial_poses):
            ux, uy, _ = initial_poses[name]
            row = ''.join(f'{_dist(ux, uy, t["x"], t["y"]):8.2f}' for t in self._targets)
            print(f'  {name}   {row}')

        print(f'\n  Running Hungarian algorithm...')

    def _print_assignment(self):
        total = sum(a['cost'] for a in self._assignments.values())
        print(f'{_DSEP}')
        print(f'  ASSIGNMENT RESULT')
        print(f'{_SEP}')
        for name in sorted(self._assignments):
            a = self._assignments[name]
            print(
                f"  {name}  →  {a['target_id']}"
                f"  ({a['target_x']:+.1f}, {a['target_y']:+.1f})"
                f"  {a['cost']:.2f} m"
            )
        print(f'{_SEP}')
        print(f'  Total cost : {total:.2f} m')
        print(f'{_DSEP}')
        print(f'\n  UGVs en route...\n')

    # ── arrival monitor ───────────────────────────────────────────────────────

    def _check_arrivals(self):
        if self._state != self._ST_RUNNING:
            return
        for ugv, a in self._assignments.items():
            if ugv in self._arrived:
                continue
            pose = self._poses.get(ugv)
            if pose and _dist(pose[0], pose[1], a['target_x'], a['target_y']) < _ARRIVAL_RADIUS:
                self._arrived.add(ugv)
                px, py, pz = pose
                tx, ty = a['target_x'], a['target_y']
                print(
                    f'  ✓  {ugv}  ({px:+.2f}, {py:+.2f}, {pz:+.2f})'
                    f'  arrived at  {a["target_id"]}  ({tx:+.2f}, {ty:+.2f}, +0.00)'
                )
                if len(self._arrived) == len(self._assignments):
                    total = sum(x['cost'] for x in self._assignments.values())
                    print(f'{_SEP}')
                    print(f'  All targets reached.  Total: {total:.2f} m')
                    print(f'{_DSEP}\n')
                    self._state = self._ST_DONE


def main(args=None):
    rclpy.init(args=args)
    node = DemoDisplayNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
