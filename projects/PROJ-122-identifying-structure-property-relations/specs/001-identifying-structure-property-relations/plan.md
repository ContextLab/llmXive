# Implementation Plan: Identifying Structure-Property Relationships in Polymer Blends

**Branch**: `001-structure-property-relationships` | **Date**: 2024-05-21 | **Spec**: `specs/001-structure-property-relations/spec.md`

## Summary

This feature implements a computational pipeline to identify structure-property relationships in polymer blends using public databases. The approach aggregates heterogeneous data (SMILES, composition, Tg, Modulus) primarily from **verified** public sources (PolymerBench, NIST, Materials Project APIs), harmonizes units (Kelvin, GPa), and generates molecular descriptors via RDKit. It then trains Random Forest and XGBoost models to predict the *residual* properties (Observed - Physics Baseline), performs rigorous statistical validation (Nested Cross-Validation, Permutation Testing for small N, VIF sensitivity analysis), and ensures all results are reproducible on CPU-only CI.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `pandas`, `scikit-learn`, `xgboost`, `shap`, `numpy`, `requests`, `jsonschema`, `datasets`  
**Storage**: Local file system (`data/` for raw/processed data, `code/` for scripts, `state.yaml` for versioning)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM, no GPU)  
**Project Type**: Data science pipeline / CLI  
**Performance Goals**: Complete pipeline < 5 hours on CI; RAM usage < 7 GB; disk usage < 14 GB.  
**Constraints**: No GPU/CUDA; no large-LLM inference; data sampled to **[deferred] rows** if raw fetch exceeds memory; strict unit harmonization; VIF sensitivity analysis must re-train models.
**Scale/Scope**: A diverse set of polymer blend entries (dependent on public data availability); Multiple molecular descriptors per monomer.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, canonical data sources, isolated virtualenv, and strict API-only data ingestion. |
| **II. Verified Accuracy** | **PASS** | Plan includes **T016** to implement Reference-Validator Agent workflow and `CITATION_TITLE_OVERLAP_THRESHOLD` check before ingestion. |
| **III. Data Hygiene** | **PASS** | Plan mandates checksumming (**T017**) via `state.yaml`, immutable raw data, and schema validation (T015). `dataset.schema.yaml` is the source of truth for `01_ingest.py`. |
| **IV. Single Source of Truth** | **PASS** | All metrics (MAE, p-values) derived from code outputs, not hand-typed. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked in `state.yaml` (root); **T017** updates this file after every data step. |
| **VI. Standardized Units** | **PASS** | Plan enforces Kelvin/GPa conversion and physical bounds checks. |
| **VII. Descriptor Traceability** | **PASS** | RDKit version pinned; feature importance tied to exact descriptor set. |

## Project Structure

### Documentation (this feature)

```text
specs/001-structure-property-relations/
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
projects/PROJ-122-identifying-structure-property-relations/
├── data/
│   ├── raw/             # Immutable downloaded data (checksummed)
│   ├── processed/       # Harmonized CSVs, feature matrices, residuals, baselines
│   └── artifacts/       # Model checkpoints, SHAP outputs, stability reports
├── code/
│   ├── 01_ingest.py     # Data fetching, unit harmonization, validation, hashing, schema check
│   ├── 02_features.py   # Descriptor generation, VIF calc (diagnostic only)
│   ├── 03_train.py      # Nested CV, model training, VIF sensitivity re-training, stability runs
│   ├── 04_report.py     # Aggregation of stability metrics, SHAP plots, final tables, causal disclaimer
│   └── utils.py         # Shared helpers (logging, unit conversion, hashing)
├── tests/
│   ├── unit/
│   │   ├── test_ingest.py
│   │   ├── test_features.py
│   │   ├── test_train.py
│   │   └── test_validation.py
│   └── integration/
│       └── test_pipeline.py
├── state.yaml           # Versioning and hash tracking (Principle V)
├── requirements.txt     # Pinned dependencies
└── README.md
```

**Structure Decision**: Single project structure selected. Separation of concerns (ingest, features, train, report) aligns with the 3-stage pipeline (US1, US2, US3). This ensures independent testing of feature engineering (US2) without requiring model training, while placing the VIF sensitivity analysis (re-training) strictly in the training module (US3) to satisfy FR-008.

## Implementation Phases

### Phase 1: Data Ingestion & Validation (US1)
*   **T015**: Implement Schema Validation. Validate raw data against `dataset.schema.yaml` before processing.
*   **T016**: Implement Reference-Validator Hook. Verify all dataset URLs and check `CITATION_TITLE_OVERLAP_THRESHOLD` before ingestion.
*   **T017**: Implement Content Hashing. Calculate SHA-256 for all `data/raw/` files and update `state.yaml` after every ingestion step.
*   **T018**: Implement Stratified Sampling. If data > 100,000 rows, sample using 'Stratified Random Sampling by Source' to fit memory (Target: [deferred] rows, capped at 7GB RAM).
*   **T019**: Implement Data Insufficiency Halt. In `code/01_ingest.py`, raise `DataInsufficiencyError` with message "Dataset size N={N} < 100" if valid records < 100. Log the error and exit code 1. (Pre-condition for US2/US3).
*   **T020**: Implement Weight-Fraction Tolerance Sensitivity Sweep. Iterate {0.01, 0.02, 0.05}, record impact on dataset size and SC-004 metrics. **Mandatory**: If MAE variance across sweeps > 5%, flag assumption as invalid in final report.

### Phase 2: Feature Engineering (US2)
*   **T021**: Implement Molecular Descriptor Generation. Generate multiple descriptors per monomer using RDKit.
*   **T022**: Implement Interaction Features. Compute weighted averages and absolute differences.
*   **T027**: Implement Fox/Gordon-Taylor Equations. Compute as **Baseline Predictions** (not predictors). Save to `data/processed/baselines.csv`. Do NOT include in feature matrix.
*   **T028a**: Implement VIF Calculation. Calculate VIF for all predictors. Flag pairs > 5.0. (Output: diagnostic report only). Located in `code/02_features.py`.
*   **T023a**: Unit test for VIF calculation logic in `tests/test_features.py`.

### Phase 3: Model Training & Validation (US3)
*   **T030**: Implement Nested Cross-Validation (x5). Outer loop for unbiased testing, inner loop for tuning. Stratify by data source.
*   **T031**: Implement Residual Prediction Workflow. Train Linear Baseline and ML models on **Residuals** (Observed - Physics Baseline).
*   **T035**: Implement VIF Sensitivity Analysis. Re-train models excluding highest-VIF features and compare MAE. (Located in `code/03_train.py`).
*   **T036**: Unit test for Sensitivity Analysis logic in `tests/test_train.py`.
*   **T037**: Implement Stability Runs. Execute multiple independent training runs with different seeds.
*   **T038**: Implement Elastic Net Fallback. If N < 200, switch to Elastic Net with L1 regularization instead of aggressive VIF pruning.

### Phase 4: Reporting & Analysis
*   **T041**: Generate MAE/p-value Summary Table. Aggregate NCV results and paired t-test/Permutation p-values (on outer loop predictions).
*   **T042**: Generate SHAP Summary Plot. Visualize feature importance for top predictions.
*   **T043**: Generate Feature Stability Chart. Aggregate results from 5 runs (T037) to compute 'frequency of top-10 features' (SC-003).
*   **T044**: Generate Causal Disclaimer. Explicitly state that SHAP values reflect predictive contribution, not causality.
*   **T045**: Refactor `code/03_train.py` to implement batched SHAP calculation and verify runtime < 5h on local runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Nested Cross-Validation** | Required to eliminate selection bias and address power issues for N=100-200. | Simple train/val/test split is statistically underpowered and biased for model selection. |
| **Residual Prediction** | Prevents tautological validation where ML re-learns physics equations. | Training on raw values with physics features allows linear baseline to trivially fit, making ML comparison meaningless. |
| **VIF Sensitivity Re-training** | FR-008 requires comparing model metrics after excluding high-VIF features. | A simple feature exclusion without re-training does not measure the *impact* on model performance. |
| **Stability Analysis (5 runs)** | SC-003 requires identifying descriptors stable across 5 independent runs. | A single run cannot establish statistical stability or robustness of feature importance rankings. |
| **Sensitivity Sweep (Tolerance)** | Assumption requires validating the ±0.02 weight-fraction tolerance. | A fixed threshold without sweeping {0.01, 0.02, 0.05} risks biasing the dataset quality metric (SC-004). |
| **Source-Stratified CV** | Addresses domain shift between Polymer DB, NIST, and MP. | Random CV may train on one source and test on another, leading to inflated performance estimates. |
| **Elastic Net Fallback** | Mitigates 'Small-N, High-P' risk where VIF removal destroys signal. | Aggressive VIF pruning in small datasets can remove the only signal, leading to false negatives. |
| **Permutation Testing** | Standard t-test is underpowered for N < 500. | Parametric tests assume normality and large N; permutation testing is robust for small samples. |

## Success Criteria Mapping

*   **SC-001**: Measured via **Nested Cross-Validation** outer-loop MAE (replaces static split).
*   **SC-002**: **Permutation Testing** (10k iterations) on absolute errors of **Residual Predictions** (ML vs Linear Baseline) on outer-loop folds (replaces t-test for N < 500).
*   **SC-003**: Aggregated via **T043** (Stability Chart) from 5 independent runs.
*   **SC-004**: Validated via **T020** (Sensitivity Sweep) across tolerance values.
*   **SC-005**: Validated via **T045** (Runtime verification).

## Edge Cases & Mitigations

*   **API Rate Limits**: Exponential backoff (a bounded number of retries). If failed, pipeline halts.
*   **Missing SMILES**: Rows with missing SMILES for components > 0.05 weight fraction are excluded. If > 50% of entries are excluded, pipeline halts with `DataInsufficiencyError`.
*   **Data Insufficiency**: If N < 100, pipeline halts with `DataInsufficiencyError` (T019).
*   **No Verified Source**: If APIs fail to provide combined SMILES+Properties, pipeline halts with `DataInsufficiencyError`. No manual fallback allowed.
