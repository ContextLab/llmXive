# Data Model: llmXive Follow-up: Dynamic Socio-Cognitive State Injection

## 1. Overview
Defines all persistent artifacts produced or consumed by the pipeline. Each artifact is validated against a JSON‑Schema in `contracts/`.

## 2. Core Entities

### 2.1 ConflictTrajectory
- **Source**: `data/processed/filtered_trajectories.jsonl` (generated, FR‑001).  
- **Schema**: `contracts/dataset.schema.yaml`.  

| Field | Type | Description |
|-------|------|-------------|
| `trajectory_id` | string (UUID) | Unique identifier. |
| `dialogue_history` | list[string] | Turn‑by‑turn text. |
| `emotional_reactivity_score` | number (0‑1) | Generated intensity metric. |
| `cultural_identity_tags` | list[string] | Cultural tags (e.g., “high‑context”). |
| `ideal_resolution` | string | Ground‑truth ideal resolution text for the consensus‑gap evaluator. |

### 2.2 ClassifierTrainingSet
- **Source**: `data/processed/classifier_training_set.jsonl` ([deferred] of generated trajectories, used exclusively for LR training).
- **Schema**: Same as `dataset.schema.yaml` (no additional fields).

### 2.3 SocioCognitiveState (embedded in logs)
- **Source**: Output of `state_classifier.py`.  
- **Fields** (stored inside `experiment_log`): `state_label`, `confidence`, `injection_instruction`.

### 2.4 ExperimentLog
- **Source**: `src/experiments/runner.py`.  
- **Schema**: `contracts/experiment_log.schema.yaml`.  

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string (UUID) | Unique run identifier. |
| `trajectory_id` | string | FK → ConflictTrajectory. |
| `model_name` | string | LLM identifier. |
| `condition` | enum(`static`, `adapter`) | Experimental condition. |
| `injected_state` | string | State label injected (or `neutral-monitoring`). |
| `llm_output` | string | Generated resolution text. |
| `consensus_gap_score` | number (0‑1) | Gap metric (0 = perfect, 1 = worst). |
| `status` | enum(`success`, `skipped`, `timeout`) | Execution outcome. |
| `timestamp` | ISO‑8601 datetime | Run timestamp. |
| `inference_time_ms` | integer | Milliseconds spent in inference (also in `metrics`). |

### 2.5 StatisticalReport
- **Source**: `src/analysis/report_generator.py`.  
- **Schema**: `contracts/report.schema.yaml`.  

| Field | Type | Description |
|-------|------|-------------|
| `llm_id` | string | Model name. |
| `comparison` | object | Contains `mean_diff`, `p_value`, `is_significant`, `effect_size`, `test_type`, `normality_p_value`. |
| `correction_applied` | boolean | Whether Holm‑Bonferroni was used across models. |

## 3. Auxiliary Artifacts
- `data/results/oversampling_report.json` – verifies FR‑001.  
- `data/results/feature_independence_audit.json` – audits FR‑002 feature separation.  
- `data/results/evaluator_independence_audit.json` – audits FR‑005 independence.  
- `data/results/scope_adjustments.json` – records any models excluded due to RAM/GPU constraints (T027).  
- `data/results/throughput_report.json` – results of T051.  
- `data/results/threshold_sensitivity_report.json` – results of T050.  

## 4. Data Flow
1. **Ingest** SoCRATES prompts → **Generate** trajectories (FR‑001).  
2. **Split** trajectories into `classifier_training_set.jsonl` (training) and `filtered_trajectories.jsonl` (experiment) (Task T018).  
3. **Train** classifier on the training split (FR‑002).  
4. **Run** experiments (FR‑003‑FR‑004) → produce `ExperimentLog`.  
5. **Evaluate** each output → store `consensus_gap_score` in the same log.  
6. **Analyze** paired differences → generate `StatisticalReport`.  

## 5. Integrity Constraints
- `trajectory_id` uniqueness across `data/processed/`.  
- Referential integrity: every `experiment_log.trajectory_id` must exist in `filtered_trajectories.jsonl`.  
- `consensus_gap_score` ∈ [0.0, 1.0].  
- All raw and derived files have SHA‑256 checksums recorded in `state/...yaml`.  

---

