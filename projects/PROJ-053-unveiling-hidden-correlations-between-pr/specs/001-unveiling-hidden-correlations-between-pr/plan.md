# Implementation Plan: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

**Branch**: `001-unveiling-hidden-correlations` | **Date**: 2026-07-14 | **Spec**: `specs/001-unveiling-hidden-correlations/spec.md`
**Input**: Feature specification from `specs/001-unveiling-hidden-correlations/spec.md`

## Summary

This project implements a Gaussian Process Regression (GPR) pipeline to model non-linear relationships between additive manufacturing (AM) processing parameters (laser power, scan speed, layer thickness) and mechanical properties (yield strength, ductility) in alloys. The system ingests the **NIST AM-Bench** dataset (verified open source), performs rigorous preprocessing (median imputation, min-max normalization), trains an RBF-kernel GPR model with 5-fold cross-validation, and generates uncertainty-aware visualizations to identify data-sparse regimes. The implementation strictly adheres to the project constitution regarding reproducibility, data hygiene, and physical measurement independence.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn==1.4.0`, `pandas==2.2.0`, `numpy==1.26.0`, `matplotlib==3.8.0`, `scipy==1.12.0`, `requests==2.31.0`, `pyyaml==6.0.1`, `seaborn==0.13.0`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `results/`)  
**Testing**: `pytest==8.1.0`  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, ~7 GB RAM)  
**Project Type**: Data Science Pipeline / CLI Tool  
**Performance Goals**: End-to-end runtime < 4 hours on 500 samples; Memory usage < 6 GB during GPR training.  
**Constraints**: No local GPU; datasets must be open and directly downloadable; strict adherence to dataset-variable fit (no synthetic data).  
**Scale/Scope**: ~ experimental observations per alloy type.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | Random seeds pinned (`np.random.seed(42)`, `random.seed(42)`); `requirements.txt` pins all versions; CI runs isolated virtualenv. |
| **II. Verified Accuracy** | ✅ Pass | **NIST AM-Bench** (Zenodo) cited as the verified source; no fabricated sources. |
| **III. Data Hygiene** | ✅ Pass | Raw data preserved in `data/raw/`; transformations write to `data/processed/` with new filenames; checksums recorded in `state/`. |
| **IV. Single Source of Truth** | ✅ Pass | All metrics in `results/` JSON derived programmatically from `code/`; no hand-typed values in docs. |
| **V. Versioning Discipline** | ✅ Pass | Content hashes tracked in `state/projects/PROJ-053...yaml`; artifact changes trigger state updates. |
| **VI. Non-Linear Process-Property Mapping** | ✅ Pass | GPR with RBF kernel selected; Linear Baseline used for comparison via Permutation Test (SC-001). |
| **VII. Physical Measurement Independence** | ✅ Pass | Pipeline verifies predictor (process) and target (property) columns are distinct and not mathematically derived (e.g., no VED calculation in source). |

## Project Structure

### Documentation (this feature)

```text
specs/001-unveiling-hidden-correlations/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── visualization.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Entry point orchestrating the pipeline
├── data_loader.py       # Dataset download, validation, and source independence check
├── preprocessing.py     # Imputation, normalization, encoding
├── models/
│   ├── __init__.py
│   ├── gpr_model.py     # GPR training, CV, and prediction
│   └── baseline.py      # Linear regression baseline
├── analysis/
│   ├── __init__.py
│   ├── importance.py    # Permutation importance
│   └── uncertainty.py   # Uncertainty quantification logic
├── visualization/
│   ├── __init__.py
│   └── plots.py         # Contour and heatmap generation
└── utils/
    ├── __init__.py
    └── io_utils.py      # JSON/CSV I/O and logging

tests/
├── __init__.py
├── test_data_loader.py
├── test_preprocessing.py
├── test_models.py
└── test_visualization.py

data/
├── raw/                 # Downloaded raw datasets (checksummed)
└── processed/           # Cleaned, normalized CSVs

results/
├── metrics.json         # R², RMSE, MAE
├── runtime.json         # Total pipeline runtime
├── importance_ranking.json
├── residual_analysis.json
├── high_uncertainty_regions.csv
└── plots/               # Generated PNGs
```

**Structure Decision**: Single-project structure selected. The pipeline is linear (Download -> Preprocess -> Train -> Analyze -> Visualize), making a monolithic `code/` directory with modular sub-packages appropriate. No separate frontend/backend is required as this is a batch processing scientific tool.

## Task Summary (Merged for Efficiency)

The following tasks represent the merged, high-level logical units of work to reduce dependency noise while satisfying all requirements.

- **T001**: **Initialize Environment**: Set up virtualenv, install dependencies, pin seeds.
- **T005**: **Implement Strict Data Loader**: Download NIST AM-Bench. Validate `len(df) >= 50`. Check for required columns. Verify source independence (target not derived from predictors). **Halt** with clear error if validation fails.
- **T016**: **Filter, Impute, Normalize, and Save Intermediate Dataset**: Load raw data. Drop zero-variance features. Median impute missing values. Min-max normalize numeric features. One-hot encode alloy types. Save to `data/processed/processed.csv`.
- **T029**: **Calculate and Save Metrics**: Train GPR (5-fold CV) and Linear Baseline. Calculate R², RMSE, MAE. Calculate `rmse_percentage = (RMSE / (max(y) - min(y))) * 100`. Perform Permutation Test to compare R² scores. Save to `results/metrics.json`.
- **T031**: **Load, Validate, and Correlate Baseline**: Load `data/baseline_importance.json` (checked first). If missing, load `data/literature_baseline_importance.json`. If neither exists, skip correlation. Calculate Spearman's rank correlation between model's permutation importance and baseline. Save correlation score to `results/importance_correlation.json`.
- **T045**: **Generate Uncertainty Flags**: Identify regions where σ > 2× median. Write coordinates to `results/high_uncertainty_regions.csv`. Generate uncertainty heatmap.
- **T047**: **Profile Memory and Save Report**: Profile peak memory usage during GPR training. Save to `results/memory_profile.json`.
- **T053**: **Implement Source Independence Validation**: (Integrated into T005) Verify no mathematical derivation of target from predictors.
- **T054**: **Update Metrics Documentation**: Ensure all metrics in `results/` are documented in `quickstart.md` and `data-model.md`.
- **T055**: **Generate Residual Analysis Report**: Analyze residuals for heteroscedasticity. If detected, flag in `results/residual_analysis.json`. (Triggers T057 if needed).
- **T057**: **Implement Sparse GPR Fallback**: If N > 500 or heteroscedasticity detected, switch to Sparse GPR or Weighted GPR.
- **T058**: **Implement Source Independence Validation**: (Integrated into T005).
- **T061**: **Measure and Log Runtime**: Wrap the entire pipeline execution in a timer. Log total runtime to `results/runtime.json` to satisfy SC-005.

## Complexity Tracking

No violations detected. The complexity is managed by strict task merging (addressing previous panel concerns) and clear separation of concerns between data loading, modeling, and visualization.

## Assumptions

- The **NIST AM-Bench** dataset (Zenodo) contains the specific variables required: laser power, scan speed, layer thickness, yield strength, and ductility.
- **Dataset-variable fit**: If the chosen dataset lacks "fatigue life" data, the analysis will be restricted to "yield strength" and "ductility" only, and this scope reduction will be documented in the final report.
- The dataset size (N ≥ 50) is sufficient for training a GPR model with an RBF kernel without overfitting on a CPU-only environment.
- The relationships between processing parameters and mechanical properties are non-linear and continuous, justifying the use of Gaussian Process Regression over linear models.
- The "free CPU" CI runner (2 cores, ~7 GB RAM) can handle the memory footprint of a GPR model trained on 50-500 samples with standard precision (no 8-bit quantization or GPU acceleration required).
- All mechanical property values in the dataset are positive and physically plausible (e.g., yield strength > 0), requiring no complex outlier removal beyond standard variance checks.
- The "uncertainty" quantified by the GPR model (predictive variance) is a valid proxy for **epistemic uncertainty** (lack of training data in that region) but does **not** capture **aleatoric uncertainty** (inherent noise in the physical measurement process). In AM, mechanical properties have high intrinsic variance due to microstructural defects; the model identifies data-sparse regimes, not necessarily regimes with high physical noise.