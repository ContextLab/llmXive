# Data Model: llmXive Follow-up: Dynamic Socio-Cognitive State Injection

## 1. Overview
This document defines the data structures, schemas, and relationships for the `001-dynamic-state-injection` feature. All data artifacts are stored in `data/` and validated against schemas in `contracts/`.

## 2. Core Entities

### 2.1 ConflictTrajectory
Represents a single dialogue instance with metadata.
- **Source**: `data/processed/filtered_trajectories.jsonl` (Derived from SoCRATES prompts).
- **Derivation**: Filtered and oversampled for high-emotion/cultural diversity.
- **Storage**: `data/processed/filtered_trajectories.jsonl`

**Fields**:
- `trajectory_id` (string): Unique identifier.
- `dialogue_history` (list of strings): Turn-by-turn conversation.
- `emotional_reactivity_score` (float): 0.0 - 1.0 (Generated metadata).
- `cultural_identity_tags` (list of strings): e.g., ["high-context", "collectivist"].
- `ideal_resolution` (string): Ground truth summary of the ideal outcome.

### 2.2 SocioCognitiveState
Inferred state label and confidence.
- **Source**: Output of `state_classifier.py` (FR-002).
- **Storage**: Embedded in `experiment_log.schema.yaml` or separate `data/processed/classifier_outputs.jsonl`.

**Fields**:
- `state_label` (string): e.g., "escalating", "cultural-friction", "neutral-monitoring".
- `confidence` (float): 0.0 - 1.0.
- `injection_instruction` (string): The dynamic prompt text derived from the state.

### 2.3 ExperimentLog
Record of a single LLM inference run.
- **Source**: `experiments/runner.py` (FR-003, FR-004).
- **Storage**: `data/results/experiment_logs/{model_name}/{condition}.jsonl`.

**Fields**:
- `run_id` (string): UUID.
- `trajectory_id` (string): FK to ConflictTrajectory.
- `model_name` (string): e.g., "llama-3-8b".
- `condition` (string): "static" or "adapter".
- `injected_state` (string): The state label used (or "none" for static).
- `llm_output` (string): Generated resolution.
- `consensus_gap_score` (float): Result of FR-005.
- `status` (string): "success", "skipped", "timeout".

### 2.4 StatisticalReport
Aggregated results.
- **Source**: `analysis/report_generator.py` (FR-006, FR-007).
- **Storage**: `data/results/statistical_report.json`.

**Fields**:
- `model_name` (string).
- `condition_comparison` (object):
  - `n_samples` (int).
  - `mean_gap_adapter` (float).
  - `mean_gap_static` (float).
  - `diff_mean` (float).
  - `test_type` (string): "t-test" or "wilcoxon".
  - `normality_p_value` (float): Shapiro-Wilk p-value.
  - `p_value` (float).
  - `is_significant` (boolean).
  - `effect_size` (float): Cohen's d or r.
- `correction_method` (string): "holm-bonferroni".
- `corrected_p_value` (float).

## 3. Data Flow
1. **Ingest**: SoCRATES Prompts -> Derived Trajectories (FR-001).
2. **Train**: Derived Trajectories -> Classifier Model (FR-002).
3. **Run**: Derived Trajectories + Classifier -> Experiment Logs (FR-003, FR-004).
4. **Evaluate**: Experiment Logs -> Consensus Gap Scores (FR-005).
5. **Analyze**: Consensus Gap Scores -> Statistical Report (FR-006, FR-007).

## 4. Integrity Constraints
- **Uniqueness**: `trajectory_id` must be unique per dataset.
- **Referential Integrity**: `experiment_log.trajectory_id` must exist in `filtered_trajectories`.
- **Range**: `consensus_gap_score` must be in [0.0, 1.0].
- **Checksum**: All raw and derived files must have a recorded SHA-256 hash in `state/...yaml`.