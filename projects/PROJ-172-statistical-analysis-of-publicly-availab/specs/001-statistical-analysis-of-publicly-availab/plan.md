# Implementation Plan: Statistical Analysis of Publicly Available Sports Data for Predictive Modeling

**Branch**: `001-sports-prediction` | **Date**: 2023-10-27 | **Spec**: `specs/001-sports-prediction/spec.md`

## Summary

This feature implements a reproducible, CPU-tractable statistical pipeline to evaluate whether advanced baseball metrics (wOBA, BABIP) provide predictive power for game outcomes beyond traditional statistics (AVG, ERA). The system ingests raw play-by-play data, engineers features with strict temporal integrity (train: early historical years, test: subsequent years)., trains three models (Logistic Regression, Random Forest, Gradient Boosting), and performs rigorous statistical significance testing (Diebold-Mariano/corrected t-test) and sensitivity analysis. 

**Critical Distinction**: This plan distinguishes between **Pipeline Validation** (testing code logic, data integrity, and statistical test implementation) and **Empirical Hypothesis Testing** (validating the scientific claim that advanced metrics add value). The pipeline can run with synthetic data for validation, but the empirical hypothesis requires verified real-world data. If real data is unavailable, the project halts the empirical claim and reports only pipeline validity.

The implementation adheres to the "free CPU-only CI" constraint (a limited number of CPU cores and constrained RAM) by sampling data where necessary and using CPU-optimized libraries.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `pandas`, `scikit-learn`, `xgboost` (CPU wheel), `statsmodels`, `requests`, `pyyaml`, `numpy`  
**Storage**: Local CSV/Parquet files (`data/`), JSON reports (`artifacts/`)  
**Testing**: `pytest` with `pytest-cov`  
**Target Platform**: Linux (GitHub Actions Free Runner)  
**Project Type**: Data Science Pipeline / CLI  
**Performance Goals**: End-to-end execution ≤ 6 hours on 2 vCPU, ≤ 7GB RAM.  
**Constraints**: No GPU; no large-LLM inference; strict temporal split (no data leakage); all datasets must be verified or simulated with documented logic.  
**Scale/Scope**: Multiple seasons of MLB game data; a substantial volume of rows after feature engineering.

> **Dataset Feasibility Note**: The spec requires Retrosheet and Baseball-Reference data. The "Verified datasets" block provided for this project **does not** contain verified URLs for Retrosheet or Baseball-Reference raw play-by-play data.
> *   **Action**: The plan will implement a `data_loader.py` that attempts to fetch data from the canonical Retrosheet/BR URLs. If these are blocked or rate-limited in the CI environment (common for raw scraping), the pipeline will fall back to a **synthetic/sampled generator** that mimics the statistical distribution of MLB data (verified against public aggregates) to ensure the pipeline logic (FR-001 to FR-006) is tested and reproducible without relying on unstable external scrapers.
> *   **Hypothesis Validity Gate**: If the fallback to synthetic data is triggered, the project **MUST** flag the empirical hypothesis as "Untested" in the final report. The synthetic data is used *only* to validate the pipeline code and statistical test logic, not to answer the research question. This satisfies the "Reproducibility" principle of the Constitution while acknowledging the lack of a verified raw data URL in the provided block and preventing scientific fallacy.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification Method |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds fixed for reproducibility.; `requirements.txt` pinned; data loader handles missing sources gracefully with synthetic fallback. *Note: Pipeline is reproducible; empirical results are conditional on data availability.* |
| **II. Verified Accuracy** | **PASS** | No external citations in code; dataset URLs restricted to the "Verified datasets" block or explicitly marked as "Synthetic Fallback" in `research.md`. *Note: If synthetic, we verify the generation logic against public aggregates, not the source URL.* |
| **III. Data Hygiene** | **PASS** | `data/` directory checksummed; raw data (if fetched) preserved; derivations written to new files. |
| **IV. Single Source of Truth** | **PASS** | All metrics derived from `data/` CSVs; no hand-typed stats in reports. |
| **V. Versioning Discipline** | **PASS** | Artifacts hashed; `state/` updated on change. *See "Versioning and Hashing" section for implementation details.* |
| **VI. Statistical Validity** | **PASS** | Plan includes Diebold-Mariano test, corrected resampled t-test, Nested Model Comparison, and effect sizes reported. |
| **VII. Temporal Integrity** | **PASS** | Explicit split: Train (≤2018), Test (2019-2022); no leakage allowed. |

## Data Source Fallback Protocol

To address FR-001 and the lack of verified URLs:
1.  **Attempt Fetch**: The `data_loader.py` will attempt to fetch from canonical Retrosheet/BR URLs.
2.  **Fallback Trigger**: If fetch fails (403, 429, timeout) or data integrity check fails, the system switches to **Synthetic Mode**.
3.  **Synthetic Mode**: Generates a statistically faithful dataset (see `research.md` for logic).
4.  **Reporting**: The final report will explicitly state: "Empirical Hypothesis Untested: Real data unavailable. Pipeline validated with synthetic data."
5.  **FR-001 Compliance**: This protocol satisfies the *functional* requirement of ingesting data for pipeline testing, while explicitly documenting the limitation for scientific claims.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Synthetic Data Fallback** | Verified URLs for Retrosheet/BR are missing in the provided block; raw scraping is brittle in CI. | Using a static "hello world" dataset would fail to test the *feature engineering* logic (wOBA/BABIP calculation) and temporal split rigor. The synthetic generator must mimic the statistical properties of real MLB data to validate the pipeline. **Crucially, results from synthetic data are labeled "Pipeline Validation Only" and do not constitute empirical findings.** |
| **Diebold-Mariano Test** | Standard t-tests are invalid for time-series cross-validation due to autocorrelation. | A standard paired t-test would violate Principle VI (Statistical Validity) by inflating Type I error rates. |
| **Nested Model Comparison** | Standard model comparison (LR vs. XGB) does not isolate the marginal gain of advanced metrics due to collinearity. | A simple comparison would conflate model architecture differences with feature set differences. Nested models isolate the specific contribution of wOBA/BABIP. |

## Project Structure

### Documentation (this feature)

```text
specs/001-sports-prediction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── model_output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-172-statistical-analysis-of-publicly-availab/
├── code/
│   ├── __init__.py
│   ├── config.py          # Paths, seeds, hyperparameters
│   ├── data_loader.py     # Ingestion (Retrosheet/BR + Synthetic Fallback)
│   ├── feature_engineering.py # wOBA, BABIP, temporal splits
│   ├── models.py          # LR, RF, XGB training & CV
│   ├── evaluation.py      # Metrics, Diebold-Mariano, Sensitivity, Nested Models
│   ├── checksum_manifest.py # Versioning and hashing logic
│   └── main.py            # Orchestrator
├── data/
│   ├── raw/               # Raw downloads (if successful) or synthetic
│   ├── processed/         # Cleaned CSVs
│   └── checksums.txt      # Manifest of hashes
├── artifacts/
│   ├── reports/           # JSON/CSV results
│   └── figures/           # Sensitivity plots
├── tests/
│   ├── test_feature_engineering.py
│   ├── test_temporal_split.py
│   └── test_statistical_tests.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `tests/`) chosen for simplicity and alignment with the "CLI/Data Pipeline" nature of the feature. No separate frontend/backend required.

## Versioning and Hashing

To satisfy Constitution Principle V:
1.  **Artifact Hashing**: A `checksum_manifest.py` script will be run after every data processing and modeling step. It computes SHA-256 hashes for all files in `data/processed/` and `artifacts/`.
2.  **State Update**: The script updates `state/projects/PROJ-172-.../current_stage.yaml` with the new hashes and `updated_at` timestamp.
3.  **Validation**: The `Advancement-Evaluator` agent will compare the current hashes against the state file. Any mismatch invalidates the stage transition.

## Task Ordering

1.  **Download/Generate**: `data_loader.py` (Fetch or Synthetic Gen).
2.  **Clean & Engineer**: `feature_engineering.py` (Compute wOBA/BABIP, Split, Completeness Check).
3.  **Train**: `models.py` (5-fold CV, Hyperparameter Tuning, Nested Models).
4.  **Evaluate**: `evaluation.py` (Test set metrics, Diebold-Mariano, Sensitivity, Completeness Report).
5.  **Report**: Generate JSON/CSV and plots.
6.  **Hash & State**: `checksum_manifest.py` updates state.