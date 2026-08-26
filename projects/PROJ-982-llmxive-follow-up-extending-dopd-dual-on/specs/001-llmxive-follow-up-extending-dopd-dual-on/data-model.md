# Data Model: 001-dopd-discrete-mdp

## 1. Overview

This document defines the data structures used for simulation, training, and analysis. All data is stored in `data/` directory. Raw logs are JSON/CSV; processed metrics are Parquet.

## 2. Entity Definitions

### 2.1 Simulation Trajectory (Raw)
A single step in the MDP environment.

- **`state_id`**: Integer. Unique identifier for the step within an episode.
- **`full_state`**: String (serialized). The complete state `(O, H)`.
- **`student_observation`**: String (serialized). The projection `O` only.
- **`teacher_observation`**: String (serialized). Same as `full_state`.
- **`privileged_variable`**: String/Int. The specific hidden variable `H`.
- **`action`**: Integer. Action taken (0-3 for grid movement).
- **`reward`**: Float. Immediate reward.
- **`next_state`**: String (serialized). Resulting state.
- **`done`**: Boolean. Episode termination flag.
- **`seed`**: Integer. Random seed for the episode.
- **`regime`**: String. "uniform" or "dopd".
- **`teacher_advantage`**: Float. Calculated advantage gap for DOPD.
- **`distillation_weight`**: Float. Weight `w` used in DOPD (1.0 for Uniform).

### 2.2 Training Log (Processed)
Aggregated metrics per episode/seed.

- **`seed`**: Integer.
- **`regime`**: String.
- **`final_q_table_size`**: Integer.
- **`convergence_step`**: Integer. Step where policy stabilized.
- **`action_entropy_mean`**: Float. Average entropy during training.
- **`accuracy_unmasked`**: Float. Accuracy on test set with `H` visible (if applicable).
- **`accuracy_masked`**: Float. Accuracy on test set with `H` hidden.
- **`drop`**: Float. `(accuracy_unmasked - accuracy_masked) / R_max`.

### 2.3 Statistical Results
Final analysis output.

- **`regime_uniform_mean_drop`**: Float.
- **`regime_dopd_mean_drop`**: Float.
- **`p_value`**: Float. Result of Mann-Whitney U test.
- **`effect_size`**: Float. (e.g., Cohen's d or rank-biserial correlation).
- **`is_significant`**: Boolean. `p_value < 0.05`.
- **`conclusion`**: String. "DOPD mitigates illusion" or "Exploratory/No Effect".

## 3. File Formats

- **Raw Logs**: `data/raw/{seed}_{regime}.csv` (One row per step).
- **Aggregated Logs**: `data/processed/training_summary.parquet`.
- **Statistical Report**: `data/processed/stats_report.json`.

## 4. Constraints

- **Grid Size**: Max 5x5 (enforced in `env/privilege_mdp.py`).
- **Seeds**: Must be integers in range [0, 2^32-1].
- **Precision**: Floats stored as `float64`.
