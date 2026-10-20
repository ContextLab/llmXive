# Data Model: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

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
| `skill_id` | string (UUID) | Unique identifier. |
| `name` | string | Function name. |
| `code` | string | Full Python source code of the skill. |
| `embedding` | list[float] (384 items) | High‑dimensional semantic vector (output of `all-MiniLM-L6-v2`). |
| `usage_count` | integer ≥ 0 | Times the skill has been retrieved/executed. |
| `last_used` | string (ISO‑8601) | Timestamp of most recent use. |

### 3. Experiment Log (`data/results/metrics.csv`)

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | string | Identifier for the experiment configuration (library size, overlap, pruning flag). |
| `task_id` | string | Reference to the task. |
| `library_size` | integer (10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 100) | Active skill library size at execution time. |
| `pruning_enabled` | boolean | Whether the pruning heuristic was active. |
| `success` | boolean | Composite success metric (see research.md). |
| `latency_ms` | number | Execution latency in milliseconds. |
| `tokens_used` | integer | Estimated token count for the simulated LLM call. |
| `retrieval_precision` | number ∈ [0, 1] | Jaccard similarity between the set of top‑5 retrieved skills and the ground‑truth skill set. |
| `retrieval_diversity` | number | Inverse of the variance of the cosine similarities of the top‑5 retrieved skills to the ground‑truth set (higher = more diverse). |
| `edge_case` | string | Tag for special conditions (`"missing_skill"`, `"memory_limit"`, `"max_overlap"`, `"null"`). |

*Note*: The CSV does **not** include an `overlap_level` column; overlap is a global experimental factor recorded elsewhere (e.g., in run identifiers) and does not vary per‑row.

### 4. Analysis Report (`data/results/analysis_report.json`)

| Field | Type | Description |
|-------|------|-------------|
| `breakpoint_estimate` | number | Library size where success‑rate slope changes (primary tipping point). |
| `breakpoint_ci` | list[number] (2 items) | 95 % confidence interval for the breakpoint. |
| `vif_library_size` | number | VIF for the “library‑size” predictor after orthogonalization. |
| `vif_total_redundancy` | number | VIF for the “total‑redundancy” predictor after orthogonalization. |
| `pruning_effect_pvalue` | number | p‑value from the ANCOVA test comparing pruning vs. baseline. |
| `pruning_effect_size` | number | Effect size (Cohen’s d) for pruning vs. baseline. |
| `permutation_pvalue` | number | p‑value from the permutation validation of the breakpoint. |
| `likelihood_ratio_pvalue` | number | p‑value from the likelihood‑ratio test of breakpoint vs. no‑breakpoint model. |
| `sensitivity_analysis` (optional) | object | Results from dense‑grid and overlap‑sweep experiments (supplemental). |

## Data Flow
1. **Generation** – `generate_data.py` creates `tasks.json` & `skills.json`, computes SHA‑256 checksums, writes `checksums.json`.  
2. **Validation** – Contract tests (`pytest tests/contract/`) validate JSON files against `task.schema.yaml` & `skill.schema.yaml`.  
3. **Execution** – `agent.py` reads the raw files, runs the experiment loop, appends rows to `metrics.csv` using `logging_config.py`.  
4. **Analysis** – `analysis.py` reads `metrics.csv`, fits piecewise logistic regression, computes VIF, performs hypothesis tests, writes `analysis_report.json`.  
5. **State Update** – Checksums for `metrics.csv` and `analysis_report.json` are added to `data/checksums.json`.  

## Constraints
- **Immutability** – `tasks.json` & `skills.json` are read‑only after generation.  
- **Append‑Only Log** – `metrics.csv` is only appended; no in‑place edits.  
- **Schema Validation** – Every read/write step validates against the corresponding schema; failures abort the CI run.  

---


