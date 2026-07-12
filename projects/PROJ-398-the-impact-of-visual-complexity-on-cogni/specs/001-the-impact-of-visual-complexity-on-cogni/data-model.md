# Data Model: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

## 1. Overview

This document defines the data structures used throughout the project. All data flows from `data/raw/` (unprocessed) to `data/processed/` (feature-engineered) and finally to `data/analysis/` (model outputs).

## 2. Entity Definitions

### 2.1 BackgroundFrame (Stimulus)
Represents a single frame or image used as a meeting background.
*   **Source**: `data/stimuli/` (images) + `data/processed/metrics.json` (computed features).
*   **Key Fields**: `frame_id`, `entropy`, `color_variance`, `object_count`.

### 2.2 ParticipantSession
Represents a single participant's interaction with the study.
*   **Source**: `data/raw/participant_logs/` (JSON logs from Streamlit).
*   **Key Fields**: `participant_id`, `session_id`, `nasa_tlx_score`, `reaction_time_ms`, `baseline_reaction_time_ms`, `task_difficulty`, `stimulus_id`.

### 2.3 HumanRating
Represents a human rating from the pilot study.
*   **Source**: `data/raw/pilot_ratings.json`.
*   **Key Fields**: `image_id`, `participant_id`, `complexity_score` (1-10).

### 2.4 AnalysisResult
Represents the output of the statistical model.
*   **Source**: `data/analysis/model_results.json`.
*   **Key Fields**: `model_id`, `predictor`, `estimate`, `std_error`, `p_value`, `p_value_adj`, `ci_lower`, `ci_upper`, `vif`, `effect_size`.

## 3. Data Flow

1.  **Ingestion**:
    *   Images placed in `data/stimuli/`.
    *   `code/metrics/extract_visual.py` runs -> `data/processed/stimulus_metrics.json`.
    *   Pilot study runs -> `data/raw/pilot_ratings.json`.
    *   Main study runs -> `data/raw/participant_logs/*.json`.
2.  **Processing**:
    *   `code/utils/data_hygiene.py` checksums raw files.
    *   `code/analysis/models.py` merges metrics with participant logs -> `data/processed/analysis_dataset.parquet`.
3.  **Analysis**:
    *   LMM and sensitivity analysis run -> `data/analysis/model_results.json`.

## 4. Schema Constraints

*   **No PII**: `participant_id` must be a UUID or anonymized string. No names, emails, or IPs stored in `data/`.
*   **Checksums**: Every file in `data/` must have a corresponding entry in `state/...yaml` `artifact_hashes`.
*   **Immutability**: Raw files are never modified. Derivations create new files.
