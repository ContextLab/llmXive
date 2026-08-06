# Implementation Plan: Predicting the Impact of Composition on the Density of Metallic Glasses

**Branch**: `001-predict-metallic-glass-density` | **Date**: 2026-07-21 | **Spec**: `specs/001-predict-metallic-glass-density/spec.md`
**Input**: Feature specification from `/specs/001-predict-metallic-glass-density/spec.md`

## Summary

This project implements a CPU-first regression pipeline to predict the bulk density of metallic glasses based on their elemental composition. The approach ingests the **UCI Machine Learning Repository: Metallic Glasses (ID: 469)**, engineers atomic-level descriptors (mean atomic mass, radius mismatch, packing efficiency proxy) using standard periodic table constants from the `mendeleev` library, and trains a Gradient Boosting Regressor (LightGBM) to predict the *residual* density (Actual - Linear Mixing Baseline). The plan explicitly enforces the Spec's hard-stop requirement: if the dataset yields <100 valid records, the system halts with `E_DATA_INSUFFICIENT`. No synthetic data is used.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `lightgbm`, `mendeleev` (for periodic table data), `shap`, `matplotlib`, `seaborn`, `ucimlrepo`, `miedema` (for mixing enthalpy)  
**Storage**: Local CSV files (`raw_data.csv`, `clean_data.csv`, `processed_data.csv`) and serialized model artifacts (`.pkl`)  
**Testing**: `pytest` (unit tests for feature engineering, integration tests for pipeline flow)  
**Target Platform**: GitHub Actions Free Tier (2 CPU cores, ~7 GB RAM, No GPU)  
**Project Type**: Data Science / Computational Materials Science CLI  
**Performance Goals**: Complete pipeline execution ≤ 2 hours; Model training < 600 seconds on CPU.  
**Constraints**: No GPU usage; Strict adherence to open-data availability (no gated datasets); Memory footprint < 7 GB.  
**Scale/Scope**: Dataset size target: ≥100 valid records. Feature set: multiple derived descriptors + raw mass fractions.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility (NON-NEGOTIABLE)**:
  - **Plan**: All random seeds will be pinned in `code/`. The dataset source URL (UCI ID: 469) will be hardcoded and checksummed in `state/`. The `requirements.txt` will pin exact versions.
  - **Compliance**: Full.
- **II. Verified Accuracy**:
  - **Plan**: The Reference-Validator Agent will verify all citations to periodic table constants and dataset sources. The `mendeleev` library is the **verified source** for periodic table constants. The baseline model (linear mixing rule) will be explicitly defined and cited against standard materials science literature.
  - **Compliance**: Full.
- **III. Data Hygiene**:
  - **Plan**: `raw_data.csv` will be downloaded and checksummed. `clean_data.csv` will be a derived artifact with a documented transformation log. No in-place modifications.
  - **Compliance**: Full.
- **IV. Single Source of Truth**:
  - **Plan**: All metrics (MAE, R²) in the final report will be generated programmatically from the model output, not hand-typed.
  - **Compliance**: Full.
- **V. Versioning Discipline**:
  - **Plan**: Every artifact (dataset, model, report) will carry a content hash in the project state file.
  - **Compliance**: Full.
- **VI. Amorphous Packing Descriptor Validation**:
  - **Plan**: The feature engineering module will explicitly derive "radius mismatch" and "packing efficiency" from the composition. The SHAP analysis will be mandated to quantify the relative contribution of **radius mismatch** and **packing efficiency** descriptors against the **Linear Mixing Rule** baseline (not Mean Atomic Mass).
  - **Compliance**: Full.
- **VII. Computational Screening Fidelity**:
  - **Plan**: The evaluation metric will prioritize MAE against a defined density threshold. If MAE > 0.1, the report will explicitly analyze the variance explained by **radius mismatch** using **sum of SHAP interaction values** and **Partial Dependence Plots (PDP)** as a distinct finding, per the constitution.
  - **Compliance**: Full.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-metallic-glass-density/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-461-predicting-the-impact-of-composition-on-/
├── data/
│   ├── raw/             # Downloaded raw files (checksummed)
│   └── processed/       # Cleaned and engineered datasets
├── code/
│   ├── __init__.py
│   ├── main.py          # Pipeline orchestrator
│   ├── data_ingestion.py
│   ├── feature_engineering.py
│   ├── baseline_model.py
│   ├── model_training.py
│   ├── evaluation.py
│   └── requirements.txt
├── tests/
│   ├── test_feature_engineering.py
│   └── test_pipeline.py
└── state/
    └── artifacts.yaml   # Checksums and hashes
```

**Structure Decision**: Selected the standard Data Science CLI structure (Option 1) to ensure a linear, reproducible pipeline flow from ingestion to reporting, fitting the CPU-only execution environment.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The complexity is low; the pipeline is linear. | N/A |

## Implementation Phases

### Phase 0: Data Acquisition
- **Task 0.1**: Download the UCI Machine Learning Repository "Metallic Glasses" dataset (ID: 469) using `ucimlrepo`.
- **Task 0.2**: Validate data integrity (checksum, row count, missing values). **Halt with `E_DATA_INSUFFICIENT` if total rows < 100.**
- **Task 0.3**: Verify that the loaded dataset contains non-linear deviations (i.e., not purely linear mixing) by checking the variance of the residual density.

### Phase 1: Feature Engineering & Baseline Calculation
- **Task 1.1**: Normalize elemental symbols (IUPAC).
- **Task 1.2**: Compute atomic properties (mass, radius, electronegativity) using `mendeleev`.
- **Task 1.3**: Calculate **Linear Mixing Rule Baseline**: $\rho_{baseline} = \sum (w_i \times \rho_i)$.
- **Task 1.4**: Compute derived features: Mean Atomic Mass, Mean Atomic Radius, Electronegativity Variance, Atomic Radius Mismatch ($\delta$), and Packing Efficiency Proxy ($P_{eff} = \delta \times \sqrt{|\Delta H_{mix}|}$).
- **Task 1.5**: Apply Centered Log-Ratio (clr) transform to compositional features to mitigate collinearity.
- **Task 1.6**: Calculate **Residual Target**: $y_{residual} = \rho_{actual} - \rho_{baseline}$.
- **Task 1.7**: Perform Variance Inflation Factor (VIF) check on derived features to ensure non-collinearity before modeling.

### Phase 2: Residual Modeling
- **Task 2.1**: Split data using Stratified K-Fold (k=5) based on the dominant element.
- **Task 2.2**: Train a **Null Model** (Dominant Element + Mean Atomic Mass) and a **Full Model** (Null + Packing Descriptors) using LightGBM.
- **Task 2.3**: Evaluate model performance on the test set (MAE, R²).
- **Task 2.4**: Perform **Nested F-Test** comparing Null vs. Full Model to validate SC-003 (statistical significance of packing descriptors).

### Phase 3: Interpretability & Validation
- **Task 3.1**: Generate SHAP summary plot to rank feature importance (specifically checking `radius mismatch` and `packing efficiency`).
- **Task 3.2**: Generate Partial Dependence Plots (PDP) for top features.
- **Task 3.3**: Perform Sensitivity Analysis (sweeping density thresholds).
- **Task 3.4**: If MAE > 0.1, generate a specific report section analyzing the variance explained by `radius mismatch` using **sum of SHAP interaction values** and PDPs.

### Phase 4: Reporting
- **Task 4.1**: Compile `report.html` with all visualizations, metrics, and analysis.
- **Task 4.2**: Save model artifacts and logs.

## Data Contingency Plan

- **Primary Source**: UCI Machine Learning Repository "Metallic Glasses" (ID: 469).
- **Fallback Source**: None. The project relies exclusively on this verified open source.
- **Trigger**: If UCI ID 469 is unavailable or < 100 rows.
- **Action**: Halt with `E_DATA_INSUFFICIENT`.
- **Failure**: If data is insufficient, the project cannot proceed. SC-001 and SC-003 are marked as "Not Measurable".
