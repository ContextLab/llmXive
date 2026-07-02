# Implementation Plan: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

**Branch**: `001-doomscrolling-anxiety` | **Date**: 2026-06-25 | **Spec**: `specs/001-doomscrolling-anxiety/spec.md`
**Input**: Feature specification from `/specs/001-doomscrolling-anxiety/spec.md`

## Summary

This project implements a statistical analysis pipeline to determine if the frequency of negative news consumption on social media predicts elevated anxiety scores, independent of baseline anxiety and demographics. The approach involves ingesting a public survey dataset, performing strict data hygiene, verifying construct validity to avoid mathematical coupling, fitting a multiple linear regression model with diagnostic checks, and generating visualizations. 

**Critical Methodological Note**: All findings are framed as **associational** only. No causal claims will be made due to the observational nature of the data. The pipeline is designed to run entirely on CPU within GitHub Actions free-tier constraints (limited CPU and memory).

> **Spec Consistency Note**: The source `spec.md` currently contains assumptions (e.g., "Hard Stop at N < 30", "robustness check if r > 0.3") that contradict the revised, scientifically rigorous methodology adopted in this plan (Hard Stop at N < 130, unconditional robustness check). This plan implements the rigorous methodology and flags the spec for correction in the `spec_coverage` review phase.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, statsmodels, scikit-learn, matplotlib, seaborn, requests, pyyaml  
**Storage**: Local filesystem (`data/`, `outputs/`)  
**Testing**: pytest (unit tests for data cleaning logic, integration tests for model fitting)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Data Analysis / Statistical Research  
**Performance Goals**: Complete analysis on ~10k records in < 60 seconds; < 7GB RAM usage.  
**Constraints**: No GPU; no heavy LLM inference; strict adherence to listwise deletion for missing data; must halt if N < 130.  
**Scale/Scope**: Single dataset ingestion, one primary regression model, one robustness check, two plots.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds (`np.random.seed(42)`, `statsmodels` defaults) will be pinned. Data ingestion will use fixed URLs. `requirements.txt` will pin versions. |
| **II. Verified Accuracy** | **WARN** | The process of verification is followed, but current verified URLs point to text datasets, not survey data. The pipeline will halt with a clear error if no valid source is found. |
| **III. Data Hygiene** | **PASS** | Raw data will be downloaded to `data/raw/` and checksummed. Cleaned data will be written to `data/processed/` with derivation logs. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final output will be generated programmatically from the `data/processed/` artifacts. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes will be generated for all `data/` and `code/` artifacts. |
| **VI. Ethical Human-Subjects** | **PASS** | The pipeline will only process public, anonymized survey data. No PII handling logic is required beyond ensuring no accidental leakage. |
| **VII. Psychometric Validity** | **PASS** | The `research.md` will explicitly map variables to validated scales (e.g., STAI) or flag proxies (general anxiety) as per FR-008. |

## Project Structure

### Documentation (this feature)

```text
specs/001-doomscrolling-anxiety/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-540-the-influence-of-social-media-doomscroll/
├── data/
│   ├── raw/             # Downloaded parquet/csv files
│   └── processed/       # Cleaned, analysis-ready datasets
├── code/
│   ├── __init__.py
│   ├── ingest.py        # Data download and parsing (FR-001)
│   ├── clean.py         # Missing data handling (FR-002)
│   ├── validity.py      # Construct validity & coupling check (New)
│   ├── model.py         # Regression fitting and diagnostics (FR-003, FR-004, FR-007)
│   ├── robustness.py    # Subset analysis (FR-006)
│   ├── viz.py           # Plot generation (FR-005)
│   └── main.py          # Orchestration script
├── tests/
│   ├── test_ingest.py
│   ├── test_clean.py
│   └── test_model.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. The scope is a linear data pipeline (Ingest -> Clean -> Validate -> Model -> Visualize). No complex microservices or separate frontend/backend is required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project is strictly scoped to a single regression analysis with one robustness check. | N/A |

## Implementation Phases

### Phase 0: Data Availability Check (New)
**Goal**: Verify that a valid dataset exists before proceeding.
1.  **Action**: Attempt to load the verified dataset URLs.
2.  **Check**: Validate schema against `contracts/dataset.schema.yaml`.
3.  **Logic**: 
    - If schema matches: Proceed to Phase 1.
    - If schema mismatch (e.g., text dataset): **HALT**. Log `ERROR: Dataset schema mismatch. Verified sources do not contain required variables.`
4.  **Constitution**: Addresses Principle II (Verified Accuracy) by preventing execution on invalid data.

### Phase 1: Data Ingestion & Cleaning
**Goal**: Prepare the analysis dataset.
1.  **Ingest**: Download raw data (FR-001).
2.  **Clean**: Perform listwise deletion for missing predictor/outcome values (FR-002).
3.  **Power Check**: 
    - Calculate N.
    - If N < 130: **HALT**. Raise `PowerLimitationError`. Log `ERROR: Power limitation. N < 130 (required for 5 predictors, medium effect).`
 - If 130 <= N < 200: Log `WARNING: Low Power ([deferred] < Power < 80%).`
4.  **Output**: `data/processed/analysis_data.csv`.

### Phase 1.5: Construct Validity & Coupling Check (New)
**Goal**: Ensure `baseline_anxiety` and `anxiety_score` are distinct constructs.
1.  **Action**: Check metadata or variable descriptions to confirm distinct instruments/time points.
2.  **Logic**: 
    - If same instrument/time point: **HALT**. Raise `MathematicalCouplingError`. Log `ERROR: Mathematical coupling detected. Baseline and Outcome must be distinct constructs.`
    - If distinct: Proceed.

### Phase 2: Statistical Modeling
**Goal**: Fit models and generate diagnostics.

#### Phase 2.1: Correlation Analysis (FR-004)
1.  **Action**: Calculate Pearson and Spearman correlation between `news_exposure_freq` and `anxiety_score`.
2.  **Output**: `outputs/correlation_results.json` (Contains `pearson_r`, `pearson_p`, `spearman_r`, `spearman_p`).

#### Phase 2.2: Primary Regression (FR-003, FR-007)
1.  **Action**: Fit OLS model: `anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender`.
2.  **Diagnostics**: 
    - Linearity (Residuals vs Fitted).
    - Homoscedasticity (Breusch-Pagan).
    - Normality (Shapiro-Wilk). **Output `shapiro_w` and `shapiro_p`**.
    - Multicollinearity (VIF).
3.  **Significance Check (SC-001)**: 
    - Extract p-value for `news_exposure_freq`.
    - Set `significant = (p < 0.05)`.
4.  **Output**: `outputs/regression_results.json` (Includes coefficients, `significant` flag, `shapiro_w`, `shapiro_p`).

#### Phase 2.3: Robustness Check (FR-006, Updated)
1.  **Action**: 
 - Split data into high-engagement subset (top [deferred] `social_media_engagement`).
    - **Remove** the `r > 0.3` condition. Run check unconditionally.
    - Fit model on subset.
2.  **Logic**: 
    - Compare coefficient sign and significance with full model.
    - Report correlation between engagement and news as descriptive statistic only.
3.  **Output**: `outputs/robustness_results.json`.

### Phase 3: Visualization & Reporting
**Goal**: Generate plots and final report.
1.  **Action**: Generate scatter plot with regression line and CI (FR-005).
2.  **Output**: `outputs/plot.png`, `outputs/final_report.md`.

## Risk Management

| Risk | Mitigation |
| :--- | :--- |
| **Data Gap** | Phase 0 explicitly halts if verified URLs are invalid. |
| **Mathematical Coupling** | Phase 1.5 validates distinct constructs. |
| **Low Power** | Hard stop at N < 130 (updated from 30). |
| **Causal Misinterpretation** | All outputs explicitly labeled "Associational". |
| **Spec Inconsistency** | Plan implements rigorous methodology; spec flagged for update. |
