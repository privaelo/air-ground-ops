# Mission Schema v1

Transport: `std_msgs/msg/String`
Encoding: JSON in `String.data`

Example:

```json
{
  "msg_type": "mission_directive",
  "mission_id": "mission-42",
  "target_xy": {"x": 10.0, "y": -4.0},
  "priority": 1,
  "timestamp_sec": 1735689600.0
}
```

Required fields:
- `msg_type`: must be `mission_directive`
- `mission_id`: string
- `target_xy`: object with numeric `x`, `y`
- `priority`: integer
- `timestamp_sec`: float/int seconds
