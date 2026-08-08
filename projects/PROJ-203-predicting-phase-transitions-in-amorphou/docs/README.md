# Predicting Phase Transitions in Amorphous Solids Using Machine Learning

**Project ID**: PROJ-203
**Scope**: Pilot Study (N=24 compositions)
**Goal**: Predict glass transition temperature (Tg) and crystallization propensity using structural descriptors derived from molecular dynamics simulations.

## Overview

This project implements a machine learning pipeline to:
1. Generate molecular dynamics (MD) trajectories for 24 amorphous solid compositions.
2. Extract short-range structural descriptors (RDF peaks, bond angles, coordination numbers).
3. Train Random Forest models to predict Tg (regression) and crystallization propensity (classification).
4. Perform interpretability analysis (SHAP, partial dependence) to identify universal vs. family-specific predictors.
5. Validate results with null models, permutation tests, and stability analysis (LOO jackknife).

## Pilot Study Scope

- **Compositions**: 24 stratified samples (oxide, sulfide, organic families).
- **Performance Targets**:
 - RMSE ≤ 15 K (validated via Null Model/Permutation Tests)
 - ROC-AUC > 0.7 (validated via Null Model/Permutation Tests)
- **Statistical Validity**: Due to small sample size (N=24), all performance claims are backed by:
 - Null model (mean predictor) comparison
 - Permutation tests for statistical significance
 - LOO jackknife for stability confidence intervals
 - Collinearity analysis (VIF > 5 threshold)

## Quickstart

See [docs/quickstart.md](docs/quickstart.md) for step-by-step instructions to run the pipeline.

## Project Structure

```
PROJ-203-predicting-phase-transitions-in-amorphou/
├── code/
│ ├── main.py # Pipeline entry point
│ ├── config.py # Configuration management
│ ├── setup_directories.py # Directory initialization
│ ├── data/ # Data pipeline modules
│ │ ├── validate_literature_subset.py
│ │ ├── simulate.py
│ │ ├── descriptor_utils.py
│ │ ├── merge.py
│ │ └── finalize_dataset.py
│ ├── models/ # Model training & analysis
│ │ ├── train.py
│ │ ├── generate_metrics_report.py
│ │ ├── generate_shap_plots.py
│ │ ├── partial_dependence_analysis.py
│ │ ├── stability_analysis.py
│ │ ├── sensitivity_analysis.py
│ │ ├── collinearity_analysis.py
│ │ ├── multiple_comparison_correction.py
│ │ └── null_model_analysis.py
│ └── utils/ # Utility functions
│ ├── logging_config.py
│ ├── validators.py
│ ├── plots.py
│ └── timeout_enforcer.py
├── data/
│ ├── raw/ # Raw data (literature_subset.csv, pilot_compositions.csv)
│ ├── processed/ # Intermediate and final datasets
│ └── logs/ # Simulation and exclusion logs
├── models/ # Trained model artifacts (.pkl)
├── artifacts/
│ ├── models/ # Additional model artifacts
│ ├── figures/ # Generated plots
│ └── reports/ # Timing and validation reports
├── docs/
│ ├── README.md # This file
│ ├── quickstart.md # Execution guide
│ └── reports/ # Final reports (metrics, SHAP, etc.)
└── tests/ # Unit and integration tests
```

## Key Features

### 1. Virtual Alignment Protocol (FR-008)
Aligns MD simulation timescales with experimental cooling rates via a scaling factor:
```
S = dsc_cooling_rate / md_cooling_rate
```
Structural descriptors are adjusted using this factor to ensure physical consistency.

### 2. Small Sample Size Mitigation
- **Null Model**: Mean predictor baseline to establish significance threshold.
- **Permutation Test**: Random shuffling of labels to compute p-values.
- **LOO Jackknife**: Leave-One-Out resampling for stability confidence intervals (replaces bootstrapping for N=24).
- **Bonferroni Correction**: Controls family-wise error rate for multiple comparisons.

### 3. Interpretability
- **SHAP Analysis**: Ranks feature importance per chemical family.
- **Partial Dependence Plots**: Visualizes monotonic/non-linear relationships.
- **Collinearity Report**: Flags predictors with VIF > 5.

### 4. Timeout Enforcement
- **6-hour wall-clock limit** enforced by `code/utils/timeout_enforcer.py`.
- Graceful shutdown with partial results if limit exceeded.
- Timing logs saved to `data/logs/` and `docs/reports/pipeline_timing.json`.

## Data Sources

- **Literature Subset**: `data/raw/literature_subset.csv` (curated experimental Tg, Tx, cooling rates).
- **Pilot Compositions**: `data/raw/pilot_compositions.csv` (24 stratified samples).
- **Potentials**: OpenKIM interatomic potentials (verified at runtime).

**Note**: All data must be obtained from verified real sources. Synthetic/fake data is strictly prohibited.

## Performance Targets (Pilot)

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| RMSE (Tg) | ≤ 15 K | Null Model/Permutation Test |
| ROC-AUC (Crystallization) | > 0.7 | Null Model/Permutation Test |
| Pipeline Runtime | ≤ 6 hours | Timeout Enforcer |

## Contributing

1. Ensure all data is real and sourced from verified repositories.
2. Run `code/main.py` to execute the full pipeline.
3. Verify outputs in `data/processed/`, `models/`, and `docs/reports/`.
4. Update `docs/quickstart.md` if new steps are added.

## License

[Insert License Here]

## References

- Design documents: `specs/001-predicting-phase-transitions/`
- Project plan: `plan.md`
- Feature specification: `spec.md`
