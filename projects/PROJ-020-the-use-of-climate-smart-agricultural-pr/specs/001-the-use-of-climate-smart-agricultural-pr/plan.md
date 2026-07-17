# Implementation Plan: The Use of Climate-Smart Agricultural Practices in Rural Areas to Improve Food Security and Livelihoods

**Branch**: `001-csa-food-security` | **Date**: 2024-05-21 | **Spec**: `specs/001-csa-food-security/spec.md`
**Input**: Feature specification from `/specs/001-csa-food-security/spec.md`

## Summary

This project implements a statistical analysis pipeline to quantify the associational relationships between Climate-Smart Agricultural (CSA) practice adoption and food security (measured by Household Dietary Diversity Score, HDDS) in Kenya, India, and Vietnam. The technical approach involves downloading LSMS microdata, FAOSTAT agricultural indicators (for context only), and NASA POWER climate data, merging them spatially (at a moderate resolution) and temporally, constructing a weighted CSA index that **includes digital-technology access and finance access variables** as mandated by FR-003, and fitting a **Fixed-Effects Regression model** (OLS with Country Dummies) to account for unobserved heterogeneity. A Fixed-Effects model is chosen over Mixed-Effects because estimating random effect variance with only 3 countries (N=3) is statistically invalid. The pipeline includes rigorous diagnostics (VIF, Bonferroni correction), robustness checks (leave-one-country-out, sensitivity analysis), and visualization generation, all constrained to run within the GitHub Actions free-tier (CPU-first).

## Technical Context

**Language/Version**: Python 3.x (Source: History of Python, https://en.wikipedia.org/wiki/History_of_Python).
*Note: The Spec and Verified Facts mandate a recent, stable version of Python. The implementation MUST use this exact version. No fallback is permitted.*

**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `geopandas`, `requests`, `huggingface_hub`, `matplotlib`, `seaborn`, `worldbank-lsms`.
**Storage**: Local file system (GitHub Actions runner), intermediate CSV/Parquet files in `data/`.
**Testing**: `pytest` (unit tests for data ingestion, model fitting logic).
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, 7 GB RAM).
**Project Type**: Data Science / Statistical Analysis Pipeline.
**Performance Goals**: Complete full pipeline (download, merge, model, viz) within 6 hours; handle timeouts via reduced-batch retry ([deferred] reduction, then [deferred]).
**Constraints**:
- Memory: ≤ 7 GB RAM (stratified sampling if raw > 7GB).
- Disk: ≤ 14 GB (streaming or incremental processing).
- Time: ≤ 6 hours (with retry logic).
- No causal claims (associational only).
- Bonferroni correction for >5 hypotheses.
**Scale/Scope**: Target N ≥ 5000 households per country (if available); otherwise proceed with available data and log a warning (do not fail).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Check Status | Notes |
|-----------|--------------|-------|
| **I. Reproducibility** | PASS | All seeds pinned; `requirements.txt` provided; data sources are canonical (LSMS, FAOSTAT, NASA). |
| **II. Verified Accuracy** | PASS | Citations will be validated against primary sources; no fabricated URLs used (LSMS/FAOSTAT/NASA URLs handled per "Verified datasets" block). |
| **III. Data Hygiene** | PASS | Checksums recorded; no in-place modification; PII scan in CI. |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to `data/` and `code/`; no hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Content hashes for artifacts; `updated_at` timestamp updated on change. |
| **VI. Survey Data Integrity** | PASS | LSMS variables linked to original questionnaire IDs; provenance logs for derived CSA index. |
| **VII. Socioeconomic Impact** | PASS | Mediation/moderation analysis (digital/finance) planned. These variables are **included in the CSA Index** as per FR-003 and also tested as moderators to satisfy Principle VII. |

## Project Structure

### Documentation (this feature)

```text
specs/001-csa-food-security/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/
├── data/
│   ├── raw/             # Downloaded raw files (LSMS, FAOSTAT, NASA)
│   ├── processed/       # Merged, cleaned, sampled datasets
│   └── checksums.txt    # SHA256 checksums
├── code/
│   ├── __init__.py
│   ├── config.py        # Paths, seeds, thresholds
│   ├── ingestion.py     # Download and merge logic
│   ├── preprocessing.py # Imputation, sampling, index construction
│   ├── modeling.py      # Fixed-Effects Regression, diagnostics
│   ├── robustness.py    # LOCO, sensitivity analysis
│   ├── viz.py           # Plot generation
│   └── main.py          # Orchestration script
├── tests/
│   ├── test_ingestion.py
│   ├── test_modeling.py
│   └── test_viz.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen for simplicity and direct data flow. `data/` is separated into `raw` and `processed` to enforce data hygiene (Principle III). `code/` is modularized by task (Ingestion, Preprocessing, Modeling, Robustness, Viz) to ensure testability and maintainability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Fixed-Effects Regression** | Data is hierarchical (households nested in countries), but N=3 countries makes Mixed-Effects invalid. | Standard OLS would ignore clustering, inflating Type I errors. Mixed-Effects with N=3 is statistically invalid (singular fit). Fixed-Effects with Country Dummies is the statistically sound alternative. |
| **Stratified Sampling** | Raw LSMS data may exceed 7 GB RAM. | Random sampling could lose regional representation; stratified preserves structure. |
| **Bonferroni Correction** | >5 hypotheses tested (CSA, digital, finance, interactions). | Standard p-values would inflate family-wise error rate. |
| **Provenance Logging** | Constitution Principle VI requires traceability to questionnaire IDs. | Aggregated indices without provenance violate survey data integrity rules. |
| **Timeout Retry** | FR-010 requires a retry mechanism. | A defined retry logic (reduce by [deferred], then [deferred]) is deterministic and testable. |
| **Sensitivity Range (0.2-0.8)** | FR-007 requires sweeping thresholds. | A defined range (0.2 to 0.8, step 0.1) is deterministic and testable. |
| **N < 5000 Warning** | Edge Cases require proceeding with available data. | A hard failure would violate the resilience requirement; a warning is appropriate. |