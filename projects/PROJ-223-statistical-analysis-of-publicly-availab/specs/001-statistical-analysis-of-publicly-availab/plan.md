# Implementation Plan: Statistical Analysis of Publicly Available Traffic Accident Data

**Branch**: `001-statistical-analysis-of-publicly-available-traffic-accident-data` | **Date**: 2024-05-21 | **Spec**: `specs/001-statistical-analysis-of-publicly-available-traffic-accident-data/spec.md`
**Input**: Feature specification from `/specs/001-statistical-analysis-of-publicly-available-traffic-accident-data/spec.md`

## Summary

This feature implements a reproducible statistical analysis pipeline to quantify the influence of weather conditions (precipitation, visibility, temperature) on traffic accident severity (property damage, injury, fatality). The approach utilizes an Ordinal Logistic Regression model with fallback to Multinomial Logistic Regression or Penalized GLM, controlling for temporal and infrastructural variables. The pipeline addresses missing data via Multiple Imputation (MICE), corrects for clustering via Cluster-Robust Standard Errors, and performs a Sensitivity Analysis (Minimum Detectable Effect) rather than post-hoc power analysis. The pipeline is designed to run entirely on CPU-only hardware within GitHub Actions constraints, adhering to strict data hygiene and reproducibility principles.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `requests`, `pyyaml`, `scipy`  
**Storage**: Local CSV/Parquet files (in-memory processing with chunking for large files)  
**Testing**: `pytest` (unit tests for data cleaning, integration tests for model convergence)  
**Target Platform**: Linux (GitHub Actions Free Tier: Multiple CPU, substantial RAM, 14GB Disk)  
**Project Type**: Data Science / Statistical Analysis Pipeline  
**Performance Goals**: Complete pipeline execution within 6 hours; model convergence within 30 minutes on sampled data.  
**Constraints**: No GPU/CUDA usage; no external API calls during CI (data pre-fetched or cached); strict memory limits (≤7GB).  
**Scale/Scope**: Analysis of merged traffic/weather datasets; generation of statistical reports and visualizations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`; `requirements.txt` pins all versions; datasets fetched from canonical URLs defined in `research.md`. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs in `research.md` are restricted to the "Verified datasets" block provided in the spec. The FARS URL now points to the verified NHTSA source (`data.nhtsa.gov`). Schema validation ensures data integrity before analysis. |
| **III. Data Hygiene** | **PASS** | Raw data checksums recorded in `state/`; transformations produce new files; PII scan integrated into CI. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final report derived directly from `data/` via `code/`; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts hashed on write; `state` updated on change; CI invalidates stale reviews on hash mismatch. |

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-analysis-of-publicly-available-traffic-accident-data/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── 01_data_ingestion.py       # Downloads, validates schema, and merges FARS/NOAA data
├── 02_preprocessing.py        # Handles missing data via MICE, encodes, and scales
├── 03_model_fitting.py        # Fits Ordinal/Multinomial Logistic Regression or Penalized GLM
├── 04_diagnostics.py          # VIF, LRT, CRSE, and Sensitivity Analysis (MDE)
├── 05_visualization.py        # Generates plots and tables
└── requirements.txt           # Pinned dependencies

data/
├── raw/                       # Downloaded raw files (checksummed)
└── processed/                 # Merged and cleaned datasets

output/
├── plots/                     # Generated visualizations
└── reports/                   # Statistical summaries

tests/
├── test_data_ingestion.py
├── test_model_fitting.py
└── test_diagnostics.py
```

**Structure Decision**: Single project structure selected to maintain simplicity for a statistical analysis pipeline. All scripts are modular and sequential, ensuring data flows from ingestion to visualization without complex interdependencies.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed. | N/A |

## Coverage Mapping (FR & SC)

| Requirement | Plan Phase/Step | Implementation Detail |
| :--- | :--- | :--- |
| **FR-001** (Download FARS/NOAA) | Phase 1: Data Ingestion | `01_data_ingestion.py` fetches from verified NHTSA/NOAA URLs. |
| **FR-002** (Merge & Filter) | Phase 1: Data Ingestion | Pandas merge on timestamp/location; drop rows with missing *critical* keys (ID, Lat/Lon) but retain rows with missing weather for MICE. |
| **FR-003** (Encode Severity) | Phase 2: Preprocessing | Map 0=Property, 1=Injury, 2=Fatality. |
| **FR-004** (Ordinal Logistic) | Phase 3: Modeling | `statsmodels` `OrderedModel`; fallback to `Multinomial` or `GLM` with regularization. |
| **FR-005** (VIF Diagnostics) | Phase 4: Diagnostics | Calculate VIF; flag >5. |
| **FR-006** (Odds Ratios) | Phase 4: Diagnostics | Compute ORs with confidence intervals (or Relative Risk Ratios for MLR). |
| **FR-007** (Visualizations) | Phase 5: Visualization | Coefficient plots, OR tables via `matplotlib`. |
| **FR-008** (CPU Only) | Global Constraint | No GPU libraries; `statsmodels` CPU default. |
| **FR-009** (Sensitivity Analysis) | Phase 4: Diagnostics | Calculate Minimum Detectable Effect (MDE) for OR=1.5 using `statsmodels.stats.power`. Report MDE value and sufficiency flag. |
| **FR-010** (Assumption Check) | Phase 3: Modeling | Run Brant test / Likelihood Ratio Test for proportional odds. If p < 0.05, switch to Multinomial or Penalized GLM. |
| **FR-011** (Ridge Fallback) | Phase 3: Modeling | If VIF > 5, switch to `statsmodels` GLM with `family=Binomial` and `fit_regularized` (L2 penalty) or robust estimator. |
| **SC-001** (Convergence) | Phase 3: Modeling | Log convergence status; fail if no fallback. |
| **SC-002** (VIF Threshold) | Phase 4: Diagnostics | Auto-apply Ridge/Robust if VIF > 5; log action. |
| **SC-003** (Model Fit) | Phase 4: Diagnostics | Report LRT p-value & McFadden's R2. |
| **SC-004** (Compute Limits) | Global Constraint | Sample data if >7GB RAM; no GPU. |
| **SC-005** (MDE Sufficiency) | Phase 4: Diagnostics | Report MDE value; flag 'sufficient' if MDE < 1.5. |
