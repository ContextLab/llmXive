# Implementation Plan: The Impact of Simulated Social Comparison on Self-Evaluation in Online Environments

**Branch**: `001-simulated-social-comparison` | **Date**: 2026-10-20 | **Spec**: specs/001-simulated-social-compariso/spec.md
**Input**: Feature specification from `/specs/001-simulated-social-compariso/spec.md`

## Summary

The project ingests a verified open Reddit comment dataset, extracts predictor features (`authenticity_score`, `engagement_proxy`, `exposure_level`) and the outcome variable (`self_eval_score`), then runs hierarchical OLS regression with interaction terms, Benjamini–Hochberg FDR correction, VIF collinearity diagnostics, demographic stratification, interaction visualizations, and a ±0.05 threshold sensitivity sweep. All computation is CPU‑only, streaming/sampling to stay ≤ 6 GB RAM.

**⚠️ Data Availability**: The required Reddit comment source is the verified HuggingFace dataset **allenai/reddit_comments** (https://huggingface.co/datasets/allenai/reddit_comments). It provides `subreddit`, `body`, `created_utc`, `author` (including `about` profile field) under a permissive license. The Data Availability Gate (Phase 0 Task 1) checks for this dataset and aborts with a structured mismatch report if the dataset does not meet the acceptance criteria (required fields, license, programmatic download).

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `nltk` (VADER), `spacy`, `matplotlib`, `seaborn`, `pyarrow`, `jsonschema`, `pytest` (versions pinned in `requirements.txt`)
- **Storage**: Files under `data/` (raw, processed, results) and `reports/`
- **Testing**: `pytest` — unit tests on synthetic fixtures + contract tests against `contracts/*.schema.yaml`
- **Target Platform**: Linux GitHub Actions runner (A modest number of CPU cores., ~7 GB RAM, no GPU)
- **Performance Goals**: full pipeline ≤ 6 h wall‑clock, peak RAM ≤ 6 GB (FR‑008, FR‑015, SC‑005)
- **Constraints**: CPU‑only; strict predictor/outcome stream separation (Constitution VI); all effects labeled “associational” (SC‑002)

## Constitution Check

| Principle | Check |
|-----------|-------|
| I. Reproducibility | Seeds pinned (`--seed 42` default); dataset fetched from a single canonical source once verified; all steps scripted, no manual intervention. |
| II. Verified Accuracy | No external citations beyond the verified dataset URL; all URLs are from the verified‑datasets block. |
| III. Data Hygiene | Checksums recorded for every file under `data/`; raw data never modified in place; PII scrubbing at ingestion (FR‑011). |
| IV. Single Source of Truth | `data/processed_features.csv` is the sole source of all predictor/outcome variables; `data/regression_results.csv` is the sole source of all model outputs; every figure traces to one row/block. |
| V. Versioning Discipline | Content hashes recorded; artifact changes update the project state timestamp. |
| VI. Distinct Data Stream Integrity | Predictors (`exposure_level`, `authenticity_score`, `engagement_proxy`) derived from community‑level exposure streams; `self_eval_score` derived exclusively from the user’s own comments. Enforced by code and unit tests. |
| VII. Demographic Stratification | Subgroup models, plots, tables reported (FR‑006, FR‑007, FR‑017); global fallback flagged if coverage insufficient. |

No violations requiring complexity tracking.

## Project Structure

```text
specs/001-the-impact-of-simulated-social-compariso/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── processed_features.schema.yaml
    └── regression_results.schema.yaml

src/
├── ingest/
│   └── reddit_ingest.py        # streaming ingestion, PII scrub, per‑user aggregation, profile metadata extraction
├── features/
│   └── extract_features.py     # exposure, authenticity, engagement, self‑eval, demographic proxies
├── analysis/
│   ├── moderation_regression.py  # hierarchical OLS, VIF, FDR, cluster‑robust SEs
│   └── sensitivity_sweep.py      # ±0.05 threshold sweep
├── viz/
│   └── demographic_plots.py    # interaction plots, correlation matrix, PDF report
└── utils/
    ├── stream_utils.py         # chunked processing, RAM guard
    └── power_check.py          # a priori power / subgroup N check
```

## Phase Mapping (FR/SC → Plan Tasks)

| Phase | Tasks | FR/SC addressed |
|-------|-------|------------------|
| **Phase 0 – Data Availability Gate & Ingestion** | 1. **Data Availability Gate**: verify presence of `allenai/reddit_comments` with required fields (`subreddit`, `body`, `created_utc`, `author.about`). Emit `data/availability_report.json` and exit non‑zero if missing.<br>2. Implement `reddit_ingest.py`: stream comments in chunks, scrub PII, **retain the `about` profile field** for demographics, aggregate per user → `data/raw_user_comments.parquet` (FR‑011, FR‑015).<br>3. Compute subreddit‑level aggregate activity within a 30‑day window → `data/subreddit_metadata.parquet` (community‑level stream, distinct from user stream). | FR‑011, FR‑013, FR‑015, SC‑001, SC‑005 |
| **Phase 1 – Feature Extraction** | 4. **Exposure Definition (operational)**: Identify *target subreddits* as the most active subreddits (by comment volume) in the 30‑day window. For each user, compute `exposure_level` as the proportion of total community comment volume in those target subreddits **that the community posted in**, not the user’s own posts. This yields a predictor stream distinct from the user’s own commenting behavior (FR‑013, Principle VI).<br>5. **Self‑selection covariate**: compute `subreddit_participation_count` – the number of target subreddits a user has posted in – and include it as a covariate to adjust for self‑selection bias (new covariate, documented in data‑model).<br>6. **Rule‑based authenticity classifier** (vulnerability‑marker lexicon) applied to exposure content → `authenticity_score` (FR‑001).<br>6.1 **Validation Sub‑task**: sample a representative set of exposure comments, manually annotate vulnerability markers, compute precision/recall; log results (methodology‑07d7dbc0).<br>7. **Engagement proxy**: average comment depth / thread participation count from exposure content (FR‑009).<br>8. **Self‑evaluation score**: VADER sentiment × first‑person pronoun ratio computed from the user’s own comments only (FR‑002, FR‑012, FR‑018).<br>9. **Demographic proxies**: extract age/gender keywords from the retained `about` profile field; compute coverage rates (FR‑017).<br>10. Write `data/processed_features.csv` conforming to `contracts/processed_features.schema.yaml`. | FR‑001, FR‑002, FR‑009, FR‑012, FR‑013, FR‑017, FR‑018, new self‑selection covariate, SC‑001 |
| **Phase 2 – Cleaning & Diagnostics** | 11. Missing‑data check (flag if any column > 10 % missing, SC‑001); median imputation + complete‑case sensitivity check.<br>12. Low‑variance detection (variance < 0.01) → skip interaction for that feature, log (FR‑014).<br>13. VIF computation for all predictors; flag VIF > 5.0 (FR‑005, SC‑004). | FR‑014, FR‑005, SC‑001, SC‑004 |
| **Phase 3 – Power & Hierarchical Regression** | 14. **A priori power check**: target the exposure × authenticity interaction in Model 3 (df₁ = 1, total predictors = 6 [including self‑selection covariate], α = 0.05, effect size f² = 0.15). Log a warning if estimated power < 0.80 but continue execution, flagging limited power in the results (methodology‑e6618bd2).<br>15. Hierarchical OLS via `statsmodels`: Model 1 (covariates) → Model 2 (+ main effects) → Model 3 (+ interactions) (FR‑003).<br>16. Apply Benjamini–Hochberg FDR across all hypothesis tests (FR‑004, SC‑003).<br>17. Use **cluster‑robust SEs by subreddit** to account for the fact that `exposure_level` is constant within a subreddit (scientific_soundness‑6946eb76).<br>18. Log that all effects are “associational” (SC‑002). | FR‑003, FR‑004, SC‑002, SC‑003 |
| **Phase 4 – Demographic Stratification** | 19. Fit Model 3 per subgroup (N ≥ 500); if proxy coverage < 10 %, fall back to global analysis and flag (FR‑006, FR‑017).<br>20. Record subgroup N and coverage tables. | FR‑006, FR‑017, SC‑005 |
| **Phase 5 – Visualization & Report** | 21. Interaction plots (≥ 2 subgroups), correlation matrix, subgroup tables → `reports/interaction_plots.pdf`; null results clearly annotated (FR‑007, SC‑007).<br>22. Assemble `data/regression_results.csv` conforming to `contracts/regression_results.schema.yaml` (FR‑018). | FR‑007, FR‑018, SC‑007 |
| **Phase 6 – Sensitivity Analysis** | 23. Sweep self‑reference and sentiment thresholds ±0.05; re‑run headline models; write `reports/sensitivity_summary.csv` (FR‑016, SC‑006). | FR‑016, SC‑006 |
| **Phase 7 – Reproducibility** | 24. Pin seeds and dependency versions; record checksums under `data/`; contract tests green. | SC‑001, SC‑005, Constitution I, III, V |

**Coverage audit**: All FR‑001…FR‑018 and SC‑001…SC‑007 are mapped to concrete tasks. No un‑specified constraints added. Power parameters and subgroup size thresholds are taken from the spec’s own assumptions.

## Limitations & Self‑Selection Note

The exposure definition uses community‑level activity in target subreddits; nevertheless, users self‑select which subreddits to participate in, introducing selection bias. To mitigate this, we (a) include `subreddit_participation_count` as a covariate, (b) report VIF diagnostics, and (c) discuss the limitation explicitly in the analysis logs and final report. Future work could incorporate propensity‑score weighting or external exposure measures if available.
