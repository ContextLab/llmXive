# Data Model: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

## Overview

This document defines the data schemas for the project, ensuring strict adherence to the "Single Source of Truth" and "Data Hygiene" principles. All data is stored in `data/` with checksums, and all derived data includes provenance metadata.

## Entity Relationship Diagram (Conceptual)

1.  **Stimulus**: A single background image.
    *   One-to-Many with **Measurement** (multiple participants view the same stimulus).
2.  **Participant**: A human subject ID.
    *   One-to-Many with **Measurement** (one participant views multiple stimuli).
3.  **Measurement**: A single observation linking a Stimulus and a Participant.
    *   Contains the cognitive load outcomes (TLX, RT).

## Schema Definitions

### 1. Stimulus Metadata (`data/derived/stimuli_metadata.csv`)
Contains the computed visual complexity metrics for each background image.

| Column | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `stimulus_id` | string | Unique ID (e.g., `img_001`) | Primary Key |
| `filename` | string | Relative path in `data/stimuli/` | Not Null |
| `entropy` | float | Shannon entropy (0-8 range) | >= 0 |
| `color_variance` | float | Variance of saturation channel | >= 0 |
| `object_count` | int | YOLOv8n detection count | >= 0 |
| `checksum` | string | SHA-256 of the image file | Not Null |

### 2. Participant Measurement (`data/measurements/raw_responses.csv`)
Raw (empirical) data from the pilot study.

| Column | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `session_id` | string | Unique session ID | Primary Key |
| `participant_id` | string | Human participant ID | Not Null |
| `stimulus_id` | string | Link to Stimulus | Foreign Key |
| `task_difficulty` | float | Self-reported difficulty (0.0-1.0) | 0.0 to 1.0 |
| `nasa_tlx_score` | float | Subjective load (0-100) | 0.0 to 100.0 |
| `reaction_time_ms` | int | Reaction time in ms | > 0 |
| `accuracy_pct` | float | Accuracy percentage | 0.0 to 100.0 |
| `attention_check` | bool | Passed attention check | True/False |
| `missing_flag` | bool | Flagged for exclusion | True/False |
| `is_baseline` | bool | Flag for baseline condition | True/False |

### 3. Analysis Results (`results/analysis/model_summary.json`)
Aggregated statistical results.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_formula` | string | The LMM formula string |
| `fixed_effects` | list | List of dicts: `{term, estimate, std_err, p_value, adj_p_value, ci_lower, ci_upper}` |
| `random_effects` | list | Variance components for random intercepts |
| `vif_scores` | dict | VIF for each predictor |
| `sensitivity_analysis` | list | Results for alpha sweeps {0.01, 0.05, 0.1} |
| `fwer_estimate` | float | Estimated Family-Wise Error Rate |
| `diagnostics` | dict | Shapiro-Wilk, Residual plots status |

## Data Flow & Transformation

1.  **Raw Images** (`data/stimuli/`) → `extract_metrics.py` → **Stimulus Metadata** (`data/derived/`).
2.  **Raw Responses** (collected from pilot) → `data/measurements/raw_responses.csv`.
3.  **Raw Responses** (filtered for `missing_flag=False`) → `analyze_results.py` → **Analysis Results** (`results/`).

## Data Hygiene & Provenance

*   **Checksums**: Every file in `data/stimuli/` and `data/derived/` is checksummed. The `state/` file records these hashes.
*   **Immutability**: Raw files are never modified. Transformations create new files (e.g., `raw_responses_v1.csv`).
*   **PII**: No real names or emails. `participant_id` is an anonymized code.
