# Data Model: The Influence of Typographic Salience on Moral Judgments

## Overview
This document defines the data structures for the typographic salience experiment. It ensures traceability from raw text scenarios to final statistical output, adhering to the "Single Source of Truth" principle.

## Entities

### 1. Scenario
The base experimental unit (a morally ambiguous text scenario).
-   `scenario_id`: Unique string (e.g., `SCN-001`).
-   `source_dataset`: Name of the source (e.g., `Dahoas/rm-single-context`).
-   `original_text`: The raw text of the scenario.
-   `ambiguity_score`: Reward score from the dataset (proxy for human coding).
-   `ambiguity_label`: Boolean (True if score indicates ambiguity).
-   `is_ambiguous`: Boolean (True if score is within the ambiguous range).

### 2. Stimulus Variant
A manipulated version of a Scenario.
-   `stimulus_id`: Unique string (e.g., `STIM-001-LOW`).
-   `scenario_id`: FK to Scenario.
-   `salience_level`: Enum (`low`, `medium`, `high`).
-   `manipulated_text`: The text with typographic emphasis applied.
-   `semantic_similarity`: Float (Cosine similarity to original text embeddings).
-   `semantic_preserved`: Boolean (True if similarity ≥ 0.95).

### 3. Participant
The subject providing ratings.
-   `participant_id`: Unique string (e.g., `P-001`).
-   `start_time`: Timestamp.
-   `end_time`: Timestamp.
-   `total_items`: Integer.
-   `variance`: Float (Variance of their ratings).
-   `is_valid`: Boolean (True if variance ≥ 0.1 and < 90% identical ratings).

### 4. Response
A single rating event.
-   `response_id`: Unique string.
-   `participant_id`: FK to Participant.
-   `stimulus_id`: FK to Stimulus Variant.
-   `blame_rating`: Integer (1-7).
-   `timestamp`: Timestamp.

## Data Flow
1.  **Ingest**: `data/raw/scenarios.json` -> `data/processed/scenarios_cleaned.json`.
2.  **Manipulate**: `data/processed/scenarios_cleaned.json` -> `data/processed/stimuli/` (text variants + metadata).
3.  **Survey**: `data/survey/responses_raw.csv` (from survey tool).
4.  **Clean**: `data/processed/responses_cleaned.csv` (excluding invalid participants).
5.  **Analyze**: `data/processed/analysis_results.json` (LMM output, effect sizes).

## Constraints
-   **No PII**: `participant_id` is anonymized.
-   **Immutability**: Raw files in `data/raw` are never modified.
-   **Traceability**: Every `response_id` links to exactly one `stimulus_id` and `participant_id`.