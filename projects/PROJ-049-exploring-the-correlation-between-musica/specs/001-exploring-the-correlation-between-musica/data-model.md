# Data Model: Exploring the Correlation Between Musical Preference and Personality Traits

## Entity Definitions

### 1. UserRecord
Represents a single participant in the study.
*   `user_id`: `string` (Unique identifier, hashed if PII was present)
*   `openness_score`: `float` (0.0 - 5.0 or 1.0 - 7.0 scale)
*   `conscientiousness_score`: `float`
*   `extraversion_score`: `float`
*   `agreeableness_score`: `float`
*   `neuroticism_score`: `float`
*   `age`: `integer`
*   `gender`: `string` (Categorical: Male, Female, Other, Prefer not to say)
*   `country`: `string` (ISO 3166-1 alpha-3 code or region name)

### 2. GenrePreference
Aggregated listening data per user per genre.
*   `user_id`: `string` (FK to UserRecord)
*   `genre_name`: `string` (One of: Rock, Pop, Hip-Hop, Classical, Electronic, Jazz, Folk, Country, Metal, Other)
*   `listening_minutes`: `float` (Total minutes listened)
*   `genre_score`: `float` (Normalized: `listening_minutes` / `total_user_minutes`)

### 3. AnalysisResult
Output of the statistical tests.
*   `trait`: `string` (One of the 5 Big Five traits)
*   `genre`: `string` (One of the 10 genres)
*   `correlation_rho`: `float` (Spearman's rho)
*   `p_value`: `float` (Raw p-value)
*   `adjusted_p_value`: `float` (Benjamini-Hochberg corrected)
*   `is_significant`: `boolean` (True if `adjusted_p_value` < 0.05)
*   `effect_size_r`: `float` (Pearson's r approximation)
*   `effect_size_fisher_z`: `float`
*   `ci_low`: `float` (95% CI lower bound)
*   `ci_high`: `float` (95% CI upper bound)
*   `effect_size_threshold_met`: `boolean` (True if `abs(effect_size_r) > 0.3`, per SC-001)
*   `beta_delta`: `float` (Change in regression coefficient when covariates are added, per SC-003)

## Data Flow

1.  **Raw Ingestion**: `raw_bfi.csv`, `raw_lastfm.csv` -> `data/raw/`
2.  **Cleaning & Mapping**:
    *   Apply Genre Lookup Table.
    *   Impute/Filter missing demographics.
    *   Aggregate `listening_minutes` by user/genre.
    *   Output: `data/processed/merged_dataset.csv` (UserRecord + GenrePreference joined).
3.  **Analysis**:
    *   Input: `merged_dataset.csv`.
    *   Process: Spearman Correlation, Linear Regression (with and without covariates), FDR Correction.
    *   Output: `data/processed/analysis_results.csv`, `data/processed/correlation_heatmap.png`, `data/processed/results_report.csv`.

## Constraints & Rules

*   **Genre Mapping**: All raw genre tags MUST be mapped to the 10 canonical categories. No raw tags allowed in `merged_dataset.csv`.
*   **Missing Data**: Rows with missing `user_id` are dropped. Rows with missing demographics are imputed or dropped (logged).
*   **Zero Listening**: Users with 0 total listening minutes are excluded prior to normalization.
*   **PII**: No raw names, emails, or exact locations. `user_id` is the only identifier.