# Data Model: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

## Entity-Relationship Overview

The data model consists of three core entities: `Participant`, `Repository`, and `Task`, with associated `Metric` observations.

### Entities

#### Participant
- **participant_id**: Unique identifier (UUID).
- **condition**: Categorical (LLM Docs, Human Docs, No Docs).
- **demographics**: Optional (age, experience level, etc.) — anonymized.
- **consent_record**: Reference to IRB protocol (e.g., `IRB-REF-001`).

#### Repository
- **repo_id**: Unique identifier.
- **url**: GitHub repository URL.
- **commit_hash**: Pinned commit hash.
- **doc_type**: Categorical (LLM, Human, None).
- **file_count**: Number of files (≤ 500).
- **rubric_score**: Float (0-100) from Phase 0 verification.

#### Task
- **task_id**: Unique identifier.
- **repo_id**: Foreign key to Repository.
- **description**: Task description.
- **expected_outcome**: Criteria for completion.

#### Metric
- **metric_id**: Unique identifier.
- **participant_id**: Foreign key to Participant.
- **task_id**: Foreign key to Task.
- **start_time**: Timestamp.
- **end_time**: Timestamp.
- **completion_time**: Calculated (end_time - start_time).
- **question_count**: Integer.
- **helpfulness_rating**: Likert scale (1-5).
- **status**: Categorical (complete, incomplete, failed).
- **failure_reason**: String (e.g., "poor_docs", "timeout", "user_abandoned") — populated if `status` is "failed" or "incomplete" due to intervention.
- **intervention_flag**: Boolean (True if moderator intervened).

## Data Flow

1. **Data Collection**: `data_collection.py` logs participant metrics to `data/raw/participant_logs.json`.
2. **Data Processing**: `analysis.py` loads raw logs, validates completeness, and outputs `data/processed/cleaned_dataset.csv`.
3. **Analysis**: Statistical tests (LMM) run on `cleaned_dataset.csv`.
4. **Reporting**: Final report generated from analysis results.

## Data Hygiene

- **Checksums**: All raw data files checksummed and recorded in `data/checksums.txt`.
- **PII**: No personally identifiable information stored; demographics anonymized.
- **Immutability**: Raw data never modified; derivations written to new files.

