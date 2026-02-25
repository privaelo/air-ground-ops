# resilient_uav_ugv_autonomy

ROS 2 Jazzy + Gazebo Harmonic framework for resilient UAV-UGV autonomy research under communication disruption.

## Quick Start

```bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

Launch simulation (default world pinned to `empty.sdf` with ground plane):

```bash
ros2 launch multi_robot_bringup simulation.launch.py use_rviz:=false
```

Launch simulation with explicit world and spawn positions:

```bash
ros2 launch multi_robot_bringup simulation.launch.py \
  use_rviz:=false \
  gz_args:='-r empty.sdf' \
  ugv_spawn_x:=0.0 ugv_spawn_y:=0.0 ugv_spawn_z:=0.0 \
  uav_spawn_x:=0.0 uav_spawn_y:=0.0 uav_spawn_z:=1.0
```

Startup sanity check:

```bash
ros2 topic echo /ugv_1/odom --once
```

If stable, initial `pose.pose.position.z` should remain near the expected chassis height (around `0.17`) and not diverge rapidly.

Teleop UGV:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/ugv_1/cmd_vel
```

Teleop behavior note:
- `teleop_twist_keyboard` keeps publishing the last velocity command. After pressing `i`, press `k` to command zero velocity.

Troubleshooting note:
- If the UGV drops, jumps, or becomes uncontrollable, verify the world includes a ground plane and wheel/base collision geometry starts non-penetrating.

Launch communication simulator (Phase 2 bootstrap):

```bash
ros2 launch comm_layer network_simulation.launch.py \
  input_topic:=/uav_1/info \
  output_topic:=/uav_1/info_sim \
  drop_probability:=0.2 \
  delay_ms:=150 \
  blackout_start_sec:=20.0 \
  blackout_duration_sec:=10.0
```

## Current Status

- Phase 1: simulation bringup complete
- Phase 2: `network_simulator_node` bootstrap added in `comm_layer`
