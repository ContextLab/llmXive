# Data Model: llmXive follow-up: extending “From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent”

## Overview
Defines the JSON and CSV structures used throughout the experiment. All files are validated against the schemas in `contracts/`.

## Entities

### 1. Task (`data/raw/tasks.json`)

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string (UUID) | Unique identifier. |
| `description` | string | Natural‑language description of the task. |
| `complexity` | integer (3‑5) | Number of steps in the solution path. |
| `ground_truth_skills` | list[string] | IDs of the skills that must be executed (3‑5 items). |
| `solution_path` | list[string] | Ordered list of function calls representing the deterministic solution. |

### 2. Skill (`data/raw/skills.json`)

| Field | Type | Description |
|-------|------|-------------|
| `skill_id` | string (UUID) | Unique identifier for the skill. |
| `name` | string | Function name. |
| `code` | string | Full Python source code of the skill. |
| `embedding` | list[float] (dimensionality of the model’s output) | Semantic vector from `all‑MiniLM‑L6‑v2`. |
| `usage_count` | integer ≥ 0 | Times the skill has been retrieved/executed. |
| `last_used` | string (ISO‑8601) | Timestamp of most recent use. |

### 3. Experiment Log (`data/results/metrics.csv`)

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | string | Identifier for the experiment configuration (library size, overlap, pruning flag). |
| `task_id` | string | Reference to the task. |
| `library_size` | integer (10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 100) | Active skill library size at execution time. |
| `pruning_enabled` | boolean | Whether the pruning heuristic was active. |
| `success` | boolean | **Exact‑match success** (True if executed solution matches ground truth). |
| `latency_ms` | number | Execution latency in milliseconds. |
| `tokens_used` | integer | Estimated token count for the simulated LLM call. |
| `retrieval_precision` | number ∈ [0, 1] | Jaccard similarity between top‑k (k=5) retrieved skills and ground‑truth skill set. |
| `retrieval_diversity` | number | Inverse of the variance of cosine similarities of the top‑k retrieved skills to the ground‑truth set (higher = more diverse). |
| `edge_case` | string | Tag for edge cases (`"missing_skill"`, `"memory_limit"`, `"max_overlap"`, `"null"`). |

*Note*: Overlap level is encoded in `run_id`; it does not vary per row.

### 4. Analysis Report (`data/results/analysis_report.json`)

| Field | Type | Description |
|-------|------|-------------|
| `breakpoint_estimate` | number | Library size where the success‑rate slope changes (primary tipping point). |
| `breakpoint_ci` | list[number] (2 items) | 95 % confidence interval for the breakpoint. |
| `vif_library_size` | number | VIF for the “library‑size” predictor (raw, not orthogonalized). |
| `vif_total_redundancy` | number | VIF for the “total‑redundancy” predictor (raw). |
| `vif_overlap_level` | number | VIF for the overlap categorical predictor (treated via dummy coding). |
| `vif_pruning_enabled` | number | VIF for the pruning flag. |
| `pruning_direct_pvalue` | number | p‑value for the direct effect of pruning on success. |
| `pruning_direct_effect_size` | number | Effect size (Cohen’s d) for the direct pruning effect. |
| `pruning_mediation_pvalue` | number | p‑value for the mediation effect of pruning via redundancy change. |
| `pruning_mediation_effect_size` | number | Effect size for the mediation pathway. |
| `likelihood_ratio_pvalue` | number | p‑value from the likelihood‑ratio test of breakpoint vs. no‑breakpoint model. |
| `power_analysis` | object | Details of the a‑priori power calculation (sample size, effect size, achieved power). |
| `runtime_seconds` | number | Total wall‑clock time of the experiment (from Phase 6). |
| `sensitivity_analysis` (optional) | object | Results from dense‑grid and overlap‑sweep experiments (supplemental). |

## Data Flow
1. **Generation** – `generate_data.py` creates `tasks.json`, `skills.json`, computes embeddings, enforces overlap thresholds, writes SHA‑256 of both files to `data/checksums.json`. If RAM > 6 GB, aborts with “Memory Limit Exceeded”. |
2. **Checksum Verification** – `write_checksums.py` recomputes hashes and asserts equality; unit test `test_write_checksums.py` validates. |
3. **Contract Validation** – `pytest tests/contract/test_schemas.py` validates raw JSON against `task.schema.yaml` / `skill.schema.yaml`. |
4. **Execution** – `agent.py` reads raw files, runs the factorial experiment (independent per‑condition sampling), logs each task to `metrics.csv` via `logging_config.py`. |
5. **Execution‑Log Validation** – `pytest tests/contract/test_logging_schema.py` validates `metrics.csv` and JSON‑L logs against `execution_log.schema.yaml`. |
6. **Analysis** – `analysis.py` reads `metrics.csv`, fits the piecewise logistic model, computes VIF on raw predictors, runs bootstrap CI, likelihood‑ratio test, and evaluates pruning (direct + mediation). Writes `analysis_report.json`. |
7. **Report Validation** – `pytest tests/contract/test_schemas.py` validates `analysis_report.json`. |
8. **Checksum Update** – After each successful phase, the new file’s SHA‑256 is appended to `data/checksums.json`. |

## Constraints
- **Immutability** – `tasks.json` & `skills.json` are read‑only after generation. |
- **Append‑Only Log** – `metrics.csv` is only appended; no in‑place edits. |
- **Schema Validation** – Every read/write step validates against its schema; failures abort the CI run. |

---

