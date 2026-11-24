# Data Model: llmXive follow‑up: extending "Self‑Distilled Agentic Reinforcement Learning"

## Overview
Defines the structured artifacts produced during training, gating, and analysis. All files are stored in `data/processed/` using JSONL (step‑level) or Parquet (episode‑level) for efficient streaming.

## Entities

### 1. TrainingRun
| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string (UUID) | Unique identifier for the run. |
| `variant` | string (`"grpo"`, `"baseline"`, `"student-only"`) | Variant executed. |
| `environment` | string (`"alfworld"`, `"webshop"`) | Environment name. |
| `seed` | integer | Random seed used. |
| `start_time` | string (ISO‑8601) | Run start timestamp. |
| `end_time` | string (ISO‑8601) | Run end timestamp. |
| `total_steps` | integer | Number of training steps executed. |
| `final_success_rate` | number ∈ [0, 1] | Mean task success over the run. |
| `avg_cpu_time_per_step` | number (seconds) | Mean CPU time per step. |
| `peak_memory_mb` | number | Peak RSS memory in MB. |
| `convergence_steps` | integer or null | Steps to reach reward ≥ 0.8; null if not reached. |
| `early_stopped` | boolean | True if terminated early (threshold or cap). |

### 2. GatingSignal
| Field | Type | Description |
|-------|------|-------------|
| `step_id` | integer | Training step index. |
| `token_id` | integer | Token position in the generated sequence. |
| `token_text` | string | Literal token string. |
| `entropy` | number | Token entropy \(H_t\). |
| `stability` | number | Context stability \(S_t\). |
| `final_gate` | number ∈ [0, 1] | Gated score \(g_t\). |
| `is_valid` | boolean | False if NaN/Inf detected. |
| `paired_trajectory_id` | string (UUID) or null | Links to baseline trajectory for correlation analysis. |

### 3. EpisodeMetrics
| Field | Type | Description |
|-------|------|-------------|
| `episode_id` | integer | Episode identifier. |
| `cumulative_reward` | number | Sum of rewards in the episode. |
| `success` | boolean | 1 if goal reached, else 0. |
| `steps` | integer | Number of timesteps in the episode. |
| `avg_gate` | number | Mean \(g_t\) across the episode. |
| `avg_entropy` | number | Mean \(H_t\) across the episode. |
| `avg_stability` | number | Mean \(S_t\) across the episode. |
| `trajectory_id` | string (UUID) | Unique ID for the full trajectory (used for pairing). |

### 4. ComparisonReport
| Field | Type | Description |
|-------|------|-------------|
| `variant_grpo` | list[number] | Cumulative rewards (all episodes). |
| `variant_baseline` | list[number] | Cumulative rewards (all episodes). |
| `variant_student_only` | list[number] | Cumulative rewards (all episodes). |
| `p_value` | number | Result of the bootstrapped hypothesis test (α = 0.05). |
| `effect_size` | number | Cohen’s d for performance difference. |
| `cost_reduction_pct` | number | % reduction in avg CPU time per step (Student‑Only vs. Baseline). |
| `performance_retention_pct` | number | % of baseline improvement over GRPO retained by Student‑Only, per the gain‑retention formula \((\text{Success}_{\text{Student}} - \text{Success}_{\text{GRPO}}) / (\text{Success}_{\text{Baseline}} - \text{Success}_{\text{GRPO}})\). |
| `correlation_coefficient` | number | Pearson r between student‑only gate and teacher‑student gap (paired trajectories). |

## Data Flow
1. **Input**: Configuration JSON + environment state.
2. **Processing**:
   * `student_only_agent.py` computes `H_t`, `S_t`, `g_t`.
   * `cost_profiler.py` records CPU time & RSS.
   * Metrics are streamed to `data/processed/<run_id>.jsonl`.
   * Baseline trajectories are saved for paired replay.
3. **Output**:
   * `data/processed/summary.json` (ComparisonReport).
   * `data/processed/correlation_analysis.csv` (Pearson r data).
   * `data/processed/episode_metrics.parquet` (used by bootstrapping in Phase 4).

## Data Hygiene
* **Checksums**: SHA‑256 stored in `state/projects/PROJ-825-...yaml` for every file under `data/processed/`.
* **Immutability**: Raw logs never overwritten; derived files receive new filenames with timestamps.
* **PII**: No personally identifying information; token text originates from synthetic environments only.

## Alignment with Plan
* **EpisodeMetrics** are explicitly used in Phase 4 for bootstrapping the performance analysis.
* **ComparisonReport** is generated in Phase 4 and persisted as `data/processed/comparison_report.json`, satisfying the reporting requirements of SC‑001 – SC‑005.

---