# Implementation Plan: The Impact of Social Media "Doomscrolling" on Anticipatory Anxiety

**Branch**: `001-doomscrolling-anxiety` | **Date**: 2026-06-27 | **Spec**: `specs/001-doomscrolling-anxiety/spec.md`

## Summary

This feature implements a robust statistical analysis pipeline to investigate the relationship between negative news sentiment intensity (proxy for doomscrolling) and population-level anticipatory anxiety. The system fetches time-series data from the GDELT Project (AVGTONE metric) and Google Trends, preprocesses them to a aligned daily resolution with z-score normalization, performs stationarity checks (ADF), differencing if necessary, and executes multivariate Granger causality tests controlling for major global events. The implementation strictly adheres to CPU-only constraints, ensuring the entire pipeline runs within 6 hours on a free-tier CI runner.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `requests`, `matplotlib`, `seaborn`, `pyyaml`  
**Storage**: Local CSV files (`data/raw/`, `data/processed/`)  
**Testing**: `pytest` (unit tests for data alignment, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Data Analysis Pipeline / CLI  
**Performance Goals**: Total runtime ≤ 6 hours; Memory ≤ 7 GB  
**Constraints**: No GPU/CUDA; No external API keys stored in repo (use env vars); Forward-fill imputation only for small gaps; Mandatory ADF testing; Differencing for non-stationary series; Granger causality requires N ≥ 20.  
**Scale/Scope**: Time-series data for an extended period.

## Constitution Check

| Principle | Status | Justification / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds will be pinned in `code/analysis.py`. External datasets (GDELT, Google Trends) are fetched from canonical sources via script. `requirements.txt` will pin versions. |
| **II. Verified Accuracy** | **Conditional Pass** | Citations are validated against the canonical GDELT 2.0 Archive structure and Google Trends API parameters defined in `research.md`. Since no specific URL was provided in the input block, the plan relies on the defined accession strings (e.g., `GDELT 2.0 Global Events Database, AVGTONE field`) to ensure testability. |
| **III. Data Hygiene** | **Pass** | Raw data (CSVs) will be saved to `data/raw/` with checksums. Processed data will be saved to `data/processed/` with derived filenames. No in-place modification. |
| **IV. Single Source of Truth** | **Pass** | All statistics in the final report will be generated programmatically from `data/processed/` and `code/analysis.py`. No hand-typed values. |
| **V. Versioning Discipline** | **Pass** | Content hashes for data artifacts will be recorded in `state/projects/...yaml`. |
| **VI. Temporal Data Alignment** | **Pass** | The `preprocessing` phase explicitly aligns timestamps to daily intervals, performs ADF tests, and documents the differencing logic. Lag operations are documented with justification. |

## Project Structure

### Documentation (this feature)

```text
specs/001-doomscrolling-anxiety/
├── plan.md              # This file
├── research.md          # Research findings & dataset strategy
├── data-model.md        # Data schemas & entity definitions
├── quickstart.md        # Setup & run instructions
├── contracts/           # YAML schemas for validation
└── tasks.md             # Generated later
```

### Source Code (repository root)

```text
projects/PROJ-487-the-impact-of-social-media-doomscrolling/
├── code/
│   ├── __init__.py
│   ├── fetch_data.py          # Fetches GDELT and Google Trends data
│   ├── preprocess.py          # Cleans, aligns, normalizes, differs data
│   ├── analysis.py            # ADF, Correlation, Granger (multivariate)
│   └── requirements.txt       # Pinned dependencies
├── data/
│   ├── raw/                   # Downloaded CSVs (GDELT, Trends)
│   └── processed/             # Aligned, normalized, differenced time-series
├── output/
│   ├── reports/               # PDF/HTML reports, plots
│   └── logs/                  # Execution logs
└── tests/
    ├── unit/                  # Test data alignment, normalization
    └── integration/           # End-to-end pipeline test
```

**Structure Decision**: Single project structure (`code/`) chosen as the scope is a linear data analysis pipeline without complex frontend/backend separation. This minimizes overhead for CI execution.

## Phase Execution Plan

### Phase 0: Research & Data Accession
- **Goal**: Define canonical data sources and fallback strategies.
- **Action**: Acknowledge that no verified URL was in the input block. Define the canonical accession: "GDELT 2.0 Global Events Database, AVGTONE field" and "Google Trends API (geo=US, category=0)".
- **Constraint Check**: Ensure no un-spec'd constraints are added. The plan relies *only* on the variables specified in FR-001 and FR-002.
- **Dataset Fit**: GDELT provides `AVGTONE` (sentiment). Google Trends provides search volume. The spec explicitly frames "doomscrolling" as the *impact* of negative news intensity, not direct social media volume. This fits the available data.
- **Fallback Strategy**: If live API access fails on CI, the pipeline will use static sample CSVs (provided in `data/raw/samples/`) to ensure the analysis logic is testable.
- **Output**: `research.md` with dataset accession strings and fallback logic.

### Phase 1: Data Model & Contracts
- **Goal**: Implement validation logic against existing schemas.
- **Action**: The contracts `raw_news.schema.yaml`, `raw_trends.schema.yaml`, and `processed_timeseries.schema.yaml` are already defined. The implementation will add validation logic in `fetch_data.py` and `preprocess.py` to ensure data conforms to these schemas before processing.
- **Constraint**: Ensure schemas enforce `date` (ISO8601), `value` (float), and `source` (string).
- **Output**: Updated `data-model.md`, `quickstart.md`, and validation code.

### Phase 2: Implementation (Mechanical Step)
- **Goal**: Generate `tasks.md` and execute the mechanical setup.
- **Action**: The runtime will execute `setup-plan.sh`. The Implementer Agent will then write code based on the plan.
- **Constraint**: Code must not use GPU libraries.

### Phase 3: Execution & Validation
- **Goal**: Run the pipeline on CI with rigorous statistical checks.
- **Action**:
  1. **Fetch Data** (FR-001): Retrieve GDELT `AVGTONE` and Google Trends. Handle API errors/retries.
  2. **Preprocess** (FR-002): 
     - Align to daily (intersection).
     - Forward-fill gaps < 3 days (preserve continuity).
     - **Stationarity Check**: Run Augmented Dickey-Fuller (ADF) test.
     - **Differencing**: If non-stationary (p > 0.05), apply first-order differencing.
     - Z-score normalization.
  3. **Analyze** (FR-003, FR-004, FR-005):
     - **Confounder Control**: Generate event dummy variables for major global events (e.g., Pandemic Start, Election Periods).
     - **Correlation**: Pearson/Spearman with p-values.
     - **Granger Causality**: Multivariate Granger tests (lags, 2, 3) including event dummies as exogenous variables.
     - **Correction**: Apply Holm-Bonferroni correction for dependent lag tests.
     - **Sensitivity**: Sweep lag windows {, 2, 3}.
  4. **Report** (FR-006): Generate plots and summary.
- **Success Criteria**:
  - SC-001: ≥95% data completeness after imputation.
  - SC-002: Holm-Bonferroni corrected p < 0.0167 for at least one lag in the primary Granger test.
  - SC-003: Runtime ≤ 6 hours (enforced by CI job timeout).

## FR/SC Coverage Matrix

| Requirement ID | Plan Element | Description |
| :--- | :--- | :--- |
| **FR-001** | `fetch_data.py` | Fetches GDELT `AVGTONE` and Google Trends. Handles API errors/retries. |
| **FR-002** | `preprocess.py` | Aligns to daily, forward-fills small gaps, ADF test, differencing if needed, z-scores. |
| **FR-003** | `analysis.py` | Computes Pearson/Spearman correlation with p-values. |
| **FR-004** | `analysis.py` | Runs multivariate Granger causality (lags 1, 2, 3) with event dummies. Frames as associational. |
| **FR-005** | `analysis.py` | Sensitivity analysis sweeping lag windows {1, 2, 3} with Holm-Bonferroni correction. |
| **FR-006** | `CI Config` | Job timeout set to 6h; Memory limit checked; `requirements.txt` pins CPU-only libraries. |
| **SC-001** | `preprocess.py` | Checks completeness after forward-fill; logs warning if <95%. |
| **SC-002** | `analysis.py` | Applies Holm-Bonferroni correction to Granger p-values (target < 0.0167). |
| **SC-003** | `CI Config` | Job timeout set to 6h; Memory limit checked. |

## Compute Feasibility Strategy

- **Data Volume**: years of daily data = [deferred] rows. Extremely small for RAM.
- **Method**: `statsmodels` Granger causality (CPU-optimized), `scipy` correlations, and `statsmodels.tsa.stattools.adfuller` are lightweight.
- **No GPU**: No deep learning models. No `torch` or `tensorflow` training.
- **Runtime**: Expected execution time < 30 minutes. Well within the 6-hour limit.