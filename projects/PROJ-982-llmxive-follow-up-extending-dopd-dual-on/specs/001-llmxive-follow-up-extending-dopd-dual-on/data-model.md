# Data Model: llmXive follow-up: extending "DOPD: Dual On-policy Distillation"

## Overview
Defines the schema for synthetic MDP logs, per‑step training logs, aggregated experiment results, and the final statistical summary. All data are generated during execution; no external datasets are ingested.

## Entity Definitions

### 1. MDP Transition Record
| Field | Type | Description |
|-------|------|-------------|
| `state_id` | integer | Unique identifier for the step within an episode. |
| `seed` | integer | Random seed for the episode. |
| `full_state_vector` | array[integer] | Complete grid encoding (Teacher view). |
| `student_observation` | array[integer] | Observable grid only (Student view). |
| `privileged_variable` | integer \| string | Hidden variable `H`. |
| `action_space` | integer | Size of the action space (multiple discrete actions). |
| `reward` | number | Immediate reward. |
| `next_state_vector` | array[integer] | Grid after action. |
| `transition_function` | string | Description of the action taken. |
| `teacher_action` | integer | Optimal action given full state. |
| `student_action` | integer | Action taken by the Student. |
| `teacher_advantage_gap` | number | Advantage gap used for λ. |
| `distillation_weight` | number | Weight λ passed to the Student. |

### 2. Training Log Entry (JSON‑Lines)
| Field | Type | Description |
|-------|------|-------------|
| `seed` | integer | Random seed for the run. |
| `regime` | enum(`uniform`,`dopd`,`randomized_weight`) | Training regime. |
| `step` | integer | Training step index. |
| `episode` | integer | Episode index (required for reproducibility). |
| `loss` | number | Distillation loss value. |
| `entropy` | number | Policy entropy at this step. |
| `expected_advantage_gap` | number \| null | Noisy signal value (expected advantage marginalized over H). Null for Uniform regime. |
| `reward` | number | Cumulative reward for the episode. |

### 3. Experiment Result (Per Seed)
| Field | Type | Description |
|-------|------|-------------|
| `seed` | integer | Seed identifier. |
| `regime` | enum(`uniform`,`dopd`,`randomized_weight`) | Regime used. |
| `accuracy_unmasked` | number (0‑1) | Accuracy when `H` is available. |
| `accuracy_masked` | number (0‑1) | Accuracy when `H` is removed. |
| `performance_drop` | number | Normalized drop in accuracy. |
| `convergence_steps` | integer | Steps until policy stabilizes. |
| `mean_entropy` | number | Average entropy during training. |

## File Formats

| Location | Format | Content |
|----------|--------|---------|
| `data/raw/transitions_seed_{seed}.jsonl` | JSON‑Lines | `MDP Transition Record` for each step. |
| `data/raw/training_log.jsonl` | JSON‑Lines | `Training Log Entry` (created by `TrainingLogger`). |
| `data/processed/results_{regime}.csv` | CSV | Columns: `seed,regime,accuracy_unmasked,accuracy_masked,performance_drop,convergence_steps,mean_entropy`. |
| `data/processed/statistical_summary.json` | JSON | Conforms to `contracts/statistical-summary.schema.yaml`. |

## Constraints
- **Grid Size**: ≤ 10×10 (enforced in `PrivilegedGridEnv`).  
- **Seeds**: Training 0‑49, Evaluation 50‑99, Baseline 1000‑1099 – all distinct.  
- **Immutability**: Raw JSON‑Lines files are never modified after creation; analysis reads only.  

---

