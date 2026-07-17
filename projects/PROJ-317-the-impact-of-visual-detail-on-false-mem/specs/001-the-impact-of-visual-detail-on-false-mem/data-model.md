# Data Model: Visual Detail and False Memory Susceptibility

## Overview

This document defines the schema for all data artifacts in the project, ensuring compliance with Constitution III (Data Hygiene) and IV (Single Source of Truth).

## Entities

### 1. Stimulus Metadata
**Path**: `data/stimuli/{stimulus_id}.yaml`
**Purpose**: Records the exact parameters of image manipulation for reproducibility.

| Field | Type | Description |
| :--- | :--- | :--- |
| `stimulus_id` | string | Unique hash of the baseline image. |
| `baseline_path` | string | Relative path to original image. |
| `enhanced_path` | string | Relative path to enhanced image. |
| `reduced_path` | string | Relative path to reduced image. |
| `manipulation_params` | object | Details of the compositing (objects added/removed). |
| `complexity_score` | float | Calculated complexity (0.0 - 1.0). |
| `created_at` | timestamp | ISO8601 timestamp of generation. |
| `checksum` | string | SHA-256 of the file content. |

### 2. Participant Session
**Path**: `data/responses/session_{participant_id}.jsonl`
**Purpose**: Raw, timestamped responses from a single session.

| Field | Type | Description |
| :--- | :--- | :--- |
| `session_id` | string | Unique session identifier. |
| `participant_id` | string | Hashed pseudonym. |
| `start_time` | timestamp | Session start. |
| `end_time` | timestamp | Session end. |
| `condition` | string | "enhanced" or "reduced". |
| `consent_verified` | boolean | Must be true. |
| `responses` | list | List of response objects. |

### 3. Response
**Path**: Embedded in `Participant Session`
**Purpose**: Individual answer to a recognition question.

| Field | Type | Description |
| :--- | :--- | :--- |
| `question_id` | string | Unique ID for the question. |
| `is_lure` | boolean | True if the item was never in the image. |
| `response` | boolean | True if participant said "Yes, it was there". |
| `reaction_time_ms` | integer | Time from question display to response. |
| `timestamp` | timestamp | Precise time of response. |
| `semantic_plausibility` | float | Score (0.0-1.0) indicating how plausible the lure is (WordNet-based). |

### 4. Analysis Results
**Path**: `data/analysis/results.json`
**Purpose**: Aggregated statistical outputs.

| Field | Type | Description |
| :--- | :--- | :--- |
| `anova_f` | float | F-statistic. |
| `anova_p` | float | P-value. |
| `effect_size` | float | Partial eta-squared. |
| `n_participants` | integer | Total valid participants. |
| `false_alarm_rates` | object | Mean rates per condition. |

## Data Flow

1.  **Ingestion**: `downloader.py` fetches images → `filter.py` selects for complexity → `manipulator.py` creates variants → `metadata.py` writes `stimuli/*.yaml`.
2.  **Collection**: `interface/app.py` collects responses → writes to `data/responses/*.jsonl`.
3.  **Processing**: `analysis/stats.py` reads `data/responses/` → computes metrics → writes `data/analysis/results.json`.
4.  **Logging**: Errors in manipulation or network timeouts are written to `data/logs/*.log`.

## Constraints

*   **PII**: No email, name, or IP address stored in `data/responses/`. IP addresses are stripped at the Streamlit gateway.
*   **Immutability**: Once a `session_*.jsonl` file is written, it is never modified. Corrections create a new versioned file.
*   **Checksums**: All files in `data/stimuli/` and `data/analysis/` must have a corresponding entry in `state/.../artifact_hashes`.