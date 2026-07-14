# Data Model: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Overview

This document defines the data structures used for the synthetic topology-shift test set, the inference logs, and the statistical analysis results. All data is stored in `data/` and processed by scripts in `code/`.

## Entities

### 1. Topology Definition (Metadata)

Describes the kinematic or deformable structure of an object in the test set.

- **`topology_id`**: `str` (UUID) - Unique identifier for the topology.
- **`type`**: `str` - Enum: `"kinematic_chain"`, `"soft_rope"`, `"cloth"`.
- **`parameters`**: `dict` - Configuration specific to the type.
  - *Kinematic*: `{"link_count": int, "joint_type": "hinge"|"slider"}`.
  - *Soft*: `{"mesh_density": int, "stiffness": float}`.
- **`training_overlap`**: `bool` - Always `False` (verified against training set hash).
- **`checksum`**: `str` - SHA-256 of the topology definition.

### 2. Simulation State (Raw Data)

Recorded at each timestep during the simulation for a single trial.

- **`trial_id`**: `str` - Unique identifier for the trial (e.g., `sym_001`, `base_001`).
- **`timestep`**: `int` - Current step index.
- **`topology_id`**: `str` - Reference to the topology.
- **`observation_latent`**: `list[float]` - Latent vector $z_t$ from GFM encoder.
- **`action_physical`**: `list[float]` - 3D action vector executed in PyBullet.
- **`state_physical`**: `dict` - Positions/velocities of all bodies.
  - `positions`: `list[list[float]]` (N vertices/bodies x 3).
  - `velocities`: `list[list[float]]`.
- **`constraint_satisfaction`**: `bool` - Whether rigid/soft constraints were met at this step.
- **`solver_time_ms`**: `float` - Time taken by symbolic solver (0 if baseline).
- **`drift_score`**: `float` - Mahalanobis distance from training distribution (if applicable).

### 3. Trial Result (Aggregated)

Summary of a single 50-trial run (one topology, one method).

- **`trial_id`**: `str`.
- **`method`**: `str` - `"symbolic"` or `"baseline"`.
- **`topology_id`**: `str`.
- **`success`**: `bool` - `True` if target reached (within 5cm for 1.0s).
- **`failure_reason`**: `str` - Enum: `"timeout"`, `"infeasible"`, `"collision"`, `"drift"`, `null`.
- **`total_latency_ms`**: `float` - Sum of inference times for all steps (or `null` if timeout).
- **`steps_executed`**: `int` - Number of timesteps before success/failure.
- **`is_censored`**: `bool` - `True` if the trial was a timeout (for survival analysis).

### 4. Statistical Summary

Output of the analysis script.

- **`metric`**: `str` - `"success_rate"` or `"latency"`.
- **`method_symbolic`**: `float` - Mean/Rate for symbolic.
- **`method_baseline`**: `float` - Mean/Rate for baseline.
- **`p_value`**: `float` - Result of statistical test.
- **`confidence_interval`**: `list[float]` - 95% CI [lower, upper].
- **`effect_size`**: `float` - Cliff's Delta (for latency) or Odds Ratio (for success).
- **`significance`**: `bool` - `True` if p < 0.05.
- **`test_type`**: `str` - `"wilcoxon"` or `"fisher_exact"` or `"kaplan_meier"`.

## File Formats

- **`data/generated/topology_shift_test_set_v1.jsonl`**: JSON Lines format. Each line is a `Topology Definition` + initial state.
- **`data/results/trial_logs.jsonl`**: JSON Lines. Each line is a `Simulation State`.
- **`data/results/trial_results.csv`**: CSV. Each row is a `Trial Result`.
- **`data/results/statistical_report.json`**: JSON. Contains `Statistical Summary`.

## Data Hygiene Rules

1. **Immutability**: Raw generated data in `data/generated/` is never modified. Derivations (e.g., `trial_results.csv`) are written to `data/results/`.
2. **Checksums**: Every file in `data/` must have a corresponding entry in `state/...artifact_hashes` with a SHA-256 hash.
3. **No PII**: No user data or external PII is included. All data is synthetic.
4. **Versioning**: Filenames include version suffix (e.g., `_v1`) to track changes in generation logic.