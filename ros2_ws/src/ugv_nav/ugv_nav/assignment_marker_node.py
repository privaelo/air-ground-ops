import json

import rclpy
from rclpy.node import Node
from builtin_interfaces.msg import Duration
from geometry_msgs.msg import Point
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from visualization_msgs.msg import Marker, MarkerArray

_COLORS = {
    'ugv_1': (1.0, 0.25, 0.25),   # red
    'ugv_2': (0.25, 1.0, 0.25),   # green
    'ugv_3': (0.35, 0.65, 1.0),   # blue
}

_DYNAMIC_LIFETIME = Duration(sec=2)   # refreshed at 10 Hz; expires if node dies
_STATIC_LIFETIME = Duration(sec=0)    # indefinite; stays until DELETE


class AssignmentMarkerNode(Node):
    def __init__(self):
        super().__init__('assignment_marker_node')

        self.declare_parameter('ugv_names', ['ugv_1', 'ugv_2', 'ugv_3'])

        ugv_names = self.get_parameter('ugv_names').value

        # OdometryPublisher gives world-frame positions directly.
        self._odom = {name: None for name in ugv_names}
        self._assignments = {}
        self._targets_published = False

        for name in ugv_names:
            self.create_subscription(
                Odometry,
                f'/{name}/odom',
                lambda msg, n=name: self._odom_cb(msg, n),
                10,
            )

        self.create_subscription(String, '/allocation/assignments', self._assignment_cb, 10)
        self._pub = self.create_publisher(MarkerArray, '/allocation/markers', 10)
        self.create_timer(0.1, self._publish)

        self.get_logger().info('Assignment marker node ready')

    def _odom_cb(self, msg: Odometry, name: str):
        p = msg.pose.pose.position
        self._odom[name] = (p.x, p.y)

    def _assignment_cb(self, msg: String):
        data = json.loads(msg.data)
        self._assignments = {a['ugv']: a for a in data.get('assignments', [])}

    def _world_pos(self, name: str):
        return self._odom.get(name)  # OdometryPublisher already gives world frame

    def _publish(self):
        if not self._assignments:
            return

        array = MarkerArray()
        marker_id = 0
        stamp = self.get_clock().now().to_msg()

        # Target discs — publish once with indefinite lifetime
        if not self._targets_published:
            seen = set()
            for assignment in self._assignments.values():
                tid = assignment['target_id']
                if tid in seen:
                    continue
                seen.add(tid)
                disc = _marker(stamp, 'targets', marker_id, Marker.CYLINDER)
                marker_id += 1
                disc.lifetime = _STATIC_LIFETIME
                disc.pose.position.x = assignment['target_x']
                disc.pose.position.y = assignment['target_y']
                disc.pose.position.z = 0.05
                disc.pose.orientation.w = 1.0
                disc.scale.x = 0.8
                disc.scale.y = 0.8
                disc.scale.z = 0.1
                disc.color.r = 1.0
                disc.color.g = 0.9
                disc.color.b = 0.0
                disc.color.a = 1.0
                array.markers.append(disc)

                lbl = _marker(stamp, 'target_labels', marker_id, Marker.TEXT_VIEW_FACING)
                marker_id += 1
                lbl.lifetime = _STATIC_LIFETIME
                lbl.pose.position.x = assignment['target_x']
                lbl.pose.position.y = assignment['target_y']
                lbl.pose.position.z = 0.9
                lbl.pose.orientation.w = 1.0
                lbl.scale.z = 0.5
                lbl.color.r = 1.0
                lbl.color.g = 0.95
                lbl.color.b = 0.0
                lbl.color.a = 1.0
                lbl.text = tid
                array.markers.append(lbl)

            self._targets_published = bool(seen)

        # Per-UGV dynamic markers
        for ugv_name, assignment in self._assignments.items():
            world_pos = self._world_pos(ugv_name)
            if world_pos is None:
                continue

            r, g, b = _COLORS.get(ugv_name, (1.0, 1.0, 1.0))
            wx, wy = world_pos
            tx, ty = assignment['target_x'], assignment['target_y']

            # Sphere at UGV current world position
            sphere = _marker(stamp, 'ugv_positions', marker_id, Marker.SPHERE)
            marker_id += 1
            sphere.lifetime = _DYNAMIC_LIFETIME
            sphere.pose.position.x = wx
            sphere.pose.position.y = wy
            sphere.pose.position.z = 0.35
            sphere.pose.orientation.w = 1.0
            sphere.scale.x = sphere.scale.y = sphere.scale.z = 0.5
            sphere.color.r = r
            sphere.color.g = g
            sphere.color.b = b
            sphere.color.a = 1.0
            array.markers.append(sphere)

            # Line from UGV to target
            line = _marker(stamp, 'lines', marker_id, Marker.LINE_STRIP)
            marker_id += 1
            line.lifetime = _DYNAMIC_LIFETIME
            line.scale.x = 0.1
            line.color.r = r
            line.color.g = g
            line.color.b = b
            line.color.a = 0.8
            line.points = [_pt(wx, wy, 0.35), _pt(tx, ty, 0.35)]
            array.markers.append(line)

            # Label at line midpoint
            lbl = _marker(stamp, 'labels', marker_id, Marker.TEXT_VIEW_FACING)
            marker_id += 1
            lbl.lifetime = _DYNAMIC_LIFETIME
            lbl.pose.position.x = (wx + tx) / 2.0
            lbl.pose.position.y = (wy + ty) / 2.0
            lbl.pose.position.z = 1.4
            lbl.pose.orientation.w = 1.0
            lbl.scale.z = 0.5
            lbl.color.r = r
            lbl.color.g = g
            lbl.color.b = b
            lbl.color.a = 1.0
            lbl.text = f"{ugv_name} → {assignment['target_id']} ({assignment['cost']}m)"
            array.markers.append(lbl)

        self._pub.publish(array)


def _marker(stamp, ns: str, mid: int, mtype: int) -> Marker:
    m = Marker()
    m.header.frame_id = 'world'
    m.header.stamp = stamp
    m.ns = ns
    m.id = mid
    m.type = mtype
    m.action = Marker.ADD
    return m


def _pt(x: float, y: float, z: float) -> Point:
    p = Point()
    p.x = x
    p.y = y
    p.z = z
    return p


def main(args=None):
    rclpy.init(args=args)
    node = AssignmentMarkerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
