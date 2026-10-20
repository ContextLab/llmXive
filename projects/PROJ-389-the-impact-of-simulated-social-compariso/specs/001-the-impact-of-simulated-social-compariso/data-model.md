# Data Model: The Impact of Simulated Social Comparison on Self-Evaluation in Online Environments

## Overview

| Artifact | Description | Format | Contract |
|----------|-------------|--------|----------|
| `data/availability_report.json` | Output of the Data Availability Gate: required variables, candidate sources checked, verdict. | JSON | N/A |
| `data/raw_user_comments.parquet` | PII‑scrubbed, per‑user aggregated comment stream (includes retained `about` profile field for demographics). | Parquet | N/A (raw) |
| `data/subreddit_metadata.parquet` | Community‑level comment‑volume aggregates per subreddit within the designated observation window (predictor stream). | Parquet | N/A (intermediate) |
| `data/processed_features.csv` | One row per `user_id`: predictors, covariates, `self_eval_score`, demographic proxy, and self‑selection metric. | CSV | `contracts/processed_features.schema.yaml` |
| `data/regression_results.csv` | Hierarchical regression outputs: coefficients, raw/FDR‑corrected p‑values, VIF, subgroup metadata. | CSV (JSON‑encoded object columns) | `contracts/regression_results.schema.yaml` |
| `reports/interaction_plots.pdf` | Interaction plots, correlation matrix, subgroup tables. | PDF | N/A |
| `reports/sensitivity_summary.csv` | Summary of the ±0.05 threshold sensitivity sweep (effect‑size variations per interaction). | CSV | N/A |

## Stream Separation (Constitution VI)

- **Predictor stream** (exposure/community content): `exposure_level`, `authenticity_score`, `engagement_proxy`, `subreddit_participation_count` — derived from subreddit‑level aggregates and exposure content, never from the user's own comments.
- **Outcome stream**: `self_eval_score` — derived exclusively from the user's own comments.
- Enforced in code (`extract_features.py` accepts the two streams as separate inputs) and by unit test `test_stream_separation.py` (FR‑012, FR‑018).

## Key Schemas

`contracts/processed_features.schema.yaml` — one row per user: `user_id`, `exposure_level`, `authenticity_score`, `engagement_proxy`, `self_eval_score` (required), plus covariates (`total_comment_count`, `subreddit_popularity_score`, `month_of_activity`, `subreddit_participation_count`), `demographic_proxy`, `notes`. **`baseline_sentiment` has been removed** to satisfy FR‑018.

`contracts/regression_results.schema.yaml` — one row per (model, subgroup): `model_id`, `subgroup`, `coefficients`, `p_values`, `corrected_p_values`, `interaction_term_significant`, `vif_scores`, `sample_size`, `inference_framing` (always “associational”), `notes`.

Both contracts are single‑document YAML files; object‑valued columns are serialized as JSON strings in the CSV and validated after parsing.
