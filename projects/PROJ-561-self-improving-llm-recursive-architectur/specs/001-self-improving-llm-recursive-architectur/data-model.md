# Data Model: Self-improving LLM: recursive architecture refinement and re‑training

## 1. Overview

This document defines the data structures used to track the state of the recursive refinement pipeline. All data is persisted to `results/` and `data/` directories. The model ensures that every artifact can be traced back to a specific cycle and configuration.

## 2. Core Entities

### 2.1 ModelCheckpoint
Represents the state of the model at the end of a cycle.
- `cycle_number`: int
- `parameter_count`: int (total parameters after modification)
- `architecture_modification`: str (description of the change)
- `training_time`: float (seconds)
- `flops`: float (total FLOPs consumed during training)
- `model_path`: str (relative path to saved weights)
- `training_subset_size`: int (number of samples used, e.g., 10000 or 1000)

### 2.2 PerformanceMetric
Represents the evaluation results for a specific benchmark.
- `cycle_number`: int
- `benchmark_name`: str (`GSM8K`, `ARC-Challenge`, `BoolQ`)
- `accuracy_or_ECE`: float (accuracy for GSM8K/ARC, ECE for BoolQ)
- `p_value_vs_predecessor`: float (or null for Cycle 0)
- `confidence_interval_lower`: float
- `confidence_interval_upper`: float
- `effect_size_cohen_d`: float (added for low-power analysis)
- `samples_evaluated`: int (100 for GSM8K/ARC, 1000 for BoolQ)

### 2.3 RefinementCycle
Aggregates all data for a single iteration.
- `cycle_number`: int
- `pre_modification_params`: int
- `post_modification_params`: int
- `training_duration`: float
- `evaluation_results`: list of `PerformanceMetric`
- `success_status`: bool (True if training completed, False if failed after retries)
- `modification_rejected`: bool (if oracle rejected the proposal)
- `is_control_cycle`: bool (True if this was a random modification control)

### 2.4 TrajectorySummary
Aggregated results for the entire experiment.
- `cycles_completed`: int
- `baseline_metrics`: dict (Cycle 0 metrics)
- `trajectory_data`: list of `RefinementCycle`
- `linear_regression`: dict (`slope`, `intercept`, `r_squared`, `trend_direction`)
- `trade_off_metrics`: list of dict (`cycle`, `perf_per_flop`, `perf_per_hour`)
- `capacity_analysis`: dict (`correlation_params_perf`, `control_cycle_result`)

## 3. Data Flow

1. **Input**: `config.py` (hyperparameters), `data/raw/*` (datasets).
2. **Process**:
   - `pipeline/trainer.py` generates `ModelCheckpoint` data.
   - `pipeline/evaluator.py` generates `PerformanceMetric` data.
   - `pipeline/trajectory.py` aggregates into `TrajectorySummary`.
3. **Output**:
   - `results/logs/cycle_N.log` (JSON log per cycle).
   - `results/trajectory.json` (final summary).
   - `data/processed/cycle_N_checkpoint.pt` (model weights).

## 4. Constraints & Validation

- **Parameter Count**: `post_modification_params` must be ≤ 1.3 * `baseline_params` (FR-003).
- **Distinctness**: `architecture_modification` must differ from previous cycles by Hamming distance ≥ 1 or >5% parameter change (FR-002).
- **Precision**: All floating point metrics stored with ≥3 decimal places.
- **Uniqueness**: Each `cycle_number` is unique within a run.
- **Sample Sizes**: `samples_evaluated` must match the plan (100 for GSM8K/ARC, 1000 for BoolQ).