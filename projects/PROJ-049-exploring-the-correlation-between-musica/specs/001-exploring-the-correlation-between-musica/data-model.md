# Data Model: Exploring the Correlation Between Musical Preference and Personality Traits

## Core Entities

| Entity | Attributes | Description |
|--------|------------|-------------|
| **UserRecord** | `user_id_hashed` (str), `openness` (float), `conscientiousness` (float), `extraversion` (float), `agreeableness` (float), `neuroticism` (float), `age` (int), `gender` (str), `country` (str) | One row per participant after merging personality and listening data. |
| **GenrePreference** | `user_id_hashed` (str), `genre` (enum, multiple categories + Other), `listening_minutes` (float), `total_minutes` (float), `listening_proportion` (float), `log_proportion` (float) | Aggregated listening data per user‑genre after preprocessing. |
| **AnalysisResult** | `trait` (enum), `genre` (enum), `correlation_r` (float), `p_value` (float), `adjusted_p_value` (float), `is_significant` (bool), `cohens_d` (float), `ci_lower` (float), `ci_upper` (float), `high_correlation_flag` (bool), `beta_baseline` (float), `beta_full` (float), `delta` (float), `vif` (float) | One row per trait‑genre pair representing the final statistical output. |

## Relationships
- **One‑to‑many**: Each `UserRecord` links to up to 10 `GenrePreference` rows (one per genre).  
- **Derived**: `AnalysisResult` is computed from the join of `UserRecord` and `GenrePreference`.

## Persisted Files
| Path | Format | Contents |
|------|--------|----------|
| `data/raw/personality_music_openml.arff` | ARFF | Original OpenML download (unchanged). |
| `data/processed/merged_clean.csv` | CSV | Post‑merge, cleaned, imputed dataset; columns match `UserRecord` + `GenrePreference`. |
| `data/processed/analysis_results.csv` | CSV | Table of `AnalysisResult` rows (used for reporting). |
| `data/processed/synthetic_data.csv` | CSV | Deterministic synthetic dataset for contract tests (Task T008). |
| `data/processed/coefficient_deltas.csv` | CSV | Trait‑genre β baseline, β full, delta, VIF, and validity status (Task T034). |
| `results/correlation_heatmap.png` | PNG | Heatmap of Pearson *r* values. |
| `results/regression_coefficients.png` | PNG | Bar chart of regression β coefficients per trait. |
| `results/diagnostics_linearity.png` | PNG | Scatter plots for linearity checks. |
| `results/diagnostics_residuals.png` | PNG | Q‑Q plot & residual histogram. |
| `results/diagnostics_heteroscedasticity.png` | PNG | Breusch‑Pagan test plot. |
| `results/diagnostics_vif.png` | PNG | VIF heatmap. |
| `results/results_report.csv` | CSV | Final report with effect sizes, CIs, and significance labels. |

## Validation Contracts
- `contracts/dataset.schema.yaml` defines required columns and types for the **raw combined** OpenML dataset.
- `contracts/processed_dataset.schema.yaml` defines required columns and types for `merged_clean.csv`.
- `contracts/analysis_output.schema.yaml` defines required columns for `analysis_results.csv`.
- `contracts/results.schema.yaml` defines required columns for `coefficient_deltas.csv`.
- `contracts/report.schema.yaml` defines required columns for `results_report.csv`.

---



