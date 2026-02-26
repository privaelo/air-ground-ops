# resilient_uav_ugv_autonomy

ROS 2 Jazzy + Gazebo Harmonic framework for resilient UAV-UGV autonomy research under communication disruption.

## Quick Start

```bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Phase 1 Baseline (No Mission Comms)

```bash
ros2 launch multi_robot_bringup simulation.launch.py use_rviz:=false
```

## Phase 2 Realistic Environment Defaults

The default world is now a local obstacle world:
- `ros2_ws/src/multi_robot_bringup/worlds/urban_obstacles.sdf`
- UAV default spawn around 5m altitude
- UAV/UGV are spatially separated by default

Launch with explicit world and spawn overrides:

```bash
ros2 launch multi_robot_bringup simulation.launch.py \
  use_rviz:=false \
  world_file:=/absolute/path/to/world.sdf \
  uav_spawn_x:=10.0 uav_spawn_y:=0.0 uav_spawn_z:=5.0 \
  ugv_spawn_x:=-2.0 ugv_spawn_y:=0.0 ugv_spawn_z:=0.0
```

## UGV Teleop

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/ugv_1/cmd_vel
```

`teleop_twist_keyboard` keeps publishing the last command; use `k` to command zero velocity.

## Phase 2 Mission Communication

Mission topic flow:
- UAV mission publisher -> `/uav_1/mission_raw`
- Network simulator -> `/uav_1/mission_sim`
- UGV mission receiver subscribes to `/uav_1/mission_sim`

### Clean scenario (baseline relay)

```bash
ros2 launch multi_robot_bringup simulation.launch.py \
  use_rviz:=false \
  use_mission_comms:=true \
  use_network_sim:=true \
  network_scenario:=clean
```

### Drop scenario

```bash
ros2 launch multi_robot_bringup simulation.launch.py \
  use_rviz:=false \
  use_mission_comms:=true \
  use_network_sim:=true \
  network_scenario:=drop
```

### Delay scenario

```bash
ros2 launch multi_robot_bringup simulation.launch.py \
  use_rviz:=false \
  use_mission_comms:=true \
  use_network_sim:=true \
  network_scenario:=delay
```

### Blackout scenario

```bash
ros2 launch multi_robot_bringup simulation.launch.py \
  use_rviz:=false \
  use_mission_comms:=true \
  use_network_sim:=true \
  network_scenario:=blackout
```

### Manual override example

```bash
ros2 launch multi_robot_bringup simulation.launch.py \
  use_rviz:=false \
  use_mission_comms:=true \
  use_network_sim:=true \
  network_scenario:=clean \
  network_drop_probability:=0.4 \
  network_delay_ms:=200
```

## Current Status

- Phase 1: simulation bringup complete
- Phase 2: realistic world + UAV->UGV mission communication + disruption scenarios implemented

