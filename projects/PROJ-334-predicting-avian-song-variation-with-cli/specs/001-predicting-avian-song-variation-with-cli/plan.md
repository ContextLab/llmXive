# Implementation Plan: Predicting Avian Song Variation with Climatic and Geographic Factors

**Branch**: `001-predicting-avian-song-variation` | **Date**: 2026-06-25 | **Spec**: `specs/001-predicting-avian-song-variation/spec.md`
**Input**: Feature specification from `/specs/001-predicting-avian-song-variation/spec.md`

## Summary

This project implements a computational pipeline to analyze the **associational relationship** between avian song variation metrics and environmental factors (climate and geography) using **real-world observational data**. The system ingests raw acoustic data from Xeno-Canto, climate data from WorldClim, and geographic data from OpenStreetMap/GEBCO, aligns them by species and location, performs exploratory data analysis with automatic multicollinearity handling, and fits linear regression or Generalized Linear Models (GLM) based on distributional checks. The pipeline includes sensitivity analysis across p-value thresholds, validation on hold-out sets, and strict adherence to CPU-only execution constraints for GitHub Actions free-tier runners.

**Critical Note**: This analysis is strictly observational. All findings will be framed as associational, not causal. Geographic coordinates are used as a spatial proxy for confounding structure, with explicit acknowledgment of limitations regarding phylogenetic control.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `scipy`, `geopandas`, `rasterio`, `pyxeno` (or API wrapper)
**Storage**: Local file system (CSV/Parquet/JSON/PDF)
**Testing**: `pytest`
**Target Platform**: Linux (GitHub Actions free-tier runner)
**Project Type**: Data Science Pipeline / CLI
**Performance Goals**: Complete execution within 4.8 hours; memory usage < 7 GB.
**Constraints**: No GPU; no deep learning training; strict observability of missing data; **Automatic fallback to GLM if normality assumptions fail (FR-009, Shapiro-Wilk test)**.
**Scale/Scope**: Single dataset processing; multiple species subsets; sensitivity analysis loop.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

**Plan ↔ Contract Alignment**:
- `code/modeling.py` **MUST** validate its output against `contracts/analysis_output.schema.yaml` before writing final artifacts.
- All modeling steps must pin `random_state` for reproducibility.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `random_state` will be pinned in all modeling steps. `requirements.txt` will pin exact versions. Data sources (Xeno-Canto, WorldClim) will be fetched via verified URLs/APIs. |
| **II. Verified Accuracy** | **PASS** | All dataset citations in `research.md` are restricted to verified real-world sources (Xeno-Canto, WorldClim, GEBCO). No synthetic data is used. |
| **III. Data Hygiene** | **PASS** | Raw data files will be preserved in `data/raw/`. Derived datasets (merged, cleaned) will be written to `data/processed/` with new filenames. Checksums will be recorded in `state.yaml`. |
| **IV. Single Source of Truth** | **PASS** | All figures and statistics in the final report will be generated programmatically from the `code/` scripts and `data/processed/` files. No manual entry. |
| **V. Versioning Discipline** | **PASS** | **Procedural Step**: After every artifact change (Phase 0, Step 6; Phase 4, Step 3), the `state.yaml` `updated_at` timestamp and content hashes **MUST** be updated. This is a mandatory step, not just a note. |

## Project Structure

### Documentation (this feature)

```text
projects/001-predicting-avian-song-variation/
├── .specify/
│   ├── scripts/
│   ├── templates/
│   └── memory/
├── code/
│   ├── __init__.py
│   ├── ingestion.py        # FR-001, FR-006
│   ├── eda.py              # FR-002, Edge Cases
│   ├── modeling.py         # FR-003, FR-004, FR-007, FR-008, FR-009
│   ├── utils.py            # Common helpers
│   └── main.py             # Orchestration
├── data/
│   ├── raw/                # Downloaded datasets (immutable)
│   └── processed/          # Merged, cleaned, aligned datasets
├── output/
│   ├── reports/            # PDF reports (Correlation, Sensitivity)
│   └── models/             # Model summaries, coefficients
├── specs/
│   ├── 001-predicting-avian-song-variation/
│   │   ├── plan.md         # This file
│   │   ├── research.md
│   │   ├── data-model.md
│   │   ├── quickstart.md
│   │   └── contracts/
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

### Source Code (repository root)

**Structure Decision**: Single project structure (Option 1) is selected. The project is a data pipeline, not a web service or mobile app. All logic is contained within `code/` with distinct modules for ingestion, EDA, and modeling.

```text
code/
├── __init__.py
├── ingestion.py
├── eda.py
├── modeling.py
├── utils.py
└── main.py

tests/
├── unit/
│   ├── test_ingestion.py
│   └── test_utils.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Automatic GLM Switch** | **FR-009** requires switching to GLM if Shapiro-Wilk rejects normality. | A simple OLS-only pipeline would fail edge cases where song metrics are skewed (e.g., count data or bounded ratios), violating the spec's robustness requirement. |
| **Sensitivity Analysis Loop** | **FR-004** requires sweeping p-values across common significance thresholds, including 0.05 and 0.1. | A single-threshold run would not provide the robustness analysis required by the spec, failing the "sensitivity" requirement. |
| **Confounder Handling** | **FR-008** requires modeling confounding via coordinates or phylogeny. | Ignoring confounders would lead to spurious associations, violating the "observational" framing and scientific rigor required. |
| **Real-World Data Validation** | Synthetic data cannot validate biological associations. | Using synthetic data would create a circular validation loop, failing the scientific soundness requirement. |
| **Data Alignment Success Rate** | **SC-001** requires a success rate of ≥95%. | A pipeline that proceeds with <95% alignment risks invalid results. A hard fail is required. |
| **Model Convergence Rate** | **SC-002** requires a convergence rate of ≥90%. | A pipeline that fails to converge on most subsets is not robust. A specific aggregation task is required. |
| **Predictive Stability** | **SC-006** requires reporting R² difference. | A pipeline that does not measure stability cannot validate its generalizability. A specific calculation task is required. |
| **Variance Partitioning** | **SC-007** requires reporting confounder variance. | A pipeline that does not partition variance cannot isolate the effect of climate. A specific calculation task is required. |

## Implementation Phases

### Phase 0: Data Ingestion & Validation (FR-001, FR-006, SC-001)

1.  **Environment Setup**: Initialize virtualenv, install dependencies, pin `random_state`.
2.  **Data Retrieval**:
    *   Download acoustic metadata from Xeno-Canto API (filtered by target species list).
    *   Download climate layers (temperature, precip) from WorldClim (current version, high-resolution).
    *   Download elevation data from GEBCO/OSM.
3.  **Alignment & Merging**:
    *   Join acoustic records with climate/geographic data using `location_id` (derived from coordinates) and `species`.
    *   Handle temporal mismatches by aggregating climate data to the recording date.
4.  **Validation Gate (SC-001)**:
    *   **Calculate Data Alignment Success Rate**: `aligned_rows / total_raw_rows`.
    *   **IF** success rate < 95%: **HALT** execution, log error, and report failure. Do not proceed to modeling.
    *   **ELSE**: Log success and proceed.
5.  **Power Analysis (New)**:
    *   **Calculate Achieved Power**: Use `statsmodels.stats.power` to calculate post-hoc power based on observed variance and effect sizes.
    *   **Report**: Log achieved power and acknowledge if the study is underpowered to detect small effects.
6.  **Artifact Update**: Update `state.yaml` `updated_at` timestamp and content hashes (Constitution Principle V).

### Phase 1: Exploratory Data Analysis (FR-002, Edge Cases)

1.  **Correlation Matrix**: Generate heatmap of all continuous variables.
2.  **Multicollinearity Check**:
    *   Identify pairs with |r| > 0.8.
    *   **IF** detected: Apply PCA or Ridge Regression and document the method in the report.
3.  **Spatial Autocorrelation Check**:
    *   Perform **Moran's I test** on residuals of a null model to detect spatial structure.
    *   Report spatial autocorrelation status.
4.  **Visualization**: Generate scatterplot matrix (song metrics vs. climate).
5.  **Output**: `output/reports/eda_report.pdf`.

### Phase 2: Data Splitting & Modeling (FR-003, FR-007, FR-008, FR-009)

1.  **Data Splitting (FR-007)**:
    *   Partition dataset into training and hold-out validation sets using `train_test_split` with fixed `random_state`.
    *   Ensure stratification by species if sample sizes allow.
2.  **Distributional Check (FR-009)**:
    *   Perform **Shapiro-Wilk test** on training residuals (initial OLS).
    *   **IF** p < 0.05: Switch to GLM (Gamma/Poisson) with appropriate link function.
    *   **ELSE**: Proceed with OLS.
3.  **Model Fitting**:
    *   Fit model on training set including climate predictors and confounders (lat/lon).
    *   **FR-008**: Explicitly model confounding structure; report variance explained by confounders vs. climate.
4.  **Predictive Stability (SC-006)**:
    *   Evaluate model on hold-out set.
    *   **Calculate `r_squared_diff`** = |R²_train - R²_valid|.
    *   **IF** `r_squared_diff` >= 0.10: Flag as "Unstable Model" in report.
    *   **Output**: Include `r_squared_diff` in `output/models/model_summary.csv`.
5.  **Output**: `output/models/model_summary.csv` (includes `r_squared_diff`).

### Phase 3: Sensitivity & Convergence Analysis (FR-004, SC-002, SC-003, SC-007)

1.  **Sensitivity Loop (FR-004)**:
    *   Iterate thresholds across a range of significance levels.
    *   For each threshold: Re-evaluate significance of predictors, count significant predictors, record R².
    *   **Calculate Effect Size**: Compute **Cohen's f²** for each predictor at each threshold to validate stability of association magnitude.
2.  **Convergence Aggregation (SC-002)**:
    *   **Aggregate Convergence Results**: Collect convergence status across all species subsets.
    *   **Calculate Convergence Rate**: `(converged_models / total_models)`.
    *   **IF** rate < 90%: Flag in report (do not halt, but document limitation).
3.  **Variance Partitioning (SC-007)**:
    *   **Calculate Variance Partition**: Compute proportion of variance explained by confounders vs. climate predictors.
    *   **Output**: Include `confounder_variance_explained` metric in final report and `model_summary.csv`.
4.  **Final Report Generation**:
    *   Compile all metrics into `output/reports/analysis_report.pdf`.
    *   Ensure all headers include "Associational Analysis".

### Phase 4: Output & Validation (FR-005, SC-008)

1.  **Schema Validation**: Validate `model_summary.csv` against `contracts/analysis_output.schema.yaml`.
2.  **Final Artifacts**:
    *   `output/reports/analysis_report.pdf`
    *   `output/models/model_summary.csv`
    *   `output/logs/ingestion.log`
3.  **Version Update**: Update `state.yaml` with final artifact hashes and `updated_at` timestamp (Constitution Principle V).

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Data Alignment Failure** | Fatal: Cannot proceed. | Hard fail at Phase 0 if < 95% alignment (SC-001). |
| **High Collinearity** | Model instability. | Automatic PCA/Ridge fallback (FR-002). |
| **Non-Normal Residuals** | Invalid p-values. | Automatic GLM switch (FR-009). |
| **Memory Overflow** | CI Job Fail. | Chunked processing or sampling if data > 2GB. |
| **Spatial Autocorrelation** | Spurious associations. | Moran's I test and spatial covariate inclusion. |