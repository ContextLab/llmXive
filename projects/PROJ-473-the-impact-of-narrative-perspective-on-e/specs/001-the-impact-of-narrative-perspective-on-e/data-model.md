# Data Model: The Impact of Narrative Perspective on Empathy and Moral Judgement

## Overview
This document defines the data structures, schemas, and relationships for the project. The model supports the extraction of narrative features, the storage of reader responses, and the output of statistical analysis results.

## Entities

### 1. StoryDocument
Represents a single narrative text and its extracted features.
*   **Attributes**:
    *   `story_id` (str): Unique identifier.
    *   `raw_text` (str): Full text content.
    *   `language` (str): Detected language code (e.g., "en").
    *   `perspective_score` (float): Normalized score [0.0, 1.0] indicating first-person density.
    *   `pronoun_density_1st` (float): Frequency of first-person pronouns.
    *   `pronoun_density_3rd` (float): Frequency of third-person pronouns.
    *   `narrator_distance_score` (float): Derived metric for narrative distance.
    *   `tfidf_vector` (list): Sparse or dense vector for similarity matching (excluding pronouns).
    *   `genre` (str): Extracted genre for confounder control.
    *   `publication_year` (int): Extracted publication year for confounder control.
    *   `exclusion_reason` (str, optional): Reason for exclusion (e.g., "data_quality_insufficient", "non_english").

### 2. ReaderResponse
Represents a response from a human participant (from verified external dataset).
*   **Attributes**:
    *   `response_id` (str): Unique identifier.
    *   `story_id` (str): Foreign key to `StoryDocument`.
    *   `participant_id` (str): Identifier for the participant.
    *   `empathy_score` (float): Score on empathy scale (e.g., IRI).
    *   `moral_judgement_score` (float): Score on moral judgement scale (e.g., 1-7 Likert).
    *   `attention_check_passed` (bool): Whether the participant passed attention checks.
    *   `is_valid` (bool): Final validity flag after aggregation.

### 3. AnalysisResult
Represents the outcome of the statistical tests.
*   **Attributes**:
    *   `analysis_id` (str): Unique identifier.
    *   `model_type` (str): e.g., "linear_regression".
    *   `regression_coefficient` (float): Slope for `perspective_score`.
    *   `p_value` (float): Raw p-value.
    *   `adjusted_p_value` (float): Bonferroni-adjusted p-value.
    *   `r_squared` (float): Model fit.
    *   `sample_size` (int): Number of observations.
    *   `vif_score` (float): Variance Inflation Factor.
    *   `sensitivity_threshold` (float): The threshold used for the sensitivity analysis (if applicable).
    *   `power_analysis` (dict): Optional power analysis results (effect size, N, power).

### 4. MatchingCandidate
Represents a potential match between a story and an external moral judgment entry (for validation).
*   **Attributes**:
    *   `story_id` (str).
    *   `external_entry_id` (str).
    *   `cosine_similarity` (float).
    *   `rank` (int): Rank among top candidates.
    *   `is_match` (bool): Whether the match is considered valid (based on threshold).

## Data Flow

1.  **Ingestion**: Raw text files -> `StoryDocument` (Extraction).
2.  **Validation**: `StoryDocument` + External Data -> `MatchingCandidate` (Matching).
3.  **Response Collection**: Real External Dataset -> `ReaderResponse`.
4.  **Join**: `StoryDocument` + `ReaderResponse` -> **Analysis Dataset**.
5.  **Analysis**: Analysis Dataset -> `AnalysisResult`.
6.  **Output**: `AnalysisResult` -> Visualizations (PNG) and Summary Tables (CSV).

## Storage Format
*   **Intermediate Data**: CSV files in `data/processed/`.
*   **Vectors**: Pickled objects or NumPy `.npy` files (compressed) in `data/processed/`.
*   **Final Artifacts**: JSON/CSV for results, PNG for plots in `artifacts/`.