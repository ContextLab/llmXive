# Data Model: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

## 1. Overview

This document defines the data model for the pilot study. All data is stored as files (JSON/CSV/Parquet) in `data/`. No database is used.

## 2. Entity Definitions

### 2.1 Participant

A volunteer recruited for the study.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `participant_id` | string | Unique ID (e.g., `P001`) | Primary key, anonymized |
| `condition` | string | Assigned condition: `llm`, `human`, `none` | Enum |
| `start_time` | datetime | Session start (UTC) | ISO 8601 |
| `end_time` | datetime | Session end (UTC) | ISO 8601 |
| `total_time_sec` | integer | Total elapsed time (seconds) | ≥0 |
| `status` | string | `complete`, `incomplete`, `failed` | Enum |
| `dropout_reason` | string | Reason for dropout (if incomplete/failed) | Optional |
| `anonymized` | boolean | Whether PII has been removed | True |
| `irb_protocol_hash` | string | SHA256 hash of the IRB protocol document | Required (Constitution VI) |

### 2.2 Task

An onboarding activity assigned to participants.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `task_id` | string | Unique ID (e.g., `T001`) | Primary key |
| `repo_url` | string | Repository URL | |
| `commit_hash` | string | Pinned commit hash | |
| `condition` | string | Condition for this task: `llm`, `human`, `none` | Enum |
| `expected_duration_min` | integer | Expected completion time (minutes) | |
| `description` | string | Task description | |

### 2.3 TaskLog

Per-task metrics for a participant.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `log_id` | string | Unique ID | Primary key |
| `participant_id` | string | FK to Participant | |
| `task_id` | string | FK to Task | |
| `start_time` | datetime | Task start (UTC) | ISO 8601 |
| `end_time` | datetime | Task end (UTC) | ISO 8601 |
| `time_sec` | integer | Elapsed time (seconds) | ≥0 |
| `help_request_count` | integer | Number of "Help Requests" (keyword + moderator tag) | ≥0 |
| `cognitive_load_proxy` | float | Composite score (time, clicks, NASA-TLX) | 0.0-100.0 |
| `helpfulness_rating` | integer | Likert scale (1-5) | 1-5 |
| `moderator_intervention` | boolean | Whether moderator intervened | |
| `intervention_type` | string | `clarification`, `action`, or `none` | |
| `status` | string | `complete`, `failed`, `timeout` | Enum |

### 2.4 Repository

Repository metadata for the study.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `repo_id` | string | Unique ID | Primary key |
| `url` | string | GitHub URL | |
| `commit_hash` | string | Pinned commit | |
| `loc` | integer | Lines of Code | ≥0 |
| `cyclomatic_complexity` | integer | Cyclomatic Complexity | ≥0 |
| `has_human_docs` | boolean | Whether human docs exist | |
| `doc_rubric_score` | integer | Rubric score (0-4) for Human Docs | 0-4 |
| `condition` | string | Assigned condition: `llm`, `human`, `none` | Enum |

### 2.5 LLMConfig

Configuration for documentation generation.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `config_id` | string | Unique ID | Primary key |
| `model_name` | string | LLM model (e.g., `gpt-4`, `phi-2`) | |
| `version` | string | Model version/commit | |
| `temperature` | float | Sampling temperature | 0.0-2.0 |
| `prompt_template` | string | Prompt used | |
| `fallback_model` | string | Fallback model (e.g., `phi-2`) | |
| `checksum` | string | SHA256 of config | |

### 2.6 AnalysisResult

Output of statistical analysis.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `result_id` | string | Unique ID | Primary key |
| `test_type` | string | e.g., `Welch_ANOVA`, `Games-Howell` | |
| `statistic` | float | Test statistic (F, t, etc.) | |
| `p_value` | float | p-value | 0.0-1.0 |
| `degrees_of_freedom` | string | e.g., `df1=2, df2=15` | |
| `confidence_interval` | string | e.g., `[0.1, 0.9]` | |
| `conclusion` | string | Summary statement | |
| `timestamp` | datetime | Analysis time (UTC) | |
| `resource_usage` | object | Runtime and memory metrics | See schema |

## 3. Data Flow

1. **Participant Registration**: `experiment.py` creates `Participant` record (includes `irb_protocol_hash`).
2. **Task Assignment**: `experiment.py` creates `TaskLog` for each task.
3. **Documentation Generation**: `doc_pipeline.py` creates `LLMConfig` and `Repository` records.
4. **Data Collection**: `experiment.py` logs `TaskLog` entries.
5. **Anonymization**: `anonymize.py` creates anonymized `Participant` and `TaskLog` in `data/processed/`.
6. **Analysis**: `stats_runner.py` reads `data/processed/` (including `Repository` covariates) and writes `AnalysisResult` to `data/processed/`.
7. **Reporting**: `report_gen.py` reads `AnalysisResult` and generates `paper/`.

## 4. Anonymization Rules

- **Participant ID**: Replace with hash (e.g., `P001` → `a1b2c3d4`).
- **PII Removal**: Remove names, emails, IPs from raw logs before analysis.
- **Consent Records**: Stored separately in `data/consent/` with restricted access.
- **IRB Protocol**: Hash stored in `Participant` record; original file in `data/irb_protocol.pdf` (restricted).

## 5. File Structure

```text
data/
├── raw/
│   ├── participants.json       # Raw participant data (PII included)
│   ├── task_logs.json          # Raw task logs (PII included)
│   └── consent/                # Consent records (restricted)
├── processed/
│   ├── participants_anon.json  # Anonymized participant data
│   ├── task_logs_anon.json     # Anonymized task logs
│   ├── repos.json              # Repository metadata (with covariates)
│   ├── llm_config.json         # LLM configuration
│   └── analysis_results.json   # Statistical analysis outputs
├── repos/                      # Pinned repository snapshots
│   └── <repo_id>/
│       ├── commit_hash.txt
│       └── source_code/
└── checksums.json              # SHA256 checksums for all files
```

## 6. Schema Validation

All files in `data/processed/` must validate against schemas in `contracts/`.