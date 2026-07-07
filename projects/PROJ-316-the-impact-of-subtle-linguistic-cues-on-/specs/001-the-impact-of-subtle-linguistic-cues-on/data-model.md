# Data Model: The Impact of Subtle Linguistic Cues on Perceived Authenticity in AI Chatbots

## Overview

This document defines the data structures used throughout the project lifecycle, ensuring adherence to the "Single Source of Truth" principle (Constitution Principle IV). All data artifacts must conform to the schemas defined in `contracts/`.

## Entity Definitions

### 1. Conversation (Raw Input)
Represents a single chatbot interaction turn.
*   **Source**: Raw Parquet/JSONL from verified datasets.
*   **Fields**:
    *   `conversation_id` (string): Unique identifier for the conversation session.
    *   `turn_number` (integer): Sequence number of the turn.
    *   `text_content` (string): The raw text of the chatbot response.
    *   `topic_category` (string, optional): Category of the topic (if available).
    *   `authenticity_score` (float, optional): Human-rated authenticity (1-5 or 1-7). May be missing in raw data.

### 2. LinguisticMetrics (Derived)
Quantitative features extracted from `Conversation`.
*   **Source**: Output of `extraction/extract_features.py`.
*   **Fields**:
    *   `conversation_id` (string): Foreign key to raw input.
    *   `turn_number` (integer): Foreign key to raw input.
    *   `first_person_count` (integer): Count of first-person pronouns.
    *   `hedge_count` (integer): Count of hedge words from the fixed lexicon.
    *   `hedge_ratio` (float): `hedge_count / total_word_count`.
    *   `sentiment_score` (float): VADER compound score (-1.0 to 1.0).
    *   `conversation_length` (integer): Total word count.
    *   `authenticity_score` (float): Copied from raw input if present, else `NaN` (will be filled by annotation).

### 3. AnnotatedSubset (Human Ratings)
Subset of conversations with human-verified authenticity scores.
*   **Source**: Human annotation process.
*   **Fields**:
    *   `conversation_id` (string): Foreign key.
    *   `rater_id` (string): ID of the human rater.
    *   `rating_value` (float): Authenticity rating (1-5 or 1-7).
    *   `timestamp` (string): ISO 8601 timestamp.

### 4. StatisticalResult (Final Output)
Aggregated results from the analysis pipeline.
*   **Source**: Output of `analysis/models.py`.
*   **Fields**:
    *   `model_id` (string): Identifier for the specific model run.
    *   `metric_name` (string): e.g., "hedge_count", "sentiment_score".
    *   `correlation_pearson` (float): Pearson r.
    *   `correlation_spearman` (float): Spearman rho.
    *   `p_value_raw` (float): Unadjusted p-value.
    *   `p_value_adjusted` (float): Benjamini-Hochberg adjusted p-value.
    *   `regression_coefficient` (float): Beta weight from multiple regression.
    *   `std_error` (float): Standard error of the coefficient.
    *   `vif_value` (float): Variance Inflation Factor.
    *   `significance_flag` (boolean): True if adjusted p-value < 0.05.

### 5. PowerAnalysisResult (Prerequisite)
Output of the power analysis step.
*   **Source**: Output of `analysis/models.py --step power_analysis`.
*   **Fields**:
    *   `effect_size_f2` (float): Assumed effect size.
    *   `alpha` (float): Significance level (0.05).
    *   `power` (float): Target power (0.8).
    *   `required_n` (integer): Minimum sample size required.
    *   `status` (string): "PASS" or "UNDERPOWERED".

## Data Flow

1.  **Ingest**: Raw data (`data/raw/*.parquet`) -> Checksummed.
2.  **Extract**: `extraction/extract_features.py` -> `data/processed/features.csv` (LinguisticMetrics).
3.  **Annotate**: Human raters -> `data/raw/rater_metadata.json` + `data/processed/annotated_subset.csv`.
4.  **Analyze**: `analysis/models.py` -> `data/results/stats_results.csv` (StatisticalResult).
5.  **Sensitivity**: `analysis/models.py --step sensitivity` -> `data/results/sensitivity_analysis.csv`.
6.  **Visualize**: `analysis/visualize.py` -> `data/results/plots/*.png`.

## Constraints & Validation

*   **Missing Data**: If `authenticity_score` is missing, the row is included in feature extraction but excluded from regression/correlation (listwise deletion).
*   **Zero Variance**: If a predictor has zero variance, it is excluded from regression with a warning.
*   **Outliers**: Conversation length is capped at the 99th percentile if extreme outliers are detected.
*   **Validation**: `contracts/` schemas must be enforced by `test_schemas.py` before any analysis step proceeds.
