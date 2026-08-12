# Data Model: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

## 1. Entity-Relationship Overview

The system manages four core entities: **Method**, **Summary**, **Participant**, and **Interaction**.

### 1.1 Method
Represents a buggy Java method extracted from Defects4J.
- **Attributes**: `method_id` (PK), `project_name`, `bug_id`, `source_code`, `ground_truth_line`, `context_code`.

### 1.2 Summary
Represents a generated summary for a method under a specific condition.
- **Attributes**: `summary_id` (PK), `method_id` (FK), `condition` (baseline/llm/rule), `summary_text`, `generation_status` (success/fallback/timeout).

### 1.3 Participant
Represents a study participant (anonymized).
- **Attributes**: `participant_id` (PK, anonymized), `cohort`, `experience_years`, `dropout_status`.

### 1.4 Interaction
Represents a single task attempt by a participant.
- **Attributes**: `interaction_id` (PK), `participant_id` (FK), `task_id` (FK), `condition`, `timestamp_ms`, `selected_line`, `ground_truth_line`, `is_correct` (derived).

## 2. Data Flow

1. **Ingestion**: Defects4J Parquet → `data/raw/defects4j.parquet`.
2. **Preprocessing**: Extract methods → `data/processed/methods.csv`.
3. **Summarization**:
   - Baseline: `summary_text` = null.
   - Rule: `srcML` extraction → `data/processed/summaries_rule.csv`.
   - LLM: `CodeLlama` inference (GPU) → `data/processed/summaries_llm.csv` (or fallback).
4. **Study Execution**:
   - Simulated: `simulate_study.py` generates `data/interaction_logs/simulated_logs.csv`.
   - Real: Web interface logs → `data/interaction_logs/raw_logs.csv` → anonymized → `data/interaction_logs/anonymized_logs.csv`.
5. **Analysis**: `analysis.py` reads `anonymized_logs.csv` + `methods.csv` → `data/analysis_results.json`.

## 3. Storage Format

- **Raw Data**: Parquet (Defects4J), CSV (intermediate).
- **Logs**: CSV with headers: `participant_id,task_id,condition,timestamp_ms,selected_line,ground_truth_line`.
- **Results**: JSON with nested structure for p-values, effect sizes, CIs.
- **Checksums**: SHA-256 stored in `data/checksums.txt`.

## 4. Anonymization Strategy
- **Participant IDs**: Hashed using SHA-256 with a salt stored in `data/.salt` (not committed).
- **PII Removal**: No names, emails, or IP addresses in `data/interaction_logs/`.
- **Consent Data**: Stored in `data/consent/` (excluded from VCS).
