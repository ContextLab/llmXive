# Data Model: Evaluating the Impact of Code Generation Models on Developer Productivity

**Branch**: `001-code-gen-productivity` | **Date**: 2024-01-15

## Entity Relationship Diagram

```
Participant (1) ──< Session >── (1) Problem
    │                               │
    │                               │
    └──< Submission >── (1) Metric
```

## Core Entities

### Participant

Represents a recruited volunteer with ≥1 year programming experience.

| Field | Type | Constraints | FR/SC Reference |
|-------|------|-------------|-----------------|
| id | string | UUID, unique | FR-012 |
| experience_years | integer | ≥1 | User Story 1 |
| consent_timestamp | datetime | UTC, not null | Constitution VII |
| dropout_status | string | "complete", "incomplete", "withdrawn" | Edge Case |
| created_at | datetime | UTC, not null | FR-012 |

### Session

Represents a participant's completion of one condition (LLM-assisted or baseline).

| Field | Type | Constraints | FR/SC Reference |
|-------|------|-------------|-----------------|
| id | string | UUID, unique | FR-012 |
| participant_id | string | FK to Participant.id | FR-012 |
| condition | string | "llm_assisted", "baseline" | User Story 1 |
| condition_order | integer | 1 or 2 (counterbalanced) | User Story 1, SC-001 |
| randomization_seed | integer | Fixed for reproducibility | FR-012, Constitution I |
| start_timestamp | datetime | UTC, not null | FR-002 |
| end_timestamp | datetime | UTC, nullable | FR-002 |
| completed | boolean | Default false | User Story 1 |

### Problem

Represents a coding task from HumanEval or Codeforces.

| Field | Type | Constraints | FR/SC Reference |
|-------|------|-------------|-----------------|
| id | string | Problem identifier (HumanEval/Codeforces ID) | FR-014 |
| source | string | "humaneval", "codeforces" | FR-001 |
| difficulty | string | "easy", "medium", "hard" | FR-014 |
| statement | text | UTF-8 problem description | FR-001 |
| test_suite | text | UTF-8 test code | FR-004 |
| avg_solution_time_sec | integer | ≥300 (5 minutes) | FR-014 |
| version | string | Commit hash or API snapshot | Constitution VI |

### Submission

Represents a participant's code submission for a problem.

| Field | Type | Constraints | FR/SC Reference |
|-------|------|-------------|-----------------|
| id | string | UUID, unique | FR-003 |
| participant_id | string | FK to Participant.id | FR-003 |
| session_id | string | FK to Session.id | FR-003 |
| problem_id | string | FK to Problem.id | FR-003 |
| condition | string | "llm_assisted", "baseline" | FR-003 |
| source_code | text | UTF-8, not null | FR-003 |
| submission_timestamp | datetime | UTC, not null | FR-002 |
| compile_success | boolean | Default true | Edge Case |
| syntax_error | text | Nullable error message | Edge Case |

### Metric

Represents a quality or time measurement.

| Field | Type | Constraints | FR/SC Reference |
|-------|------|-------------|-----------------|
| id | string | UUID, unique | FR-004 |
| submission_id | string | FK to Submission.id | FR-004 |
| metric_type | string | "time", "pass_rate", "complexity", "coverage", "warnings" | FR-004-007 |
| value | float | Depends on metric_type | FR-004-007 |
| computed_at | datetime | UTC, not null | FR-004-007 |

## Data Flow

1. **Participant Registration**: Participant consents → Participant record created
2. **Randomization**: Participant assigned to condition order → Session records created
3. **Problem Loading**: Problem loaded from HumanEval/Codeforces → Problem record created
4. **Task Execution**: Participant completes task → Submission record + code file created
5. **Quality Assessment**: Test suite, radon, coverage.py, pylint executed → Metric records created
6. **Statistical Analysis**: Paired comparisons computed → Analysis results exported

## Data Hygiene (Constitution III)

- **Raw Data**: `data/raw/humaneval/`, `data/raw/codeforces/` (checksummed, unmodified)
- **Derived Data**: `data/derived/` (new files with documented derivations)
- **Participant Data**: `data/participants/` (anonymized, encrypted at rest)
- **Checksums**: All files under `data/` recorded in `data/metadata.yaml`
- **PII Scan**: No PII in committed data; Repository-Hygiene Agent validates

## Data Versioning (Constitution V)

- **Content Hash**: SHA-256 for all files under `data/`
- **Metadata**: `data/metadata.yaml` includes:
  - Dataset version (commit hash/API snapshot date)
  - Checksums
  - Processing pipeline version
  - `updated_at` timestamp
