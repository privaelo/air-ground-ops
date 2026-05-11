# air-ground-ops

A ROS 2 + Gazebo sandbox for studying and comparing Multi-Robot Task Allocation (MRTA) strategies with heterogeneous agents.

## What it is

One UAV acts as an aerial observer — it detects targets in the environment and broadcasts their positions. Three ground robots (UGVs) receive assignments and navigate to their targets. The repo is built to compare MRTA strategies (centralized optimization, decentralized auction) in a consistent simulation environment, then stress-test them under comms disruption.

## Scope

- **1 UAV** — static aerial observer; flight dynamics out of scope
- **3 UGVs** — diff-drive ground executors
- **Urban obstacle world** — static barriers, Gazebo Harmonic
- **Allocation strategies** — Hungarian (M3), auction/CBBA (M4), comparison study (M5)
- **Comms disruption** — stress-test layer on top of allocation (M6); pre-existing `comm_layer` package will be re-integrated

## Current status

M3 complete: Hungarian allocation end-to-end. UAV detects targets, allocator solves the assignment problem, UGVs navigate to assigned targets. RViz shows colored path lines per robot. Terminal display prints initial state, cost matrix, assignment result, and arrival confirmations.

## Demo

<!-- M3 demo video — replace with embed or GIF -->

## Stack

- ROS 2 Jazzy · Gazebo Harmonic · Ubuntu 24.04
- Python (ROS nodes) · URDF/Xacro + SDF (robot and world descriptions)

## Packages

| Package | Role |
|---|---|
| `multi_robot_bringup` | Top-level launch, world SDF, RViz config |
| `uav_description` | UAV URDF/Xacro + `robot_state_publisher` launch |
| `ugv_description` | UGV URDF (RViz) + SDF with VelocityControl + OdometryPublisher plugins |
| `uav_observer` | Target detection node — broadcasts discovered targets on `/uav_1/targets` |
| `task_allocator` | Hungarian allocator — solves assignment, publishes to `/allocation/assignments` |
| `ugv_nav` | Goal follower, RViz marker node, demo display node |
| `comm_layer` | Pre-existing comms disruption layer (clean / drop / delay / blackout) — re-integrated at M6 |

## Running it

```bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

### Baseline sim (Gazebo only)

```bash
ros2 launch multi_robot_bringup simulation.launch.py use_rviz:=false
```

### M3 — Hungarian allocation demo

Two terminals:

```bash
# Terminal 1
ros2 launch multi_robot_bringup simulation.launch.py \
  use_rviz:=true use_uav_observer:=true use_allocator:=true

# Terminal 2
ros2 run ugv_nav demo_display_node
```

### Comms disruption layer (pre-existing, not part of active MRTA flow)

```bash
ros2 launch multi_robot_bringup simulation.launch.py \
  use_rviz:=false \
  use_mission_comms:=true \
  use_network_sim:=true \
  network_scenario:=drop
```

Scenarios: `clean`, `drop`, `delay`, `blackout`. Schema and parameters in `ros2_ws/src/comm_layer/`.
