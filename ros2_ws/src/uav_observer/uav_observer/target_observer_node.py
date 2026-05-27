import json
import math

import rclpy
from rclpy.node import Node
from ros_gz_interfaces.msg import LogicalCameraImage
from std_msgs.msg import String

TARGET_PREFIX = 'target_'


def _rotation_matrix(roll, pitch, yaw):
    """Build a 3×3 rotation matrix from RPY (Rz @ Ry @ Rx)."""
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return [
        [cy * cp,  cy * sp * sr - sy * cr,  cy * sp * cr + sy * sr],
        [sy * cp,  sy * sp * sr + cy * cr,  sy * sp * cr - cy * sr],
        [-sp,      cp * sr,                  cp * cr               ],
    ]


class TargetObserverNode(Node):
    def __init__(self):
        super().__init__('target_observer_node')

        self.declare_parameter('uav_x', -2.0)
        self.declare_parameter('uav_y', 0.0)
        self.declare_parameter('uav_z', 5.0)
        self.declare_parameter('camera_roll', 0.0)
        self.declare_parameter('camera_pitch', 1.5708)  # π/2 — nadir view
        self.declare_parameter('camera_yaw', 0.0)

        self._uav_pos = (
            self.get_parameter('uav_x').value,
            self.get_parameter('uav_y').value,
            self.get_parameter('uav_z').value,
        )
        # Rotation matrix: transforms a vector from camera frame to world frame.
        self._R = _rotation_matrix(
            self.get_parameter('camera_roll').value,
            self.get_parameter('camera_pitch').value,
            self.get_parameter('camera_yaw').value,
        )

        # 'logical_camera' is resolved under the uav_1 namespace by the launch file.
        self.create_subscription(LogicalCameraImage, 'logical_camera', self._camera_cb, 10)
        self._pub = self.create_publisher(String, 'targets', 10)

        self.get_logger().info('Target observer ready — awaiting logical camera data')

    def _camera_cb(self, msg: LogicalCameraImage):
        R = self._R
        ux, uy, uz = self._uav_pos

        detected = []
        for model in msg.model:
            if not model.name.startswith(TARGET_PREFIX):
                continue
            cx = model.pose.position.x
            cy_val = model.pose.position.y
            cz = model.pose.position.z
            wx = R[0][0] * cx + R[0][1] * cy_val + R[0][2] * cz + ux
            wy = R[1][0] * cx + R[1][1] * cy_val + R[1][2] * cz + uy
            detected.append({'id': model.name, 'x': round(wx, 3), 'y': round(wy, 3)})

        out = String()
        out.data = json.dumps({'targets': detected})
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = TargetObserverNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
