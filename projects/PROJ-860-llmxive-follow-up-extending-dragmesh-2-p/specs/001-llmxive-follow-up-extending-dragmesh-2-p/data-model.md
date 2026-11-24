# Data Model: Virtual Tactile Zero-Shot Adaptation

## Overview
All artifacts reside under `data/`. No external databases are used. Files are immutable; derived files receive new filenames and checksums.

## Schemas

### 1. Novel Object Manifest (`data/generated/novel_objects/<object_id>.json`)
| Field | Type | Constraints |
|---|---|---|
| `object_id` | string | UUID, unique |
| `base_mesh_source` | string | Path to original DragMesh‑2 mesh |
| `friction_coefficient` | number | ≥ 0.0, ≤ 2.0 |
| `object_mass` | number | ≥ 0.1, ≤ 5.0 (kg) |
| `geometry_params` | object | `{ "scale": number, "rotation": [number, number, number], "articulation_links": [{…}] }` |
| `created_at` | string | ISO 8601 timestamp |

### 2. Simulation Run Log (`data/logs/simulation_run_<run_id>.csv`)
One row per timestep (raw signals). The estimator populates `k_est` later.

| Column | Type | Description |
|---|---|---|
| `timestep` | int | Simulation step index |
| `policy_type` | string | `static`, `adaptive`, or `ablation_random` |
| `object_id` | string | Links to Novel Object Manifest |
| `torque_hand` | float | Norm of hand joint torque vector (RAW) |
| `velocity_object` | float | Norm of object velocity vector (RAW) |
| `normal_force` | float | Estimated normal contact force `N` |
| `k_est` | float | Dynamic Resistance Proxy (filled by estimator) |
| `reward_detach` | float | Current detachment reward weight |
| `reward_contact` | float | Current contact reward weight |
| `is_success` | int | 1 if goal reached (final row only), else 0 |

**Data Flow Guarantee**: `torque_hand` and `velocity_object` are logged *without* derivatives; `k_est` is computed exclusively by `virtual_tactile.py`.

### 3. Experiment Summary (`data/logs/experiment_summary.json`)
| Field | Type | Description |
|---|---|---|
| `experiment_id` | string | UUID |
| `total_objects` | int | Number of novel objects (should be a sufficient quantity to ensure adequate diversity) |
| `adaptive_success_rate` | number | Mean success (0‑1) |
| `static_success_rate` | number | Mean success (0‑1) |
| `ablation_success_rate` | number | Mean success (0‑1) |
| `improvement_pct` | number | `(adaptive - static) * 100` |
| `p_value` | number | GLMM fixed‑effect p‑value |
| `correlation_r` | number | Pearson r from validation experiment |
| `conclusion` | string | `"PASS"` if all SCs met, else `"FAIL"` |
| `timestamp` | string | ISO 8601 |

## Constraints & Validations
- **Friction Coefficient**: Must be > 0.0 and ≤ 2.0.  
- **k_est**: Finite, positive, within `[1e‑4, 10]`.  
- **Success Rate**: 0 ≤ rate ≤ 1.  
- **File Integrity**: SHA‑256 checksum recorded in `state/...yaml`.  

---
