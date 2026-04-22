# CLAUDE.md

Project context for Claude Code working on this repository.

## Project overview

`air-ground-ops` (renamed from `resilient_uav_ugv_autonomy`) is a ROS 2 + Gazebo sandbox for heterogeneous multi-robot task allocation (MRTA). Target configuration: 1 UAV (aerial observer, static pose) + 3 UGVs (ground executors, diff-drive). Built as a comparison sandbox for MRTA strategies — market-based auctions, optimization methods, and learning-based approaches — with an existing comms disruption layer to be used as a stress-test harness at a later milestone.

## Direction change — read this before making changes

This repo was originally focused on resilient UAV-UGV autonomy under comms disruption. The direction has shifted to MRTA. Implications:

- The `comm_layer` package (mission publisher, network simulator, receiver with clean/drop/delay/blackout scenarios) is **pre-existing functional code from the old direction**. Do not rebuild what it already provides. It will be re-integrated at milestone M6 as the MRTA stress-test harness.
- Do not extend the "resilient autonomy" framing in docs, node names, or architecture. New code should align with the MRTA direction.
- UAV flight dynamics are explicitly out of scope initially. The UAV is a static observer spawned in the world SDF.

## Current status

- UAV (static pose in `urban_obstacles.sdf`) and **one** UGV (diff-drive, diff-drive plugin in SDF) spawn and run in Gazebo Harmonic.
- UGV teleop works via `ros_gz_bridge` mapping `/ugv_1/cmd_vel` to `/model/ugv_1/cmd_vel`.
- Odometry is bridged from Gazebo to ROS at `/ugv_1/odom`.
- `comm_layer` runs end-to-end with all four scenarios but is not part of the MRTA workflow yet.

Immediate next milestone: **M1 — scale to 3 UGVs with namespaced bringup.**

## Roadmap

- [x] M0 — Foundation: sim bringup, UAV + UGV, teleop
- [ ] M1 — Scale to 3 UGVs (`ugv_1`, `ugv_2`, `ugv_3`) with namespaced topics
- [ ] M2 — Target placement in world + UAV target detection and broadcast
- [ ] M3 — Centralized optimization-based allocation (Hungarian)
- [ ] M4 — Decentralized market-based allocation (auction)
- [ ] M5 — Comparison study (solution quality, compute time, scaling)
- [ ] M6 — Allocation under comms disruption (integrate existing `comm_layer`)
- [ ] M7 — Learning-based allocation (stretch)

Each milestone closes with checkpoint questions that verify understanding of the design tradeoffs. When finishing a milestone, propose a short set of such questions in the relevant doc.

## Workspace layout

```
ros2_ws/src/
├── multi_robot_bringup/       # top-level launch, worlds
│   ├── launch/simulation.launch.py
│   └── worlds/urban_obstacles.sdf
├── uav_description/           # UAV URDF/Xacro + launch (robot_state_publisher)
├── ugv_description/           # UGV URDF (RViz) + SDF with diff-drive plugin (Gazebo)
└── comm_layer/                # pre-existing: mission publisher, network simulator, receiver
```

The `docs/` directory is `.gitignore`'d — treat it as a local scratchpad, not a public artifact.

## Build & run

Build from the workspace root:

```bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

Baseline sim (no comms layer):

```bash
ros2 launch multi_robot_bringup simulation.launch.py use_rviz:=false
```

With the pre-existing comms disruption layer (not part of MRTA flow yet):

```bash
ros2 launch multi_robot_bringup simulation.launch.py \
  use_rviz:=false use_mission_comms:=true use_network_sim:=true network_scenario:=drop
```

Scenarios: `clean`, `drop`, `delay`, `blackout`. See `ros2_ws/src/comm_layer/comm_layer/mission_schema.md`.

## Conventions

- **Environment**: ROS 2 Jazzy, Gazebo Harmonic, Ubuntu 24.04.
- **Languages**: Python (`rclpy`) for ROS nodes. Robot descriptions are URDF/Xacro (RViz) and SDF (Gazebo). Keep both in sync when changing geometry or joint layout.
- **Topic namespacing**: per-robot namespace prefix, e.g. `/ugv_1/cmd_vel`, `/ugv_1/odom`. Continue this pattern when adding `ugv_2`, `ugv_3`. UAV topics live under `/uav_1/`.
- **Mission messages**: JSON payload in `std_msgs/msg/String` — schema in `comm_layer/mission_schema.md`. When extending, version the schema explicitly.
- **Launch design**: `simulation.launch.py` uses `IfCondition` toggles (`use_mission_comms`, `use_network_sim`) so optional subsystems can be turned on without changing the default baseline.

## Guardrails

- Do not reintroduce the "resilient autonomy" framing in new code, docs, or commit messages.
- Do not rebuild functionality already in `comm_layer`. If something comms-related is needed, extend `comm_layer` or route through it.
- Do not add UAV flight dynamics without explicit discussion — out of scope initially.
- Keep the repo runnable at every milestone. A broken baseline sim is worse than a slow roadmap.
