# Implementation Plan: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

**Branch**: `001-predict-cold-work-kinetics` | **Date**: 2026-07-13 | **Spec**: `specs/001-predict-cold-work-kinetics/spec.md`
**Input**: Feature specification from `/specs/001-predict-cold-work-kinetics/spec.md`

## Summary

This project implements a predictive modeling pipeline to analyze the impact of cold work percentage and alloy composition (Mg, Si, Cu, Mn) on recrystallization kinetics (time-to-peak softening) in aluminum alloys. The primary approach involves generating a deterministic synthetic dataset (seed=42) to serve as the ground truth, engineering interaction features to capture pinning effects, training a Random Forest Regressor, and performing statistical significance testing via a **Delta-Permutation Test** and **SHAP Interaction Values**. The pipeline is strictly constrained to CPU-only execution on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: pandas, scikit-learn, numpy, shap, pytest  
**Storage**: Local CSV/Parquet files in `data/` directory  
**Testing**: pytest (unit and integration tests)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data Science / Computational Materials Science CLI  
**Performance Goals**: Complete full pipeline (ingest, train, test, analyze) within 6 hours; Memory usage < 4GB.  
**Constraints**: CPU-only; Dataset size capped at <10,000 rows; No causal claims; No Arrhenius normalization of target.  
**Scale/Scope**: Synthetic dataset generation; Single model training; Statistical validation of interaction terms.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds are pinned in the synthetic generator and model training.. All code is in `code/`. |
| **II. Verified Accuracy** | **Pass** | Citations will be validated against primary sources (NIST, literature) via the Reference-Validator. No fabricated URLs. |
| **III. Data Hygiene** | **Pass** | Raw synthetic data will be checksummed. Transformations (cleaning, feature engineering) will produce new files in `data/`. |
| **IV. Single Source of Truth** | **Pass** | All metrics (R², MAE, p-values) will be derived directly from the `code/` execution logs and stored in `data/`. |
| **V. Versioning Discipline** | **Pass** | Content hashes will be recorded in the state YAML for every data artifact. |
| **VI. Interaction-Feature Explicitness** | **Pass** | The plan explicitly requires engineering `cold_work * Mn_content` and similar terms. **Crucially, the Permutation Test (comparing Additive vs. Interaction models) and SHAP Interaction Values are the specific mechanisms mandated to validate this principle.** |
| **VII. Computational Boundedness for CI/CD** | **Pass** | Random Forest (CPU) and dataset size <10k rows are selected to fit within 2-CPU/4GB RAM constraints (Constitution Principle VII). |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-cold-work-kinetics/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── metrics.schema.yaml
│   └── model-output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/code/
├── __init__.py
├── config.py            # Configuration (seeds, paths, thresholds)
├── data/
│   ├── __init__.py
│   ├── generate_synthetic.py  # Synthetic generator (seed=42)
│   ├── ingest.py        # Cleaning and imputation logic
│   └── engineer.py      # Feature engineering (interactions)
├── models/
│   ├── __init__.py
│   ├── train.py         # Random Forest training & CV
│   └── evaluate.py      # Delta-Permutation Test & SHAP Interaction analysis
├── utils/
│   ├── __init__.py
│   └── validators.py    # Data validation and outlier clipping
└── main.py              # Pipeline orchestrator

tests/
├── __init__.py
├── test_data_generation.py
├── test_feature_engineering.py
├── test_model_training.py
└── test_statistical_tests.py
```

**Structure Decision**: Selected the "Single Project" structure with modular separation (`data`, `models`, `utils`) to maintain clarity between data generation, feature engineering, and statistical analysis. This aligns with the Constitution's requirement for reproducibility and single-source-of-truth.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Interaction Feature Engineering** | Essential to test the "pinning effect" hypothesis (Constitution Principle VI). | A simple additive model (cold work + composition) would fail to capture the non-linear modulation of kinetics by alloying elements, rendering the research question unanswerable. |
| **Delta-Permutation Test** | Required to establish statistical significance of interaction terms beyond standard feature importance. | Standard permutation importance on a single model does not isolate the *incremental* gain of interactions over a baseline additive model. |
| **SHAP Interaction Values** | Required to handle collinearity between main effects and interaction terms. | Standard feature importance (Gini/MDI) is biased towards correlated features and cannot isolate the unique contribution of the interaction term. |
| **Synthetic Data Generation** | No verified public dataset exists with the specific combination of cold work %, specific alloying elements, and time-to-peak softening. | Using a generic dataset would require imputation of critical variables, introducing uncontrolled bias and violating Data Hygiene principles. |
| **Dataset Size Cap (<10k)** | Required to fit within CI/CD memory constraints (Constitution Principle VII). | Larger datasets would exceed the RAM limit of the GitHub Actions free-tier runner, causing execution failure. |