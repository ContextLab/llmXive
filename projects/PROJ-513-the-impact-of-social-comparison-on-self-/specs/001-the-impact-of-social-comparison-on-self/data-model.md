# Data Model: The Impact of Social Comparison on Self-Perception on AI-Generated Image Platforms

## Overview

This document defines the data structures required for the `001-synthetic-body-comparison` feature. It covers the schema for stimuli metadata, participant responses, and the final analysis dataset. All data is stored in CSV or JSON format within the `data/` directory.

## Entity Definitions

### 1. Stimulus Metadata
Stores the properties of the image assets to ensure matching and integrity.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `stimulus_id` | String | Unique identifier for the image (e.g., `AI_001`, `H_001`). | PK, Non-null |
| `origin` | Enum | Source of the image. | Values: `AI`, `Human` |
| `match_group` | String | Identifier linking an AI image to its Human counterpart. | Non-null, Foreign Key |
| `file_path` | String | Relative path to the image file in `data/stimuli/`. | Non-null |
| `pose` | String | Description of the pose (e.g., `front_view`, `side_profile`). | Non-null |
| `lighting` | String | Lighting condition (e.g., `studio`, `natural`). | Non-null |
| `body_type` | String | Broad category (e.g., `athletic`, `slim`). | Non-null |
| `content_hash` | String | SHA-256 hash of the image file. | Non-null, Immutable |
| `generation_prompt` | String | The exact prompt used to generate the AI image (if origin=AI). | Non-null for AI; Optional for Human |

### 2. Participant Profile
Stores baseline covariates collected before stimulus exposure.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | String | Anonymized unique identifier. | PK, Non-null |
| `incom_score` | Integer | Iowa-Netherlands Comparison Orientation Measure score. | Range: 0-60 |
| `usage_frequency` | Float | Average weekly hours on image-sharing platforms. | Non-negative |
| `enrollment_date` | Date | Date of survey completion. | Non-null |
| `completion_status` | Enum | Status of the session. | Values: `Complete`, `Partial`, `Excluded` |
| `is_outlier` | Boolean | Flag for extreme INCOM scores (for sensitivity analysis). | Default: False |

### 3. Response Log
Records the immediate self-report after each stimulus.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `response_id` | String | Unique identifier for the response. | PK |
| `participant_id` | String | Link to Participant Profile. | FK |
| `stimulus_id` | String | Link to Stimulus Metadata. | FK |
| `biss_score` | Float | Body Image States Scale score. | Range: 1-5 |
| `timestamp` | DateTime | Time of response submission. | Non-null |
| `trial_order` | Integer | Position of the image in the randomized sequence. | 1-40 |

### 4. Blind Pre-Test Result (FR-009)
Stores the results of the validation test for visual indistinguishability of quality.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `pretest_id` | String | Unique identifier for the pre-test run. | PK |
| `p_value` | Float | P-value from the t-test comparing quality ratings. | Range: 0-1 |
| `passed` | Boolean | True if p > 0.05 (indistinguishable quality). | Derived |
| `timestamp` | DateTime | Date of pre-test execution. | Non-null |

### 5. Analysis Dataset (Derived)
A flattened dataset created for the LME model, combining the above entities.

| Field | Type | Description |
| :--- | :--- | :--- |
| `participant_id` | String | Random intercept grouping variable. |
| `stimulus_id` | String | Unique stimulus identifier. |
| `image_type` | Category | `AI` or `Human` (Fixed effect). |
| `biss_score` | Float | Dependent variable. |
| `incom_score` | Float | Covariate (Fixed effect, mean-centered). |
| `usage_frequency` | Float | Covariate (Fixed effect, mean-centered). |
| `trial_order` | Integer | Control variable (optional). |
| `is_outlier` | Boolean | Flag for sensitivity analysis. |

## Data Flow

1.  **Ingestion**: `stimulus_loader.py` reads `data/stimuli/metadata.json` to validate image existence and hashes.
2.  **Pre-Test**: `data_validation.py` runs the blind pre-test (if not done) and writes `data/pretest/results.json`.
3.  **Collection**: External tool (or simulator) writes `raw/participant_{id}.csv` containing `Response Log` data.
4.  **Validation**: `data_validation.py` checks:
    - Completeness: ≥ 95% non-null values.
    - Participant Count: ≥ 150 (target).
    - Stimulus Match: All `stimulus_id`s exist in `Stimulus Metadata`.
    - **Gate**: If validation fails, exit with non-zero code.
5.  **Processing**: `analysis.py` merges `Participant Profile` and `Response Log` into `Analysis Dataset`.
    - Center covariates.
    - Flag outliers.
6.  **Output**: `Analysis Dataset` is fed into the LME model. Results are saved to `data/analysis_results.json`.

## Constraints & Validation Rules

- **PII Exclusion**: No names, emails, or IP addresses in `data/`. `participant_id` is a random UUID.
- **Immutability**: Raw response files are never modified. Derived files are created with new timestamps.
- **Stimulus Integrity**: The `content_hash` in `Stimulus Metadata` must match the actual file hash. Mismatch blocks the study.
- **Range Checks**: `biss_score` must be 1.0–5.0; `incom_score` must be 0–60.
- **FR-009 Gate**: If `data/pretest/results.json` indicates `passed: false`, the study launch is blocked.