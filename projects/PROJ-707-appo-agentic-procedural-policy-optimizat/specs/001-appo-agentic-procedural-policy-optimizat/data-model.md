# Data Model: APPO: Agentic Procedural Policy Optimization

## 1. Entities & Relationships

### TrainingRun
Represents a single execution of the RL agent.
- **Attributes**:
  - `run_id`: UUID (unique identifier).
  - `config_id`: String (e.g., "baseline", "default", "ablation_001").
  - `seed`: Integer.
  - `model_name`: String (e.g., "llama-3.1-8b-q4_k_m").
  - `model_hash`: String (SHA256 of the GGUF file for reproducibility).
  - `benchmark`: String ("MATH").
 - `max_steps`: Integer (hard limit, [deferred]).
  - `steps_executed`: Integer (actual steps).
  - `final_success_rate`: Float (0.0 - 1.0).
  - `steps_to_threshold`: Float or String ("Censored" if not reached).
  - `timestamp`: ISO8601.

### BranchingScore (Transient)
Computed at each token step. **Note**: This entity is **transient** and not persisted to disk as a separate file. Its values are aggregated into the `TrainingRun` metrics (e.g., mean Branching Score) or logged in the step-wise CSV if debugging is enabled.
- **Attributes**:
  - `step_index`: Integer.
  - `token_entropy`: Float.
  - `future_value_estimate`: Float.
  - `branching_score_value`: Float.
  - `reward`: Float.

### BenchmarkLog
Per-episode log for a run.
- **Attributes**:
  - `episode_id`: Integer.
  - `success`: Boolean.
  - `tool_calls_count`: Integer.
  - `steps_in_episode`: Integer.
  - `final_score`: Float.

## 2. File Formats

### CSV: `results/training_logs.csv`
Aggregated logs from all seeds.
- Columns: `run_id`, `config_id`, `seed`, `benchmark`, `steps_to_threshold`, `final_success_rate`, `mean_tool_calls`, `collinearity_r`, `model_hash`.

### CSV: `results/ablation_summary.csv`
Summary of ablation grid.
- Columns: `config_id`, `epsilon`, `epsilon_prime`, `b`, `mean_steps_to_threshold`, `std_steps_to_threshold`, `variance_check` (boolean: <15%).

### JSON: `data/checkpoints/run_<run_id>_metrics.json`
Intermediate metrics (optional, for debugging).

### Log: `results/warnings.log`
Specific warnings, including collinearity flags (|r| ≥ 0.9).

## 3. Data Flow

1.  **Download**: Datasets fetched from HF and cached in `data/raw/`.
2.  **Preprocess**: `environments.py` wraps datasets into RL environments (Synthetic).
3.  **Train**: `cli/train.py` executes loop, logging to `results/training_logs.csv`.
4.  **Aggregate**: `app/stats.py` reads CSVs, computes KM curves, checks variance, generates `results/summary.csv`.
5.  **Report**: Final report generated from `results/summary.csv`.