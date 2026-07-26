# Data Model: Exploring the Correlation Between Musical Preference and Personality Traits

## Core Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **UserRecord** | One participant with personality and demographics. | `user_id` (hashed string), `openness`, `conscientiousness`, `extraversion`, `agreeableness`, `neuroticism`, `age`, `gender`, `country`, `education`, `ses`, `total_listening_minutes` |
| **GenrePreference** | Aggregated listening for a single genre per user. | `user_id`, `genre` (standardized), `listening_minutes`, `log_minutes` |
| **MergedRecord** | Join of `UserRecord` and `GenrePreference` (one row per user‑genre). | All fields from `UserRecord` + `genre`, `listening_minutes`, `log_minutes`, `genre_prop_*`, `genre_log_*` |
| **AnalysisResult** | Output of statistical testing for a trait‑genre pair. | `trait` (enum), `genre` (enum), `correlation_rho`, `p_value`, `adjusted_p_value`, `is_significant`, `cohens_d`, `ci_lower`, `ci_upper`, `high_correlation_flag`, `beta_baseline`, `beta_full`, `delta`, `vif` |

## File Schemas

- **Raw BFI‑2** – `data/raw/bfi2.csv` (columns: `user_id`, five trait scores, `age`, `gender`, `country`, `education`, `ses`).  
- **Raw Listening** – `data/raw/lastfm_listening.csv` (columns: `user_id`, `raw_genre_tag`, `listening_minutes`).  
- **Processed Merged** – `data/processed/merged_dataset.csv` (conforms to `contracts/merged_dataset.schema.yaml`).  
- **Analysis Results** – `data/processed/analysis_results.csv` (conforms to `contracts/analysis_results.schema.yaml`).  
- **Coefficient Deltas** – `data/processed/coefficient_deltas.csv` (conforms to `contracts/analysis_output.schema.yaml`).  

All CSVs are encoded in a UTF format, are comma‑separated, and include a header row.

## Relationships
- `UserRecord` 1‑to‑N `GenrePreference` (each user may have multiple genre rows).  
- `MergedRecord` is a materialized view used for correlation/regression.

---


