# air-ground-ops

Heterogeneous multi-robot task allocation (MRTA) in a ROS 2 + Gazebo sandbox: one UAV providing aerial observation, multiple UGVs executing ground tasks, with comms disruption as an eventual stress-test layer on top of any allocation scheme.

<!-- TODO: add demo GIF once M2 is working -->

## What this is

A simulation environment for studying MRTA with heterogeneous agents. The goal is to implement and compare MRTA strategies — market-based auctions, optimization methods, and learning-based approaches — in a consistent setting, then stress-test them under comms disruption.

## Scope

- **1 UAV** — aerial observer (static pose; flight dynamics out of scope initially)
- **3 UGVs** — ground executors (diff-drive model)
- **Urban obstacle world** — static barriers and blocks
- **Targets** — distributed in the environment, discovered by the UAV (M2)
- **Allocation strategies** — multiple MRTA families to be compared (M3–M5)
- **Comms disruption** — applied as a stress-test layer on top of allocation (M6)

## Status

Sim bringup complete: ROS 2 / Gazebo workspace with UAV + 1 UGV spawning in the obstacle world, UGV teleop via `cmd_vel`. Scaling to 3 UGVs (M1) is the immediate next step.

A ROS-level communication disruption layer (mission publisher, network simulator, receiver with JSON schema validation; scenarios: clean / drop / delay / blackout) exists in the repo from an earlier iteration of this project and will be re-integrated at M6 as the MRTA stress-test harness.

## Roadmap

Built milestone by milestone. Each milestone closes with checkpoint questions that make the design tradeoffs explicit — useful as a self-check when learning MRTA alongside the code.

- [x] **M0** — Foundation: ROS 2 / Gazebo workspace, UAV + UGV bringup, UGV teleop
- [ ] **M1** — Scale to 3 UGVs with namespaced bringup
- [ ] **M2** — Target placement + UAV target detection and broadcast
- [ ] **M3** — Centralized optimization-based allocation (Hungarian)
- [ ] **M4** — Decentralized market-based allocation (auction)
- [ ] **M5** — Comparison study: solution quality, compute time, scaling
- [ ] **M6** — Allocation under comms disruption (integrate existing `comm_layer`)
- [ ] **M7** — Learning-based allocation (stretch)

## Stack

- ROS 2 Jazzy
- Gazebo Harmonic
- Ubuntu 24.04
- Python (ROS nodes), URDF/Xacro + SDF (robot and world description)

## Packages

- `multi_robot_bringup` — top-level launch, worlds
- `uav_description` — UAV URDF/Xacro + `robot_state_publisher` launch
- `ugv_description` — UGV URDF (for RViz) + SDF with diff-drive plugin (for Gazebo)
- `comm_layer` — pre-existing mission publisher, network simulator, mission receiver (to be re-integrated at M6)

## Running it

Build and source the workspace:

```bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

### Baseline sim

```bash
ros2 launch multi_robot_bringup simulation.launch.py use_rviz:=false
```

### UGV teleop

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/ugv_1/cmd_vel
```

### Pre-existing comms disruption layer

Not part of the active MRTA flow yet, but functional and runnable:

```bash
ros2 launch multi_robot_bringup simulation.launch.py \
  use_rviz:=false \
  use_mission_comms:=true \
  use_network_sim:=true \
  network_scenario:=drop
```

Available scenarios: `clean`, `drop`, `delay`, `blackout`. Mission schema and parameter overrides are in `ros2_ws/src/comm_layer/`.

## Why this project

MRTA is well-studied, but most implementations specialize in one approach. This repo is a learning vehicle and a comparison sandbox: implementing the major MRTA families in one sim — and eventually testing them under realistic comms disruption — makes the tradeoffs concrete rather than theoretical.
