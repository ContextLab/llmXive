# Data Model: Virtual Tactile Zero-Shot Adaptation

## Overview

This document defines the data structures used in the `Virtual Tactile` feature. All data is generated, processed, and stored locally within the project's `data/` directory. No external databases are used.

## Entity Relationships

1.  **NovelObject**: A generated articulated object geometry with specific friction properties.
2.  **SimulationRun**: A single execution of a policy on a NovelObject.
3.  **EstimateLog**: Time-series data of the Virtual Tactile Dynamic Resistance Proxy output during a SimulationRun.
4.  **ExperimentResult**: Aggregated statistics (success rates, p-values) for the entire experiment.

## Data Schema Definitions

### 1. Novel Object Metadata (JSON)
Stored in `data/generated/novel_objects/<object_id>.json`.

| Field | Type | Description |
| :--- | :--- | :--- |
| `object_id` | string | Unique identifier (UUID). |
| `base_geometry` | string | Filename of the base mesh from DragMesh-2. |
| `friction_coefficient` | float | Randomized friction value (0.1 - 2.0). |
| `stiffness_range` | object | `{ "min": float, "max": float }` expected range. |
| `created_at` | string | ISO 8601 timestamp. |

### 2. Simulation Run Log (CSV)
Stored in `data/logs/simulation_run_<run_id>.csv`. One row per timestep.
**Critical Data Flow**: This file contains **RAW** signals. The estimator module reads this file to compute derivatives.

| Column | Type | Description |
| :--- | :--- | :--- |
| `timestep` | int | Simulation step index. |
| `policy_type` | string | `adaptive`, `static`, or `ablation_random`. |
| `object_id` | string | Reference to NovelObject. |
| `torque_hand` | float | Norm of hand joint torque vector (RAW). |
| `velocity_object` | float | Norm of object velocity vector (RAW). |
| `k_est` | float | Estimated Dynamic Resistance Proxy ($|\Delta \tau| / |\Delta v|$). **Computed by estimator module**. |
| `reward_detach` | float | Current detachment reward weight. |
| `reward_contact` | float | Current contact reward weight. |
| `is_success` | int | 1 if goal reached, 0 otherwise (only in final row). |

**Note on Data Flow**: The `torque_hand` and `velocity_object` columns are written by the physics engine *without* any derivative calculation. The `k_est` column is populated by the `virtual_tactile.py` module *after* reading the raw log, applying the moving average filter (window=5), and epsilon clamping. This ensures the estimator logic is tested end-to-end.

### 3. Experiment Summary (JSON)
Stored in `data/logs/experiment_summary.json`.

| Field | Type | Description |
| :--- | :--- | :--- |
| `experiment_id` | string | UUID. |
| `total_objects` | int | Number of novel objects tested. |
| `adaptive_success_rate` | float | Mean success rate of adaptive policy. |
| `static_success_rate` | float | Mean success rate of static policy. |
| `ablation_success_rate` | float | Mean success rate of ablation (random proxy) policy. |
| `improvement_pct` | float | Percentage improvement (Adaptive vs Static). |
| `p_value` | float | Result of GLMM (Fixed effect of Policy Type). |
| `conclusion` | string | `PASS` or `FAIL` based on SC-001/SC-005/SC-006. |

## Data Flow

1.  **Generation**: `articulated_object_gen.py` reads `data/raw/manifest.jsonl`, randomizes friction, and writes `NovelObject` JSONs.
2.  **Simulation**: `drag_mesh_env.py` runs episodes, logging **RAW** `torque_hand` and `velocity_object` to `SimulationRun` CSVs.
3.  **Estimation**: `virtual_tactile.py` reads the raw CSVs, applies the moving average filter (window=5), applies epsilon clamping, computes $k_{est}$, and updates the log. **This step is mandatory; the sweep generator does not pre-calculate derivatives.**
4.  **Analysis**: `statistical_test.py` reads all `SimulationRun` CSVs, aggregates success rates, runs a GLMM, and writes `ExperimentSummary`.

## Constraints & Validations

- **Friction Coefficient**: Must be $> 0.0$ and $< 3.0$.
- **k_est**: Must be finite and positive.
- **Success Rate**: Must be $0.0 \le rate \le 1.0$.
- **File Integrity**: All generated files must be checksummed (SHA-256) and recorded in `state/...yaml`.