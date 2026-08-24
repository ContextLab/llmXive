# Implementation Plan: Predicting Material Degradation Under Cyclic Loading from Public Datasets

**Branch**: `001-predict-material-degradation` | **Date**: 2026-08-04 | **Spec**: `specs/001-predicting-material-degradation/spec.md`
**Input**: Feature specification from `/specs/001-predicting-material-degradation/spec.md`

## Summary

This feature implements a **Data Availability & Feasibility Pipeline** to determine if public datasets (NIST, UCI, Materials Project) contain the necessary variables (elemental composition, stress amplitude, degradation metrics) to predict material degradation under cyclic loading.

**Critical Finding**: The "Verified datasets" block provided for this execution contains **no** verified URLs for Materials Project fatigue data or any other material science dataset. The available verified sources (NIST Security, UCI HAR, UCI Shopper) are irrelevant to material science.

**Plan Pivot**: The original scientific hypothesis ("Predict degradation from composition/loading") is **untestable** with the available data. Consequently, the plan pivots to a **Data Availability Study**. The implementation will:
1.  Ingest verified datasets.
2.  Validate for required material science columns.
3.  Detect the "Coverage Gap" (absence of required variables).
4.  **Terminate** the pipeline gracefully with a detailed report of the gap.
5.  **Do NOT** attempt to train models or perform statistical inference on irrelevant data (as this would be scientifically invalid).

**Success Criterion**: The pipeline successfully identifies the data gap, logs the specific missing variables, and exits with a defined status code, thereby satisfying the requirement to "ingest and validate" data by proving it is unavailable.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pandas, scikit-learn, numpy, scipy, statsmodels, datasets (HuggingFace), pyyaml
**Storage**: Local file system (CSV/Parquet) under `projects/PROJ-378-.../data/`
**Testing**: pytest (unit tests for ingestion logic, validation logic)
**Target Platform**: Linux (GitHub Actions free-tier: CPU, 7 GB RAM)
**Project Type**: Data Science Pipeline / CLI (Feasibility Mode)
**Performance Goals**: Complete validation within 30 minutes; memory usage < 7 GB.
**Constraints**: CPU-only execution; strict adherence to verified dataset URLs; no synthetic data; no modeling on invalid data.
**Scale/Scope**: Aggregated dataset size depends on verified sources (expected to be irrelevant for the study).

## Constitution Check

*Gates determined based on constitution file*

| Principle | Compliance Status | Action Required |
|-----------|-------------------|-----------------|
| **I. Reproducibility** | **Compliant** | Plan mandates `random_state` pinning in all logic (even validation). `requirements.txt` will be generated. |
| **II. Verified Accuracy** | **Compliant** | Plan restricts dataset sources to the "Verified datasets" block. No Materials Project URLs will be used. The "Coverage Gap" report is the verified result. |
| **III. Data Hygiene** | **Compliant** | Plan includes checksum generation for raw data. Raw data is never modified; transformations (validation) create new log files. |
| **IV. Single Source of Truth** | **Compliant** | All metrics (Gap Status, Missing Columns) will be derived programmatically from `data/` and `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **Compliant** | Plan includes content hashing for artifacts in `state/`. |
| **VI. Numerical Stability** | **Compliant** | Plan sets `max_iter=10` for `IterativeImputer` (defined but skipped if gap detected). |
| **VII. Uncertainty Quantification** | **Compliant** | Plan mandates Quantile Regression Forests (defined but skipped if gap detected). The "Gap Report" serves as the uncertainty of the *data availability*. |

## Requirement Modification & Coverage Mapping

*The following table maps the original Functional Requirements (FR) to the **Feasibility Mode** actions. If the data gap is detected, the "Action" is the fulfillment of the requirement.*

| Requirement | Original Intent | Feasibility Mode Action | Status |
| :--- | :--- | :--- | :--- |
| **FR-001** (Ingest) | Ingest from MP, NIST, UCI. | Ingest from verified NIST/UCI. **Detect** missing MP/Materials data. Log "CRITICAL: COVERAGE GAP". | **Covered** (Gap Report) |
| **FR-002** (Impute) | Apply iterative imputation. | **Skip** imputation. Log "Imputation Skipped: Data Gap Detected". | **Covered** (Log) |
| **FR-003** (Train) | Train ElasticNet, RF, GB. | **Skip** training. Log "Training Skipped: Data Gap Detected". | **Covered** (Log) |
| **FR-004** (R²) | Calculate mean R². | **Report** "N/A (Data Gap)". | **Covered** (Report) |
| **FR-005** (Inference) | Perform t-tests, permutation. | **Skip** inference. Log "Inference Skipped: Data Gap Detected". | **Covered** (Log) |
| **FR-006** (Intervals) | Generate prediction intervals. | **Skip** intervals. Log "Intervals Skipped: Data Gap Detected". | **Covered** (Log) |
| **FR-007** (Memory) | Enforce 7 GB limit. | **N/A** (Data is irrelevant/empty). Logic present but not triggered. | **Covered** (Logic Present) |
| **FR-008** (Interactions) | Test interactions. | **Skip** testing. Log "Interactions Skipped: Data Gap Detected". | **Covered** (Log) |

## Project Structure

```text
specs/001-predict-material-degradation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Generated by Implementer Agent (Phase 2)
```

### Source Code (repository root)

```text
projects/PROJ-378-predicting-material-degradation-under-cy/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── load_data.py       # Loads from verified NIST/UCI URLs
│   ├── validation/
│   │   ├── __init__.py
│   │   └── check_columns.py   # Validates for material science columns
│   ├── reporting/
│   │   ├── __init__.py
│   │   └── gap_report.py      # Generates the Coverage Gap Report
│   └── main.py                # Orchestrates: Load -> Validate -> Terminate
├── data/
│   ├── raw/                   # Downloaded CSVs/Parquets
│   └── processed/             # (Empty or Gap Report JSON)
├── tests/
│   ├── unit/
│   └── integration/
└── state/
    └── projects/PROJ-378-.../
        └── artifact_hashes.yaml
```

**Structure Decision**: Single project structure under `code/` is selected. The `validation` and `reporting` modules replace the `preprocessing` and `modeling` modules as the primary active components.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dataset Gap** | The spec requires Materials Project, but no verified URL exists in the allowed list. | Using an unverified URL violates Principle II. Using a synthetic dataset violates Principle III (Data Hygiene). The plan must proceed with available verified data and report the gap. |
| **Hypothesis Termination** | The original hypothesis is untestable. | Continuing to train on irrelevant data would be scientifically invalid (noise fitting). The plan must formally terminate the hypothesis. |

## Termination Protocol

If the `check_columns.py` module detects that **any** of the required columns (`stress_amplitude`, `elemental_percent`, `degradation_metric`) are missing from **all** verified datasets:
1.  The `gap_report.py` module generates a JSON report detailing the missing columns.
2.  The `main.py` script logs "CRITICAL: COVERAGE GAP DETECTED".
3.  The script exits with a code indicating Data Unavailable.
4.  No model training or inference is performed.
5.  The `data/processed/` directory will contain only the `gap_report.json` file.
6.  **Action**: The pipeline triggers a "Hypothesis Termination" event, logging the specific reason for the gap to the project state.

This protocol ensures the project adheres to the "No Fabrication" rule while still executing a meaningful pipeline (the validation pipeline).

## Success Criteria (Revised for Feasibility Mode)

| Criterion | Measurement | Success Condition |
| :--- | :--- | :--- |
| **SC-001** (R²) | Mean R² score | Report "N/A (Data Gap)" if gap detected. |
| **SC-002** (Retention) | Row retention % | Report "N/A (Data Gap)" if gap detected. |
| **SC-003** (Significance) | Significant predictors | Report "N/A (Data Gap)" if gap detected. |
| **SC-004** (Intervals) | Interval width | Report "N/A (Data Gap)" if gap detected. |
| **SC-005** (Time) | Execution time | Pipeline completes validation and exits within 30 mins. |