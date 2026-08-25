# Implementation Plan: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

**Branch**: `001-predict-poissons-ratio` | **Date**: 2026-07-05 | **Spec**: `specs/001-predict-poissons-ratio/spec.md`

## Summary

This feature implements a reproducible machine learning pipeline to predict the Poisson's ratio of monolithic aluminum alloys based on the atomic fractions of five key alloying elements: Copper (Cu), Magnesium (Mg), Silicon (Si), Zinc (Zn), and Manganese (Mn). The approach utilizes Isometric Log-Ratio (ILR) transformation to handle the compositional nature of the data (unit-sum constraint) before training a Random Forest regressor. The pipeline strictly adheres to the project constitution, ensuring data hygiene, reproducibility, and the correct framing of findings as associational rather than causal.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `joblib`, `pyyaml`, `datasets` (HuggingFace), `numpy`, `scipy`  
**Storage**: Local file system (`data/raw`, `data/processed`, `models`, `results`)  
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for data transformations)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)  
**Project Type**: Data Science / Computational Materials Science  
**Performance Goals**: Complete pipeline execution (data fetch to report) within 6 hours on CPU; model training < 1 hour.  
**Constraints**: No GPU available for training; dataset must be streamed or sampled to fit available RAM; strict adherence to ILR transformation for compositional data.  
**Scale/Scope**: Target dataset size < 1000 entries (based on availability in `materials/alloy-elastic` dataset).  
**Data Source**: Primary source is the verified HuggingFace dataset `materials/alloy-elastic`.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All random seeds pinned in `code/`; `requirements.txt` pins versions; data fetched from canonical HuggingFace ID `materials/alloy-elastic`. |
| **II. Verified Accuracy** | **Pass** | Citations in `research.md` restricted to the specific verified dataset `materials/alloy-elastic`. |
| **III. Data Hygiene** | **Pass** | Raw data checksummed; derived files written to new paths; no in-place modification. |
| **IV. Single Source of Truth** | **Pass** | All metrics in `results/final_report.md` derived programmatically from `data/processed/*.json`. |
| **V. Versioning** | **Pass** | Artifact hashes recorded in state YAML upon completion. |
| **VI. Unit Consistency** | **Pass** | Explicit normalization step in `code/data_processing.py` ensures GPa and atomic fractions. |
| **VII. Compositional Attribution** | **Pass** | ILR transformation and Permutation Importance logic implemented; feature importance ranking mandatory. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-poissons-ratio/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── model_metrics.schema.yaml
    └── collinearity_diagnostic.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Entry point orchestrating the pipeline
├── data_processing.py   # Download, filter, normalize, ILR transform
├── modeling.py          # Train RF, CV, save model, compute metrics
├── analysis.py          # VIF calculation (diagnostic), Permutation Importance
└── utils.py             # Logging, checksumming, path handling

data/
├── raw/                 # Downloaded raw JSON/Parquet (immutable)
├── processed/           # Cleaned CSV/JSON, metrics (derived)
└── checksums.txt        # SHA256 of raw files

models/
└── rf_model.pkl         # Trained Random Forest (joblib)

results/
├── feature_importance_summary.json
├── collinearity_diagnostic.json
├── model_metrics.json
└── final_report.md
```

**Structure Decision**: Single-project structure selected to minimize overhead for a data-science workflow. All logic is modularized into `code/` scripts to ensure end-to-end reproducibility without notebook dependency.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **ILR Transformation** | Essential for compositional data (atomic fractions sum to 1). | Standard normalization (min-max) or log-ratio without ILR violates the unit-sum constraint, leading to spurious correlations and invalid regression coefficients. |
| **VIF Diagnostic** | Required to demonstrate the 'closure problem' (mathematical necessity of high VIF). | Skipping VIF would hide the justification for ILR; VIF > 5 is expected and confirms the need for transformation, not a data error. |
| **Permutation Importance** | RF importance cannot be back-transformed; permutation on ILR space is valid. | Direct back-transformation of RF gain is mathematically invalid for non-linear models. |
| **Repeated CV** | Single split introduces high variance in small datasets. | Single 80/20 split is unreliable for <1000 samples; Repeated CV provides confidence intervals. |
| **Separate Model/Analysis Scripts** | Ensures clear separation between prediction (modeling) and interpretation (analysis). | Monolithic script would obscure the dependency chain and make unit testing of specific transformations difficult. |

## Phase Plan

### Phase 0: Data Acquisition & Verification
- **Goal**: Secure the dataset from the verified source.
- **Steps**:
  1.  Load data from HuggingFace dataset `materials/alloy-elastic`.
  2.  Compute checksums of the downloaded dataset.
  3.  Filter for monolithic Al alloys with non-missing Poisson's ratio and required elements (Cu, Mg, Si, Zn, Mn).
  4.  Verify unit consistency (GPa, atomic fractions).
  5.  **Step 4.5**: Verify Poisson's ratio independence (check `is_independent_measurement` flag or source method).
  6.  **Gate**: If filtered count < 50, halt with error "Insufficient data (< 50 samples) for Repeated 5-Fold CV".

### Phase 1: Data Cleaning & Feature Engineering
- **Goal**: Prepare data for modeling.
- **Steps**:
  1.  Normalize units (GPa, atomic fractions).
  2.  Apply exclusion rule: sum of major elements < 0.95.
  3.  Apply ILR transformation to predictors (Cu, Mg, Si, Zn, Mn).
  4.  Split data for Repeated K-Fold CV (no single held-out set).

### Phase 2: Model Training & Validation
- **Goal**: Fit the Random Forest.
- **Steps**:
  1.  Train RF with **Repeated K-Fold Cross-Validation**.
  2.  Compute mean CV-MAE and % Confidence Interval.
  3.  Save model to `models/rf_model.pkl`.
  4.  Save metrics to `data/processed/model_metrics.json`.

### Phase 3: Diagnostic & Interpretation
- **Goal**: Extract insights and check validity.
- **Steps**:
  1.  **Step 3.1**: Compute VIF on raw features to demonstrate the 'closure problem' (expect VIF > 5).
  2.  **Step 3.2**: Generate `collinearity_diagnostic.json` with VIF scores and flag (always True for raw compositional data).
  3.  Compute Permutation Importance on ILR features.
  4.  Rank elements by magnitude of Permutation Importance.
  5.  Save diagnostics to `results/feature_importance_summary.json`.

### Phase 4: Reporting
- **Goal**: Generate final scientific report.
- **Steps**:
  1.  **Step 4.1**: Aggregate all metrics and diagnostics.
  2.  **Step 4.2**: Generate `results/final_report.md` with explicit enforcement of the phrase "associational (not causal)".
  3.  Validate report against `contracts/` schemas.

### Phase 5: Verification
- **Goal**: Ensure reproducibility.
- **Steps**:
  1.  Run `pytest` on contract tests.
  2.  Verify checksums.
  3.  Re-run pipeline on fresh env.