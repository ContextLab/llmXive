# Data Model: Exploring the Correlation Between Musical Preference and Personality Traits

## Core Entities

| Entity | Attributes | Description |
|--------|------------|-------------|
| **UserRecord** | `user_id` (string, hashed), `openness_score` (float 1‑5), `conscientiousness_score` (float 1‑5), `extraversion_score` (float 1‑5), `agreeableness_score` (float 1‑5), `neuroticism_score` (float 1‑5), `age` (int), `gender` (categorical: Male/Female/Other), `country` (categorical, grouped) | One row per participant after merging BFI‑2 and listening data. |
| **GenrePreference** | `user_id` (string), `genre_name` (categorical, one of several standardized categories), `listening_minutes` (float), `total_minutes` (float), `genre_proportion` (float = listening_minutes / total_minutes), `genre_score` (float = log10(genre_proportion + ε)) | Aggregated per‑user per‑genre listening metrics. Note: **Regression models will use `listening_minutes` (raw) as predictors**, while `genre_proportion` / `genre_score` are retained for correlation analyses. |
| **AnalysisResult** | `trait` (categorical), `genre` (categorical), `correlation_r` (float), `p_value` (float), `adjusted_p_value` (float), `is_significant` (bool), `beta` (float, regression coefficient), `std_error` (float), `cohens_d` (float), `ci_lower` (float), `ci_upper` (float) | One row per trait‑genre pair after analysis. |

## Relationships
- `UserRecord` 1‑to‑N `GenrePreference` (each user has up to 10 genre rows).  
- `GenrePreference` aggregates into `UserRecord` fields `total_minutes` and per‑genre `genre_score`.  
- `AnalysisResult` joins `UserRecord` traits with `GenrePreference` scores for statistical testing.

## Data Flow Diagram (high‑level)
1. **Raw BFI‑2 CSV** → `UserRecord` (personality + demographics).  
2. **Raw Last.fm parquet** → `GenrePreference` (listening minutes per raw tag).  
3. **Genre Mapping** (lookup table) → standardized `genre_name`.  
4. **Aggregation** → compute `total_minutes`, `genre_proportion`, `genre_score`.  
5. **Merge** on `user_id` → unified dataframe for analysis.  
6. **Statistical Modules** → produce `AnalysisResult` rows.  
7. **Reporting** → heatmap PNG + `results_report.csv`.

## Schema Contracts (refer to `contracts/processed_dataset.schema.yaml`)

- `merged_dataset.csv` must contain all columns from `UserRecord` plus `genre_name`, `listening_minutes`, `total_minutes`, `genre_proportion`, `genre_score`.  
- `analysis_results.csv` must match the `AnalysisResult` attribute list with correct types.  

---

