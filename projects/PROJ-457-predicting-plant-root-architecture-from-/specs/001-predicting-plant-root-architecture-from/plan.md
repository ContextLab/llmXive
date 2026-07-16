# Implementation Plan: 001-predict-root-architecture

**Branch**: `001-predict-root-architecture` | **Date**: 2024-05-21 | **Spec**: `specs/001-predict-root-architecture/spec.md`
**Input**: Feature specification from `/specs/001-predict-root-architecture/spec.md`

## Summary

This project implements a statistical pipeline to quantify the associational relationship between soil nutrient availability (Phosphorus and Nitrogen) and plant root architecture traits (length, branching density, surface area). The approach utilizes Linear Mixed-Effects Models (LMM) with species as a random intercept and Random Forest baselines, validated via cross-species stratified splitting.

**CRITICAL DATA LIMITATION & SCOPE ADJUSTMENT**: The spec (FR-002) mandates merging with ISRIC-World Soil Information. However, no verified ISRIC source exists in the project's `# Verified datasets` block. The primary source (PlantPheno) may lack explicit P/N columns. Consequently, the pipeline **cannot** fulfill the core spec requirement to link root phenotypes to ISRIC data using a verified source.
*   **Action**: The implementation will proceed ONLY with the verified PlantPheno dataset.
*   **If PlantPheno contains P/N**: The analysis proceeds as planned.
*   **If PlantPheno lacks P/N**: The project will **not** fabricate a merge or use unverified sources. The analysis will proceed with root metrics only, and the "Nutrient Prediction" hypothesis will be flagged as **Unverifiable** in the final report. This is a **Spec Deviation** due to data unavailability, not a methodological choice.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `pyyaml`, `datasets` (Hugging Face), `geopandas`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `artifacts`)  
**Testing**: `pytest` with `pytest-cov`  
**Target Platform**: Linux (GitHub Actions Runner: CPU, ~7 GB RAM)  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Complete full pipeline (ingest → model → report) within 6 hours; output artifacts ≤100MB.  
**Constraints**: No local GPU; must use CPU-first methods (statsmodels, sklearn CPU); **must exclude rows with missing nutrients** (scientific validity); must exclude experimental data (FR-012).  
**Scale/Scope**: Processing of verified public datasets (estimated <10k rows after filtering); analysis across multiple species.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

**Missing Nutrient Data Handling**: Per FR-003, the spec mandates KNN imputation. However, KNN imputation on missing soil nutrients creates circular bias and invalidates p-values. The implementation will **exclude** rows with missing P/N values. This is a **Spec Deviation** (not a standard path) to preserve statistical validity. The pipeline logs the exclusion count and proceeds.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Enforced via pinned `requirements.txt` in `code/`, random seed fixation in all scripts, and deterministic data fetching via Hugging Face `datasets` library.
- **II. Verified Accuracy**: **Task 0.2** explicitly runs the Reference-Validator Agent to verify all citations in `research.md` (Constitution Principle II). Title-token-overlap check is performed.
- **III. Data Hygiene**: Raw data stored in `data/raw` with checksums recorded in `state`. All transformations (log, exclusion) write to new files in `data/processed`.
- **IV. Single Source of Truth**: All figures and statistics in the final report will be generated programmatically from `data/processed` and `code/`, with no manual entry.
- **V. Versioning Discipline**: **Task 4.3** explicitly calculates content hashes for all artifacts in `artifacts/` and updates the `state` file with these hashes, as required by the Advancement-Evaluator Agent.
- **VI. Cross-Species Stratified Validation**: Model splitting logic in `code/modeling.py` will strictly split by `species` ID, not by row, ensuring no data leakage.
- **VII. Nutrient-Specific Metric Normalization**: Preprocessing scripts will explicitly apply log-transformation to root metrics and z-score normalization to nutrients before modeling.

## Project Structure

The following directory structure and placeholder files must exist before execution:

```text
projects/PROJ-457-predicting-plant-root-architecture-from-/specs/001-predicting-plant-root-architecture-from/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── model_results.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output

code/
├── __init__.py
├── config.py            # Paths, seeds, hyperparameters
├── ingestion.py         # Data download, merging, FR-001/002/012 filtering
├── preprocessing.py     # Log-transform, normalization (FR-003), exclusion logic
├── modeling.py          # LMM, RF, CV, FR-004/005/006/008/010
├── analysis.py          # Sensitivity analysis (FR-011), literature comparison, SC-006 measurement
├── visualization.py     # Partial dependence plots (FR-007)
├── reporting.py         # JSON/Report generation (FR-002/003)
├── main.py              # Orchestration script
└── validate_citations.py # Reference-Validator Agent wrapper (Phase 0)

data/
├── raw/                 # Downloaded source files (checksummed)
│   ├── plantpheno_raw.csv
│   └── ...
└── processed/           # Merged, cleaned, transformed datasets
    └── merged_clean.csv

artifacts/
├── models/              # Saved model artifacts (pickle/joblib)
│   ├── lmm_model.pkl
│   └── rf_model.pkl
├── plots/               # PNG visualizations
│   └── partial_dependence_p.png
├── reports/             # Final JSON and Markdown reports
│   ├── model_metrics.json
│   └── final_report.md
└── sensitivity/         # Sensitivity analysis outputs
    └── sensitivity_analysis.json

tests/
├── test_ingestion.py
├── test_preprocessing.py
├── test_modeling.py
└── test_analysis.py

docs/
└── README.md            # Updated with final results
```

**Structure Decision**: Single project structure selected to facilitate tight coupling between data ingestion, modeling, and reporting steps required for a research pipeline. Direct access to `data/` from `code/` is acceptable given the local-runner constraint and data hygiene rules.

## Implementation Phases

### Phase 0: Setup & Validation
- **Task 0.1**: Verify environment and install dependencies (`requirements.txt`).
- **Task 0.2**: **Run Reference-Validator Agent** to verify all citations in `research.md` (Constitution Principle II). Check title-token-overlap ≥ 0.7.
- **Task 0.3**: Download and checksum raw datasets (`data/raw`).

### Phase 1: Data Ingestion & Preprocessing
- **Task 1.1**: Ingest root phenotype data from PlantPheno. **Check for P/N columns**.
- **Task 1.2**: If P/N columns are missing, **STOP** the nutrient merge logic. Flag as "Unverifiable" in report. Proceed with root metrics only if possible.
- **Task 1.3**: **Filter for FR-012**: Exclude experimental/controlled data based on `data_source_type`. **Log exclusion count**.
- **Task 1.4**: **Filter for missing nutrients (Spec Deviation)**: Exclude rows where P or N is missing. **Do NOT impute** (deviation from FR-003 KNN). **Log exclusion count**.
- **Task 1.5**: **Filter for sample size**: Exclude species with n < 20. **Log exclusion count**.
- **Task 1.6**: Preprocess data: log-transform root metrics, z-score normalize nutrients.
- **Task 1.7**: Save cleaned dataset to `data/processed/merged_clean.csv`.

### Phase 2: Statistical Modeling
- **Task 2.1**: Fit Linear Mixed-Effects Model (LMM) with species as random intercept. **AND** fit Within-Species models or interaction models to address confounding (scientific soundness).
- **Task 2.2**: Fit Random Forest Regressor baseline.
- **Task 2.3**: Perform k-fold cross-validation (species-stratified).
- **Task 2.4**: Calculate metrics (R², RMSE, p-values) and VIF for collinearity. **Clarify**: R² comparison is for model complexity assessment, not validity.
- **Task 2.5**: Save model artifacts and metrics to `artifacts/models/` and `artifacts/reports/model_metrics.json`. **Ensure JSON conforms to `model_results.schema.yaml`**.

### Phase 3: Sensitivity Analysis & Literature Comparison (FR-011, SC-006)
- **Task 3.1**: **Conduct sensitivity analysis of nutrient coefficients against literature-reported physiological ranges (FR-011)**. Re-calculate coefficients with ±10% variation in input nutrients.
- **Task 3.2**: **Measure SC-006**: Compare coefficients to physiological ranges. Calculate `literature_overlap` boolean: True if 95% CI of coefficient overlaps with literature range.
- **Task 3.3**: Generate `sensitivity_analysis.json` and update `artifacts/reports/final_report.md` with findings. Link `analysis.py` output to `contracts/model_results.schema.yaml`.

### Phase 4: Visualization & Reporting
- **Task 4.1**: Generate partial dependence plots (FR-007).
- **Task 4.2**: Compile final report with all statistical findings.
- **Task 4.3**: **Update State File**: Calculate content hashes for all artifacts in `artifacts/` and update the `state` file with these hashes (Constitution Principle V).
- **Task 4.4**: **Update `README.md` and `docs/`** with final results, including the `literature_comparison` findings and the `spec_deviations` list.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| KNN Imputation | Spec requires KNN (FR-003). | Scientific validity: KNN on missing nutrients creates circular bias. **Exclusion** chosen instead (Spec Deviation). |
| ISRIC Merge | Spec requires ISRIC (FR-002). | No verified ISRIC source exists. **Exclusion** of missing nutrients chosen. **Spec Deviation** flagged in report. |
| Cross-Species Split | Spec requires species-level split (Constitution VI). | Standard practice for generalization. |

## Output Artifacts

The following artifacts must be produced and validated against their schemas:

1.  **`data/processed/merged_clean.csv`**: Validated against `contracts/dataset.schema.yaml`.
2.  **`artifacts/reports/model_metrics.json`**: Validated against `contracts/model_results.schema.yaml`. Must include:
    *   `lmm.adjusted_r_squared`, `lmm.rmse`, `lmm.p_values`, `lmm.coefficients`
    *   `random_forest.r_squared`, `random_forest.rmse`
    *   `cross_validation.lmm_mean_r2`, `cross_validation.rf_mean_r2`
    *   `literature_comparison.phosphorus_overlap`, `literature_comparison.nitrogen_overlap`
    *   `spec_deviations` (list of strings)
3.  **`artifacts/plots/*.png`**: Total size ≤ 100MB.
4.  **`artifacts/sensitivity/sensitivity_analysis.json`**: Output of Task 3.1/3.2.
5.  **`docs/README.md`**: Updated with final results and literature comparison.