# Data Model: Exploring the Correlation Between Musical Preference and Personality Traits

## 1. Entity Definitions

### 1.1 UserRecord
Represents a single participant in the study.
*   `user_id`: Unique identifier (hashed string).
*   `openness`: Float (0-100 or 1-5 scale, standardized).
*   `conscientiousness`: Float.
*   `extraversion`: Float.
*   `agreeableness`: Float.
*   `neuroticism`: Float.
*   `age`: Integer (years).
*   `gender`: Categorical (Male, Female, Other, Unknown).
*   `country`: String (ISO code or Region).

### 1.2 GenrePreference
Aggregated listening data for a user per genre.
*   `user_id`: Foreign key to UserRecord.
*   `genre`: Categorical (Rock, Pop, Hip-Hop, Classical, Electronic, Jazz, Folk, Country, Metal, Other).
*   `listening_minutes`: Integer (Total minutes).
*   `log_minutes`: Float (log1p of listening_minutes).
*   `genre_score`: Float (Normalized score, e.g., z-score within user).

### 1.3 AnalysisResult
Output of the statistical tests.
*   `trait`: String (Name of Big Five trait).
*   `genre`: String (Name of genre).
*   `correlation_rho`: Float (Spearman coefficient).
*   `p_value`: Float (Raw p-value).
*   `adjusted_p_value`: Float (BH-corrected p-value).
*   `is_significant`: Boolean (True if adjusted_p < 0.05).
*   `effect_size_r`: Float (Pearson r equivalent).
*   `ci_lower_bootstrap`: Float (95% CI lower bound).
*   `ci_upper_bootstrap`: Float (95% CI upper bound).
*   `beta`: Float (Regression coefficient).
*   `std_error`: Float.
*   `t_stat`: Float.
*   `vif`: Float (Variance Inflation Factor).
*   `beta_baseline`: Float (Beta coefficient in baseline model).
*   `beta_full`: Float (Beta coefficient in full model).
*   `delta`: Float (Change in beta).
*   `percent_change`: Float (Percent change in beta).
*   `effect_size_threshold_met`: Boolean (True if |effect_size_r| > 0.3).

### 1.4 RegressionCoefficient
Output of the regression models (subset of AnalysisResult for clarity).
*   `trait`: String.
*   `genre`: String.
*   `beta`: Float (Coefficient).
*   `std_error`: Float.
*   `t_stat`: Float.
*   `p_value`: Float.
*   `vif`: Float (Variance Inflation Factor).

## 2. Data Flow & Transformation

1.  **Ingestion**: Raw CSVs -> `data/raw/`.
2.  **Cleaning**:
    *   Remove rows with missing `user_id`, `trait` scores, or `listening_minutes`.
    *   Impute missing `age` (median), `gender` (mode), `country` (mode) OR drop if >10% missing.
    *   Map raw genre tags to standardized 10 categories.
    *   Hash `user_id`.
3.  **Merging**: Join Personality and Music data on `user_id`.
4.  **Aggregation**: If multiple entries per user/genre, sum `listening_minutes`.
5.  **Analysis**: Compute correlations and regressions.
6.  **Output**: Save `analysis_results.csv`, `coefficient_deltas.csv`, `results_report.csv`.

## 3. Constraints & Validations

*   **Uniqueness**: `user_id` must be unique in the merged dataset.
*   **Range**: Personality scores must be within the valid range of the instrument (e.g., 1-5).
*   **Non-Negative**: `listening_minutes` must be >= 0.
*   **Completeness**: No null values allowed in the final `analysis_results.csv` for `correlation_rho`, `p_value`, or `adjusted_p_value`.