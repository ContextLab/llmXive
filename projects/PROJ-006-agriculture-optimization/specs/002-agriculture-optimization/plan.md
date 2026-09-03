# Implementation Plan: Correlational Analysis of Climate-Smart Agricultural Practices and Yield Stability Independent of Financial Access

**Branch**: `001-climate-smart-eval` | **Date**: 2026-08-14 | **Spec**: `specs/001-climate-smart-eval/spec.md`
**Input**: Feature specification from `/specs/001-climate-smart-eval/spec.md`

## Summary

This project implements an observational cross-sectional analysis to assess the association between Climate-Smart Agricultural (CSA) practice adoption and yield stability (measured via satellite-derived NDVI variability) and food security (HFIAS), while controlling for financial access. The implementation relies on classical statistical methods (multiple linear regression with robust standard errors) executed on a CPU-constrained GitHub Actions runner. The core challenge is harmonizing LSMS-ISA survey data with Sentinel-2 satellite imagery, constructing a validated CSA index, and performing rigorous diagnostics (VIF, Bonferroni correction) to ensure statistical integrity without fabricating data or exceeding compute limits.

**Critical Data Note**: No verified open-source dataset exists that contains the specific combination of household-level CSA practices, financial access, food security scores (HFIAS), and geospatial coordinates required for this study. Consequently, this project operates in **"Structural Validation Mode"**: it validates the *code logic* and *statistical pipeline* using a verified generic tabular dataset (UCI) and clearly labeled synthetic data, but explicitly refrains from making scientific claims about the hypothesis until real data becomes available.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels` (for robust regression/VIF), `geopandas` (for spatial joins), `requests`, `pyyaml`, `pytest`.  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `contracts`). No external database.  
**Testing**: `pytest` (unit, integration, contract tests).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM).  
**Project Type**: Data analysis pipeline / Statistical research.  
**Performance Goals**: Complete full pipeline (ingest, join, model, report) within 6 hours on CPU.  
**Constraints**: No GPU available; LSMS-ISA data access is restricted (requires open substitute or explicit fallback); Sentinel-2 data must be streamed or sampled to fit RAM.  
**Scale/Scope**: Target $N > 1000$ households (if available); aggregated to village level if $N$ is insufficient.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt` and random seeds in `src/analysis/`. |
| **II. Verified Accuracy** | **PASS (with Data Gap)** | Plan acknowledges no verified primary source exists for LSMS-ISA/Sentinel-2. Structural Validation Mode uses generic verified tabular data (UCI) for code logic only. No scientific claims made on synthetic data. |
| **III. Data Hygiene** | **PASS** | Plan requires checksums for raw data and immutable transformations to new files. |
| **IV. Single Source of Truth** | **PASS** | Plan structure aligns with `src/analysis/` scripts and `contracts/` schemas. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts will be recorded in state YAML. |
| **VI. Multi-Source Validation** | **PASS** | Synthetic data generation is strictly decoupled from analysis logic (fixed seed, independent RNG) to prevent tautological correlation. |
| **VII. Spatial-Temporal Alignment** | **PASS** | Plan mandates explicit growing season window alignment checks before metric calculation. |

**Critical Gap Addressed**: The spec mentions LSMS-ISA for Malawi/Tanzania. The "Verified datasets" block explicitly states **NO verified source found** for LSMS-ISA. Per Constitution II and Data Availability rules, the plan **MUST NOT** assume this data is downloadable. The implementation strategy (detailed in `research.md`) will:
1.  **Abort Real Data Path**: Acknowledge that no open dataset supports the specific hypothesis.
2.  **Structural Validation**: Use a verified generic tabular dataset (e.g., UCI) to test the *pipeline's ability to run regressions* and calculate VIFs.
3.  **Synthetic Fallback**: If no generic dataset is suitable, generate synthetic data strictly for schema conformance testing, clearly labeled as non-scientific.
4.  **Reporting**: The final report will explicitly state that results are "Structural Validation Only" and not a test of the scientific hypothesis.

## Project Structure

### Documentation (this feature)

```text
specs/001-climate-smart-eval/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── ingest.py              # Data download, spatial join, cleaning
│   ├── processing/
│   │   └── feature_engineering.py # CSA Index, Stability Score calc
│   └── validation.py          # Schema validation logic
├── analysis/
│   ├── run_regression.py      # Model fitting (Model 1 & 2)
│   ├── diagnostics.py         # VIF, Robust SE checks
│   └── sensitivity_check.py   # Cloud cover threshold sweep
├── reports/
│   └── generate_report.py     # PDF generation with disclaimers
├── cli/
│   ├── validate.py            # Contract validation CLI
│   └── run_pipeline.py        # End-to-end orchestration
├── config/
│   ├── constants.py           # Thresholds (VIF > 5, alpha = 0.0167)
│   └── schemas.py             # Schema definitions
└── tests/
    ├── contract/
    │   └── test_dataset_schema.py
    ├── integration/
    │   └── test_pipeline.py
    └── unit/
        ├── test_feature_engineering.py
        └── test_diagnostics.py

data/
├── raw/                       # Downloaded/Verified raw data
├── processed/                 # analysis_dataset.csv, village_aggregated.csv
└── logs/                      # ingestion_errors.log, linkage_validation.json

contracts/
├── dataset.schema.yaml
└── output.schema.yaml
```

**Structure Decision**: The structure follows a standard data science pipeline (Ingest -> Process -> Analyze -> Report) with explicit separation of concerns for validation (CLI) and diagnostics. This resolves the previous "structural drift" concern by ensuring `src/analysis/` contains the regression logic as specified in the plan, and `src/data/` handles the heavy lifting of ingestion and feature engineering.

## Complexity Tracking

| Necessary Complexity | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Spatial Join & Satellite Harmonization** | Essential for linking survey data to yield stability metrics. | A simple CSV merge is insufficient; geospatial alignment (fuzzing, pixel matching) is required by the methodology. |
| **Robust Standard Errors & VIF Diagnostics** | Required by FR-004/FR-005 to address heteroskedasticity and collinearity. | OLS without diagnostics would violate statistical rigor requirements and risk spurious results. |
| **Sensitivity Analysis (Cloud Cover Sweep)** | Required by FR-006 to validate robustness against data quality thresholds. | A single-point analysis would fail to demonstrate result stability under varying data quality conditions. |
| **Model Specification Sensitivity** | Required to detect non-linearity (Ramsey RESET) and interaction effects. | A linear-only model risks Type II errors if the true relationship is non-linear. |
| **Temporal Alignment Validation** | Required to ensure satellite growing season matches survey reference period. | Mismatched seasons would render the "Yield Stability" metric noise. |
| **NDVI Masking Protocol** | Required to exclude non-vegetated pixels (fallow/early season) from CV calculation. | Including low-NDVI pixels introduces massive outliers that robust SE cannot fully correct. |

## Tasks (Implementation Roadmap)

*Note: Tasks are grouped by User Story for clarity, but each test type is distinct.*

### Phase 1: Data Ingestion & Harmonization (US-1)
- [ ] **T001**: Implement `src/data/ingest.py` to download/calculate synthetic data.
- [ ] **T002**: Implement `src/data/processing/feature_engineering.py` for CSA Index and Stability Score.
- [ ] **T003**: Implement spatial join logic with fuzzing and temporal alignment checks.
- [ ] **T004**: Generate `data/processed/analysis_dataset.csv` and `data/logs/linkage_validation.json`.
- [ ] **T005**: **Contract Test**: Implement `tests/contract/test_dataset_schema.py` to validate `analysis_dataset.csv` against `contracts/dataset.schema.yaml`.

### Phase 2: Statistical Analysis (US-2)
- [ ] **T006**: Implement `src/analysis/run_regression.py` for Model 1 & 2 with robust SE.
- [ ] **T007**: Implement `src/analysis/diagnostics.py` for VIF calculation and logging.
- [ ] **T008**: Generate `data/processed/regression_results.json`.
- [ ] **T009**: **Unit Test**: Implement `tests/unit/test_feature_engineering.py` for CSA/NDVI logic.
- [ ] **T010**: **Unit Test**: Implement `tests/unit/test_diagnostics.py` for VIF logic.

### Phase 3: Sensitivity & Reporting (US-3)
- [ ] **T011**: Implement `src/analysis/sensitivity_check.py` for cloud cover sweep.
- [ ] **T012**: Implement `src/reports/generate_report.py` with disclaimers.
- [ ] **T013**: **Integration Test**: Implement `tests/integration/test_pipeline.py` to run full flow.
- [ ] **T014**: **Contract Test**: Implement `tests/contract/test_output_schema.py` for `regression_results.json`.

## Data Availability & Structural Validation Strategy

**Status**: **NO VERIFIED SOURCE** for LSMS-ISA or Sentinel-2 in the provided verified datasets block.

**Strategy**:
1.  **Structural Validation**: The pipeline will be tested using a verified generic tabular dataset (UCI Water Treatment Plant) or a strictly synthetic dataset that adheres to `contracts/dataset.schema.yaml`.
2.  **Decoupling**: The synthetic data generation logic is **strictly decoupled** from the analysis logic (independent RNG seeds). No correlation is imposed between `CSA_Index` and `Stability_Score` in the synthetic generator.
3.  **Outcome**: The pipeline will successfully run regressions and calculate VIFs, but the resulting coefficients and p-values are **mathematical artifacts of the random seed**, not scientific findings.
4.  **Reporting**: The final report will explicitly state: "Results are Structural Validation Only. No scientific claims regarding the hypothesis are made due to lack of verified real-world data."

## Compute Feasibility

-   **Environment**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM, no GPU).
-   **Strategy**: **CPU-First**.
    -   All statistical operations (regression, VIF) are classical and CPU-tractable.
    -   Data processing (spatial join) will be performed on a **sampled** dataset or aggregated to village level to ensure memory safety (< 7 GB).
    -   No deep learning or GPU-accelerated models are used.
-   **Rationale**: The methodology (OLS, VIF, Bonferroni) does not require GPU acceleration. Using a GPU would be unnecessary overhead and incompatible with the runner. The "GPU escape hatch" is not needed for this specific statistical analysis.