# Implementation Plan: The Impact of Simulated Social Comparison on Self-Evaluation in Online Environments

**Branch**: `001-simulated-social-comparison` | **Date**: 2026-10-20 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-simulated-social-comparison/spec.md`

## Summary
The project ingests public Reddit comment data, extracts predictor features (`authenticity_score`, `engagement_proxy`, `curated_aesthetic_score`, **exposure_level** proxy), and the outcome variable (`self_eval_score`), then runs hierarchical multiple regression with interaction terms, applies Benjamini‑FDR correction, checks collinearity (VIF), performs demographic‑stratified analyses, and produces visualizations. All steps run on CPU‑only resources, streaming or sampling data to stay ≤ 6 GB RAM.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `spacy`, `nltk`, `matplotlib`, `seaborn`, `datasets` (HuggingFace), `tqdm`  
- **Storage**: Files under `data/` (raw, intermediate, results)  
- **Testing**: `pytest` with contract validation (`jsonschema`)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM)  
- **Constraints**: CPU‑only (FR‑008), RAM ≤ 6 GB (FR‑015), strict stream separation (VI)  

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | Random seeds pinned; all external URLs fixed. |
| III. Data Hygiene | Checksums recorded; no in‑place mutation. |
| VI. Distinct Data Stream Integrity | Predictor features derived from **subreddit‑wide exposure statistics**; outcome (`self_eval_score`) derived exclusively from the user’s own comment stream. |
| VII. Demographic Stratification Requirement | Subgroup models and plots generated (FR‑006, FR‑007). |
| SSoT Declarations | `processed_features.csv` is the authoritative source for all predictor variables; `regression_results.csv` is the authoritative source for all model outputs. |

All principles satisfied; no violations.

## Project Structure
```text
specs/001-the-impact-of-simulated-social-comparison/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── regression_results.schema.yaml
    └── processed_features.schema.yaml

src/
├── ingest/
│   └── reddit_ingest.py
├── features/
│   └── extract_features.py
├── analysis/
│   └── moderation_regression.py
├── viz/
│   └── demographic_plots.py
└── utils/
    └── stream_utils.py

tests/
├── contract/
│   └── test_regression_schema.py
└── unit/
    └── test_feature_extraction.py
```

## Phase Mapping (FR → Plan Tasks)

| Phase | Tasks | FR IDs addressed |
|-------|-------|-------------------|
| **Phase 0 – Data Ingestion & PII Scrubbing** | 1. Download Pushshift Reddit dump via `datasets.load_dataset(..., streaming=True)`<br>2. Stream comments, drop PII fields (`author`, `author_flair`), keep `subreddit`, `body`, `created_utc`<br>3. Aggregate per `user_id` → `raw_user_comments.parquet`<br>4. **Download subreddit‑level metadata** (comment counts per subreddit) for exposure calculations. | FR‑011, FR‑015 |
| **Phase 1 – Feature Extraction** | 5. Compute **exposure_level**: a **subreddit‑wide exposure proxy** representing the weighted average of overall subreddit comment volume for subreddits a user has posted in (derived from the subreddit metadata aggregated across all users, not from the user’s own comment stream). This satisfies Principle VI by ensuring the predictor originates from an independent exposure stream. (FR‑013, revised)<br>6. Rule‑based authenticity classifier (vulnerability markers) → `authenticity_score` (FR‑001)<br>7. Engagement proxy: average comment depth / thread participation → `engagement_proxy` (FR‑009)<br>8. Curated aesthetic detection (markdown, image links) → `curated_aesthetic_score` (FR‑010)<br>9. **Self‑evaluation**: Sentiment (VADER) + first‑person pronoun ratio **computed ONLY from the user’s own comment stream** → `self_eval_score` (FR‑002, VI)<br>10. Additional covariates: total comment count, subreddit popularity score, month of activity, baseline sentiment (new covariates) (addresses methodology‑4e1e7c28)<br>11. Write `processed_features.csv` adhering to `contracts/processed_features.schema.yaml` (new contract) (FR‑012) | FR‑001, FR‑002, FR‑009, FR‑010, FR‑012, FR‑013, added covariates |
| **Phase 2 – Data Cleaning & Validation** | 12. Verify no missing >10 % in any column (SC‑001).<br>13. Median imputation for any residual missing values; run a complete‑case sensitivity check (addressing methodology‑dc3a607e).<br>14. Low‑variance check (variance < 0.01) → skip interaction, log (FR‑014)<br>15. Compute VIF for all predictors (FR‑005) | FR‑014, FR‑005, SC‑004 |
| **Phase 3 – Power Analysis & Hierarchical Regression** | 16. Perform a priori power analysis (f² = 0.15, α = 0.05, power = 0.80) → required N≈400 per subgroup; if N < 500 log power limitation (methodology‑19fcf0e1).<br>17. Fit Model 1 (main effects) → Model 2 (add exposure) → Model 3 (add interactions) using `statsmodels` OLS.<br>18. Extract coefficients, p‑values, interaction terms.<br>19. Apply Benjamini‑Hochberg FDR to all tested hypotheses (FR‑004) | FR‑003, FR‑004, SC‑003 |
| **Phase 4 – Demographic Stratification** | 20. Infer demographic proxies (age, gender) via keyword extraction from users’ comment text (e.g., “19M”, “female”) – no external profile metadata required (addresses data_resources‑76a00e9c).<br>21. If proxy coverage <10 % → fall back to global analysis and flag (FR‑017).<br>22. For each subgroup with N ≥ 500, repeat Model 3 (FR‑006).<br>23. Record subgroup sample sizes & coverage rates. | FR‑006, FR‑017, SC‑005 |
| **Phase 5 – Visualization & Reporting** | 24. Generate interaction plots per subgroup (Matplotlib/Seaborn) (FR‑007)<br>25. Assemble `regression_results.csv` conforming to `contracts/regression_results.schema.yaml` (FR‑018)<br>26. Produce PDF report with tables & plots | FR‑007, FR‑018 |
| **Phase 6 – Sensitivity Analysis** | 27. Sweep self‑reference and sentiment thresholds ±0.05, re‑run regression, record effect size variation (FR‑016) | FR‑016, SC‑006 |
| **Phase 7 – Reproducibility & Packaging** | 28. Pin random seeds, write `requirements.txt`, store checksums, write `README` with quickstart (SC‑001) | All SCs |

Total tasks: 28 (grouped into 7 phases). No extraneous scaffolding tasks.

---



## projects/PROJ-389-the-impact-of-simulated-social-compariso/specs/001-the-impact-of-simulated-social-compariso/quickstart.md===
# Quickstart: The Impact of Simulated Social Comparison on Self-Evaluation in Online Environments

This guide walks a new researcher from a fresh GitHub Actions runner to a complete PDF report.

## 1️⃣ Setup
```bash
# Clone the repo (already done in CI)
cd projects/PROJ-389-the-impact-of-simulated-social-compariso

# Create virtualenv and install pinned deps
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2️⃣ Data Download & Pre‑processing
```bash
python -m src.ingest.reddit_ingest \
    --streaming \
    --output data/raw_user_comments.parquet
```
- Streams the Pushshift Reddit dump, removes PII, aggregates per user.

## 3️⃣ Feature Extraction
```bash
python -m src.features.extract_features \
    --input data/raw_user_comments.parquet \
    --subreddit-metadata data/subreddit_metadata.parquet \
    --output data/processed_features.csv \
    --seed 42
```
- Generates all predictor columns **and** the additional covariates (total comment count, subreddit popularity score, month of activity).  
- **Important**: `exposure_level` is computed from **subreddit‑wide metadata** (global comment volume per subreddit), **not** from the user’s own comment stream, satisfying Principle VI.  
- `self_eval_score` is computed **only from the user’s own comments**.  
- Logs low‑variance skips, median‑imputes any residual missing values, and writes a `notes` column.  

## 4️⃣ Power Check (optional)
```bash
python -m src.utils.power_check \
    --features data/processed_features.csv \
    --target_n 500 \
    --effect_size 0.15
```
- Reports whether each demographic subgroup meets the ≥ 500 sample‑size requirement; logs a power‑limitation warning if not.

## 5️⃣ Regression & Diagnostics
```bash
python -m src.analysis.moderation_regression \
    --features data/processed_features.csv \
    --results data/regression_results.csv \
    --seed 42
```
- Fits hierarchical models, computes VIF, applies Benjamini‑Hochberg FDR, writes results conforming to `contracts/regression_results.schema.yaml`.

## 6️⃣ Demographic Stratification & Plots
```bash
python -m src.viz.demographic_plots \
    --results data/regression_results.csv \
    --output reports/interaction_plots.pdf
```
- Produces interaction plots for each subgroup **with ≥ 500 users**; if demographic proxies are insufficient, the script falls back to a global plot and notes the limitation.

## 7️⃣ Sensitivity Analysis (optional)
```bash
python -m src.analysis.sensitivity_sweep \
    --features data/processed_features.csv \
    --output reports/sensitivity_summary.csv
```
- Sweeps self‑reference and sentiment thresholds ±0.05 and reports variation in headline moderation effect sizes.

## 8️⃣ Verify Contracts
```bash
pytest -q tests/contract/test_regression_schema.py
```
- Ensures `regression_results.csv` matches the JSON‑Schema contract.

## 9️⃣ Final Report
All artifacts are now in `reports/`. Open `reports/interaction_plots.pdf` and `reports/sensitivity_summary.csv` for the complete results.

**All steps complete within the CI runner limits** (≤ 6 h, ≤ 6 GB RAM).

---



## projects/PROJ-389-the-impact-of-simulated-social-compariso/specs/001-the-impact-of-simulated-social-compariso/data-model.md===
# Data Model: The Impact of Simulated Social Comparison on Self-Evaluation in Online Environments

## Overview
The pipeline produces three core artifacts that are validated against JSON‑Schema contracts located in `contracts/`.

| Artifact | Description | Format | Contract |
|----------|-------------|--------|----------|
| `raw_user_comments.parquet` | Aggregated per‑user comment stream (exposure content only). | Parquet | N/A (raw source) |
| `processed_features.csv` | One row per `user_id` with all predictor variables, additional covariates, and `self_eval_score`. The predictor `exposure_level` is derived from **subreddit‑wide metadata** (global comment volume) and is therefore independent of the user’s own comment stream, satisfying Principle VI. | CSV | `contracts/processed_features.schema.yaml` |
| `regression_results.csv` | Results of hierarchical regression, including interaction coefficients, corrected p‑values, VIF scores, and subgroup metadata. | CSV | `contracts/regression_results.schema.yaml` |

## Processed Features Schema (`contracts/processed_features.schema.yaml`)
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Processed Features"
type: object
required:
  - user_id
  - exposure_level
  - authenticity_score
  - engagement_proxy
  - curated_aesthetic_score
  - self_eval_score
properties:
  user_id:
    type: string
    description: "Unique Reddit user identifier"
  exposure_level:
    type: number
    description: "Weighted subreddit‑wide exposure proxy (0‑1) derived from subreddit‑level comment volume, not from the user’s own comments (distinct stream)"
  authenticity_score:
    type: number
    description: "Rule‑based vulnerability‑marker score (0‑1)"
  engagement_proxy:
    type: number
    description: "Average comment depth or thread participation count"
  curated_aesthetic_score:
    type: number
    description: "Fraction of comments containing markdown formatting or image links"
  self_eval_score:
    type: number
    description: "Sentiment‑adjusted first‑person pronoun ratio derived from the user’s own comments"
  total_comment_count:
    type: integer
    description: "Total number of comments authored by the user"
  subreddit_popularity_score:
    type: number
    description: "Aggregate popularity (comment count) of subreddits the user posted in"
  month_of_activity:
    type: integer
    description: "Month (1‑12) of the dominant activity period for the user"
  demographic_proxy:
    type: string
    description: "Derived demographic label (e.g., \"young_female\", \"older_male\", \"unknown\")"
  notes:
    type: string
    description: "Optional log notes (e.g., low‑variance skip flag, imputation flag)"
```

## Regression Results Schema (`contracts/regression_results.schema.yaml`)
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Regression Results"
type: object
required:
  - model_id
  - subgroup
  - coefficients
  - p_values
  - corrected_p_values
  - interaction_term_significant
  - vif_scores
  - sample_size
properties:
  model_id:
    type: string
    description: "Identifier for the regression model (e.g., \"model3_interaction\")"
  subgroup:
    type: string
    description: "Demographic subgroup label (\"global\" if no stratification)"
  coefficients:
    type: object
    description: "Mapping from predictor name to estimated coefficient"
    additionalProperties:
      type: number
  p_values:
    type: object
    description: "Raw p‑values for each predictor"
    additionalProperties:
      type: number
  corrected_p_values:
    type: object
    description: "Benjamini‑Hochberg FDR‑adjusted p‑values"
    additionalProperties:
      type: number
  interaction_term_significant:
    type: boolean
    description: "True if the interaction term's corrected p‑value < 0.05"
  vif_scores:
    type: object
    description: "Variance Inflation Factor for each predictor"
    additionalProperties:
      type: number
  sample_size:
    type: integer
    description: "Number of observations used in this regression"
  notes:
    type: string
    description: "Optional free‑text notes (e.g., low‑variance skip, collinearity warning)"
```

All schemas are single‑document YAML files with quoted strings where needed.

---



## projects/PROJ-389-the-impact-of-simulated-social-compariso/specs/001-the-impact-of-simulated-social-compariso/contracts/processed_features.schema.yaml===
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Processed Features"
type: object
required:
  - user_id
  - exposure_level
  - authenticity_score
  - engagement_proxy
  - curated_aesthetic_score
  - self_eval_score
properties:
  user_id:
    type: string
    description: "Unique Reddit user identifier"
  exposure_level:
    type: number
    description: "Weighted subreddit‑wide exposure proxy (0‑1) derived from subreddit‑level comment volume, not from the user’s own comments (distinct stream)"
  authenticity_score:
    type: number
    description: "Rule‑based vulnerability‑marker score (0‑1)"
  engagement_proxy:
    type: number
    description: "Average comment depth or thread participation count"
  curated_aesthetic_score:
    type: number
    description: "Fraction of comments containing markdown formatting or image links"
  self_eval_score:
    type: number
    description: "Sentiment‑adjusted first‑person pronoun ratio derived from the user’s own comments"
  total_comment_count:
    type: integer
    description: "Total number of comments authored by the user"
  subreddit_popularity_score:
    type: number
    description: "Aggregate popularity (comment count) of subreddits the user posted in"
  month_of_activity:
    type: integer
    description: "Month (1‑12) of the dominant activity period for the user"
  demographic_proxy:
    type: string
    description: "Derived demographic label (e.g., \"young_female\", \"older_male\", \"unknown\")"
  notes:
    type: string
    description: "Optional log notes (e.g., low‑variance skip flag, imputation flag)"