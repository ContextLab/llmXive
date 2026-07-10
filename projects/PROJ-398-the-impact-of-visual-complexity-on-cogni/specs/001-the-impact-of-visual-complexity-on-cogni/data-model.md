# Data Model: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

## 1. Overview

This document defines the data structures used throughout the project. All data is stored in JSON or CSV formats, with strict schema validation against the YAML contracts defined in `contracts/`.

## 2. Entity Definitions

### 2.1 BackgroundFrame
Represents a single frame from a meeting video (or synthetic image) with computed complexity metrics.

- **Source**: `data/stimuli/` (raw) -> `data/derived/metrics.json` (processed).
- **Key Fields**: `frame_id`, `entropy`, `color_variance`, `object_count`.
- **Constraints**: `entropy` ≥ 0, `object_count` ≥ 0.

### 2.2 HumanRating
Represents a human participant's rating of a background image for visual complexity.

- **Source**: `data/measurements/pilot_ratings.csv`.
- **Key Fields**: `image_id`, `participant_id`, `complexity_score` (1-10).
- **Constraints**: `complexity_score` ∈ [1, 10].

### 2.3 ParticipantSession
Represents a participant's interaction with the experimental stimuli, including cognitive load metrics.

- **Source**: `data/measurements/session_logs.csv`.
- **Key Fields**: `session_id`, `participant_id`, `clip_id`, `nasa_tlx_score`, `reaction_time_ms`, `accuracy_pct`, `task_difficulty`.
- **Constraints**: `reaction_time_ms` > 0.

### 2.4 AnalysisResult
Represents the output of the statistical model.

- **Source**: `data/derived/model_results.json`.
- **Key Fields**: `model_id`, `predictor`, `estimate`, `std_err`, `p_value`, `p_adj`, `vif`, `ci_lower`, `ci_upper`.

## 3. Data Flow

1.  **Ingestion**: Raw images placed in `data/stimuli/`.
2.  **Processing**: `code/metrics/extraction.py` reads images, computes metrics, writes to `data/derived/metrics.json`.
3.  **Collection**: Pilot ratings and session logs written to `data/measurements/`.
4.  **Analysis**: `code/analysis/models.py` reads metrics and session logs, fits LMM, writes `data/derived/model_results.json`.
5.  **Validation**: `tests/test_contracts.py` validates all JSON/CSV outputs against `contracts/*.schema.yaml` (including `analysis_result.schema.yaml` and `analysis_results.schema.yaml`).

## 4. Schema Validation

All data artifacts must conform to the schemas defined in:
- `contracts/background_frame.schema.yaml`
- `contracts/human_rating.schema.yaml`
- `contracts/participant_session.schema.yaml`
- `contracts/participant_sessions.schema.yaml`
- `contracts/analysis_result.schema.yaml`
- `contracts/analysis_results.schema.yaml`
- `contracts/metrics.schema.yaml`
- `contracts/stimuli_metadata.schema.yaml`
- `contracts/stimuli_metrics.schema.yaml`
- `contracts/participant_data.schema.yaml`
- `contracts/participant_measurements.schema.yaml`