# Data Model: The Impact of Incidental Music on Autobiographical Memory Retrieval

## 1. Entity Relationship Overview

The data model is designed to support the User-Track Pair aggregation (FR-004) and the subsequent mixed-effects modeling (FR-005).

### Core Entities

1.  **User**: Represents an individual participant.
    -   Attributes: `user_id`, `birth_year` (nullable), `birth_decade` (derived).
2.  **Track**: Represents a music track.
    -   Attributes: `track_id`, `track_name`, `release_date`, `popularity`, `artist_id`.
3.  **ListenEvent**: A single listening instance.
    -   Attributes: `user_id`, `track_id`, `listen_timestamp`.
4.  **MemoryCue**: A memory association between a user and a track.
    -   Attributes: `user_id`, `track_id`, `cue_text`, `vividness`, `valence`, `match_confidence` (Levenshtein score).

## 2. Aggregated Data Model (User-Track Pair)

The primary analysis dataset is the **User-Track Pair** (FR-004).

### Schema: `user_track_pair`

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| `user_id` | string | Unique user identifier | ListenEvent |
| `track_id` | string | Unique track identifier | ListenEvent, MemoryCue |
| `birth_year` | int | User's birth year (nullable) | User |
| `adolescent_exposure_ratio` | float | Ratio of listens during adolescence (0-15) to total listens | Calculated (FR-001) |
| `total_listens` | int | Total number of listens for this user-track pair | ListenEvent |
| `mean_vividness` | float | Average vividness rating (1-7 scale) | MemoryCue |
| `mean_valence` | float | Average valence rating (-3 to +3 scale) | MemoryCue |
| `n_cues` | int | Number of memory cues for this pair | MemoryCue |
| `popularity` | float | Track popularity score (0-100) | Track |
| `match_threshold` | int | Levenshtein threshold used for matching (1-5) | Config |
| `global_exposure_proxy` | float | Global exposure metric if birth_year is missing (FR-008) | Calculated |
| `is_excluded_from_primary` | boolean | True if user has missing birth year and is excluded from primary LMM | Derived |
| `is_simulated` | boolean | True if data is generated for prototype validation | Config |

### Derived Variables

-   **`adolescent_exposure_ratio`**:
    -   Calculation: `count(listens where listen_year in [birth_year, birth_year+15]) / count(all listens)`
    -   Fallback: If `birth_year` is missing, `adolescent_exposure_ratio` is set to `NaN` and `is_excluded_from_primary` is set to `True`.
-   **`birth_decade`**: `floor(birth_year / 10) * 10` (used for fallback grouping).
-   **`global_exposure_proxy`**:
    -   Calculation: Mean `adolescent_exposure_ratio` across all tracks in the user's birth decade (for users with missing birth year).
    -   Usage: **Descriptive only**. Not used as a predictor in the primary LMM.

## 3. Intermediate Data Models

### Ingested Cohort (`ingested_cohort`)
Raw data after initial cleaning and matching.
-   Contains `user_id`, `track_id`, `listen_timestamp`, `birth_year`, `cue_text`, `vividness`, `valence`, `match_score`.
-   Used to validate data quality (US-002, SC-004).

### Sensitivity Analysis Dataset
A collection of `user_track_pair` datasets, one for each Levenshtein threshold (1-5).
-   Stored as a list of DataFrames or separate Parquet files.

## 4. Output Data Models

### Regression Summary (`regression_summary.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `threshold` | int | Levenshtein threshold used |
| `coef_adolescent_exposure` | float | Coefficient for `adolescent_exposure_ratio` |
| `std_err` | float | Standard error of the coefficient |
| `t_stat` | float | T-statistic |
| `p_value` | float | P-value from LMM |
| `vif_exposure` | float | VIF for exposure variable |
| `vif_popularity` | float | VIF for popularity variable |
| `n_observations` | int | Number of User-Track pairs |
| `n_users` | int | Number of users |
| `is_simulated` | boolean | True if data is simulated |

### Bootstrap Results (`bootstrap_results.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `threshold` | int | Levenshtein threshold used |
| `observed_coef` | float | Observed coefficient from original model |
| `bootstrap_coef_mean` | float | Mean of bootstrap distribution |
| `bootstrap_coef_std` | float | Std dev of bootstrap distribution |
| `p_value_bootstrap` | float | Bootstrap p-value |
| `n_bootstraps` | int | Number of bootstraps (1000) |

### Selection Correction Results (`selection_correction.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `threshold` | int | Levenshtein threshold used |
| `coef_adolescent_exposure_corrected` | float | Coefficient after Heckman correction |
| `inverted_mills_ratio_coef` | float | Coefficient for the inverse Mills ratio |
| `p_value_corrected` | float | P-value after correction |

## 5. Data Quality Constraints

-   **Missing Birth Year**: If `birth_year` is null, `adolescent_exposure_ratio` is set to `NaN` and `is_excluded_from_primary` is set to `True`.
-   **Zero Variance**: Tracks with `n_cues` = 0 are filtered out (EC-002).
-   **Minimum Listens**: `total_listens` < 3 are filtered out (FR-009).
-   **Match Rate**: If match rate < 80%, a warning is logged (SC-004).
-   **Simulation Flag**: `is_simulated` is set to `True` for the prototype run.
