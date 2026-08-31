# Data Model: The Influence of Perceived Agency in AI Interactions on Trust

## Overview

This document defines the data structures used throughout the project. It ensures that the experimental simulation, data storage, and analysis pipeline adhere to a single, consistent schema. The model supports the "Single Source of Truth" principle by separating structural definitions (schema) from content (survey items).

## Entities

### 1. Participant
Represents a single user session in the experiment.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | UUID | Unique identifier for the session. | Required, Unique |
| `condition` | String | Experimental condition assigned. | Enum: `["High", "Low", "Control"]` |
| `adherence_rate` | Float | Percentage of AI recommendations followed. | Range: [0.0, 100.0] |
| `trust_item_1` ... `trust_item_12` | Integer | Individual responses to Lee and See items. | Range: [1, 7] |
| `trust_score` | Float | **Derived** mean of 12 items. | Calculated, included in raw CSV for schema compliance |
| `attention_score` | Float | Continuous attention metric (0-100). Derived from 5 attention questions. | Range: [0.0, 100.0] (steps of 20) |
| `attention_check` | Boolean | Derived: True if `attention_score` >= 80. | Calculated |
| `cognitive_load_score` | Float | Manipulation check for cognitive load. | Range: [1, 7] |
| `perceived_agency_score` | Float | Manipulation check for perceived agency. | Range: [1, 7] |
| `completion_time_sec` | Float | Time taken to complete the task. | > 0 |
| `timestamp` | ISO8601 | Time of session completion. | Required |

### 2. Survey Metadata
Stores the text of the survey items (separate from the data to avoid schema bloat).

| Field | Type | Description |
| :--- | :--- | :--- |
| `item_id` | String | Identifier (e.g., `trust_item_1`). |
| `question_text` | String | The full text of the question. |
| `scale_min` | Integer | Minimum value (e.g., 1). |
| `scale_max` | Integer | Maximum value (e.g., 7). |
| `source` | String | Citation for the item (e.g., "Lee & See, 2004"). |

### 3. Analysis Result
Represents the output of the statistical pipeline.

| Field | Type | Description |
| :--- | :--- | :--- |
| `analysis_id` | UUID | Unique identifier for the run. |
| `contrast_name` | String | Name of the contrast (e.g., "High vs Low"). |
| `t_statistic` | Float | t-statistic value. |
| `p_value` | Float | Raw p-value. |
| `p_value_adj` | Float | Adjusted p-value (Holm-Bonferroni). |
| `cohen_d` | Float | Effect size. |
| `significant` | Boolean | Is the result significant at α=0.05? |

## Data Flow

1.  **Generation**: `simulation/task_generator.py` creates raw data conforming to the `Participant` schema (individual items, plus pre-calculated `trust_score` and `attention_score`).
2.  **Storage**: Raw data is saved to `data/raw/` as CSV.
3.  **Processing**: `analysis/contrasts.py` reads raw data, calculates `attention_check` (derived), and computes statistics.
4.  **Output**: Results are saved to `data/processed/` as CSV/JSON and validated against the `Analysis Result` schema.

## Data Hygiene

-   **Checksums**: Every file in `data/raw/` and `data/processed/` is checksummed (SHA-256) upon creation.
-   **PII**: No Personally Identifiable Information (names, emails) is collected. `participant_id` is a random UUID.
-   **Immutability**: Raw data files are never modified. Derivations create new files in `data/processed/`.

## Attention Check Definition

The attention check consists of a **series of 5 distinct questions** (e.g., "Select the option that is NOT a fruit", "What is 2+2?", etc.).
-   **Attention Score**: Percentage of correct answers out of 5 (0, 20, 40, 60, 80, 100).
-   **Threshold Justification**: The range is based on standard practice in online panel studies to balance data quality and sample size. A threshold of 70% corresponds to 3.5/5 correct (rounded to 4/5 = 80%), making the sweep mathematically valid.
