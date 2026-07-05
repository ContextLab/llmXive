# Implementation Plan: Machine Learning Prediction of Crack Propagation Rates in Metals

**Branch**: `001-crack-propagation-ml` | **Date**: 2026-07-04 | **Spec**: `specs/001-crack-propagation-ml/spec.md`
**Input**: Feature specification from `/specs/001-crack-propagation-ml/spec.md`

## Summary

This feature implements a machine learning pipeline to predict fatigue crack growth rates ($da/dN$) in metals using stress intensity factor range ($\Delta K$), material composition, and heat-treatment descriptors. The implementation establishes a physics-based baseline (Paris Law) via **alloy-stratified linear regression**, then augments it with tree-based ensemble models (Random Forest, XGBoost) to quantify the unique variance explained by engineering descriptors. The analysis uses **change-point detection** for regime identification and **permutation tests** for statistical significance, ensuring all computations are feasible on CPU-only GitHub Actions runners.

**Spec Exception & FR-005 Resolution**: The source specification (FR-005) lists "nested model F-test" as an option. This plan explicitly rejects the F-test as statistically invalid for comparing linear and non-linear models (tree-based ensembles are non-nested). The implementation will **only** use Permutation Tests. A kickback to the specification is required to remove the F-test option to resolve this conflict. The plan proceeds with the scientifically valid method.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `xgboost`, `optuna`, `matplotlib`, `seaborn`, `pyyaml`, `ruptures` (for change-point detection), `jsonschema` (for data validation)  
**Storage**: 
- **Raw**: `data/raw/` (immutable, checksummed files fetched from verified URLs).
- **Processed**: `data/processed/` (derived, encoded files).
- **Prerequisite**: `data/` is populated *only after* the `code/main.py --step download` executes a schema validation against `contracts/dataset.schema.yaml`. If validation fails, the pipeline halts.
**Testing**: `pytest` (unit tests for data ingestion, integration tests for model training)  
**Target Platform**: Linux (GitHub Actions free-tier: CPU cores, limited RAM, no GPU)  
**Project Type**: Data Science Pipeline / Research Tool  
**Performance Goals**: Full pipeline execution ≤ 6 hours; Memory usage < 7 GB; No GPU dependencies.  
**Constraints**: Strict CPU-only execution; no deep learning frameworks; dataset sampling if necessary to fit RAM.  
**Scale/Scope**: Single dataset ingestion (FCGEC), k-fold cross-validation, regime-specific analysis.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: **COMPLIANT**. Plan mandates pinned `requirements.txt`, random seed setting in `code/`, and canonical dataset fetching from verified URLs.
2.  **II. Verified Accuracy**: **COMPLIANT**. Plan includes a **Data Validation** step using `jsonschema` that halts execution if the verified dataset lacks required engineering descriptors (composition, heat treatment). No external URLs will be invented.
3.  **III. Data Hygiene**: **COMPLIANT**. Plan enforces checksumming of raw data, immutable raw files, and versioned derived files in `data/`.
4.  **IV. Single Source of Truth**: **COMPLIANT**. All metrics ($R^2$, $\Delta R^2$, p-values) will be generated programmatically from `code/` outputs, not hand-typed.
5.  **V. Versioning Discipline**: **COMPLIANT**. Implementation will use content hashes for data and code artifacts to trigger state updates.
6.  **VI. Engineering Descriptor Validation**: **COMPLIANT**. The core methodology (Baseline vs. Augmented model comparison via Permutation Test) is explicitly defined to isolate variance from composition/heat-treatment.
7.  **VII. Domain Regime Granularity**: **COMPLIANT**. The plan includes specific phases for data-driven regime identification (Change-Point Detection) and generating local metrics with sliding window stability checks on the boundaries.

## Project Structure

### Documentation (this feature)

```text
specs/001-crack-propagation-ml/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/001-crack-propagation-ml/
├── code/
│   ├── __init__.py
│   ├── main.py              # Entry point orchestrating the pipeline
│   ├── config.py            # Hyperparameters, seeds, paths
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py        # Ingestion from verified URLs with schema check
│   │   ├── preprocessor.py  # Cleaning, imputation, encoding
│   │   └── split.py         # Stratified splitting (with fallback)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── baseline.py      # Linear Regression (Paris Law, stratified)
│   │   ├── augmented.py     # RF/XGBoost (with fallback logic)
│   │   └── trainer.py       # Optuna tuning, 5-fold CV
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── regimes.py       # Regime identification (change-point) & local R2
│   │   ├── sensitivity.py   # Stability analysis (bootstrapping/boundary perturbation)
│   │   └── viz.py           # PDPs, regime maps
│   └── utils/
│       ├── __init__.py
│       └── stats.py         # Permutation tests, residual decomposition
├── data/
│   ├── raw/                   # Downloaded checksummed files (populated post-verify)
│   └── processed/             # Cleaned, imputed, encoded data
├── tests/
│   ├── unit/
│   │   ├── test_loader.py
│   │   └── test_preprocessor.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: Selected a modular Python package structure (`code/` submodules) to separate data loading, modeling, and analysis. `main.py` acts as the orchestrator. This ensures testability and adherence to the "Single Source of Truth" principle by isolating logic. The directory layout supports the required phased execution: Load -> Verify -> Clean -> Baseline -> Augmented -> Regime Analysis.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Optuna for Hyperparameter Tuning** | Required by FR-004 to rigorously tune $n\_estimators$, $max\_depth$, $learning\_rate$ for XGBoost/RF. | Grid search is computationally too expensive for the limited CI time on 2 cores.; random search lacks the efficiency of Optuna's TPE sampler. |
| **Stratified Splitting by Alloy Family** | Required to ensure the model generalizes across different material types (Edge Case: unseen alloy families). | Random splitting could lead to data leakage where similar alloys appear in both train and test, inflating performance metrics artificially. **Fallback**: If alloy family metadata is missing, the plan defaults to random splitting (as defined in Research). |
| **Regime-Specific Analysis (Change-Point)** | Required by FR-006/007 and Constitution Principle VII to identify where Paris Law fails objectively. | Arbitrary binning introduces high variance and "p-hacking" risk. Change-point detection provides a data-driven, reproducible boundary definition. |
| **Permutation Test** | Required to validly compare linear baseline vs. non-linear tree models (Scientific Soundness). | F-test is statistically invalid for non-nested models. Permutation tests make no distributional assumptions about the error terms. |
| **Fallback Logic (Composition/Heat-Treatment)** | Required to handle missing data without halting the entire project (Research Fallback Strategy). | A hard halt on missing data creates a single point of failure. The pipeline must gracefully degrade to "Composition-Only" or "Heat-Treatment-Only" modes if one descriptor set is missing. |

## FR-005 Conflict Resolution

The source specification (FR-005) states: "System MUST ... perform a nested model F-test or permutation test".
This plan implements **only** the Permutation Test.
**Reasoning**: The F-test assumes nested linear models with Gaussian errors. Comparing a Linear Regression to XGBoost violates these assumptions, rendering the F-test p-values invalid.
**Action**: The plan proceeds with the statistically valid method (Permutation Test). The specification must be updated to remove the F-test option to align with scientific standards.

## Fallback Strategy Implementation

The plan explicitly implements the fallback logic defined in Research:
1.  **Check**: After data ingestion, verify presence of `composition` and `heat_treatment` columns.
2.  **Scenario A (Missing Heat Treatment)**: Proceed with "Composition-Only" model. Log warning. Update `data-model.md` to reflect reduced feature set.
3.  **Scenario B (Missing Composition)**: Proceed with "Heat-Treatment-Only" model. Log warning.
4.  **Scenario C (Both Missing)**: Halt execution with fatal error. This scenario is not recoverable.
5.  **Code**: `code/models/augmented.py` will contain conditional logic to select features based on availability.