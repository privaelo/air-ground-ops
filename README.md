# air-ground-ops

A ROS 2 + Gazebo sandbox for studying and comparing Multi-Robot Task Allocation (MRTA) strategies with heterogeneous agents.

## What it is

One UAV acts as an aerial observer — it detects targets in the environment and broadcasts their positions. Three ground robots (UGVs) receive assignments and navigate to their targets. The repo is built to compare MRTA strategies (centralized optimization, decentralized auction) in a consistent simulation environment, then stress-test them under comms disruption.

## Scope

- **1 UAV** — static aerial observer; flight dynamics out of scope
- **3 UGVs** — diff-drive ground executors
- **Urban obstacle world** — static barriers, Gazebo Harmonic
- **Allocation strategies** — centralized optimization (Hungarian), decentralized auction (CBBA), comparison study

## Current status

Hungarian allocation end-to-end: UAV detects targets, allocator solves the assignment problem, UGVs navigate to their assigned targets. RViz shows colored path lines per robot. Terminal display prints initial state, cost matrix, assignment result, and arrival confirmations.

## Demo
https://github.com/user-attachments/assets/e8433b71-6ec4-4faa-a1e9-a579bd446a06


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
| `comm_layer` | Comms disruption layer (clean / drop / delay / blackout) — not active yet |

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

### Hungarian allocation demo

Two terminals:

```bash
# Terminal 1
ros2 launch multi_robot_bringup simulation.launch.py \
  use_rviz:=true use_uav_observer:=true use_allocator:=true

# Terminal 2
ros2 run ugv_nav demo_display_node
```

