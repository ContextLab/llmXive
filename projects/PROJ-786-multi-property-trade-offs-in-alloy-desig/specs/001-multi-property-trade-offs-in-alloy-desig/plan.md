# Implementation Plan: Multi-Property Trade-Offs in Alloy Design Using Public Compositional Data

**Branch**: `786-multi-property-trade-offs` | **Date**: 2026-07-08 | **Spec**: [link]
**Input**: Feature specification from `/specs/786-multi-property-trade-offs/spec.md`

## Summary

This project implements a computational pipeline to identify alloy compositions that optimize the trade-off between **Bulk Modulus** and **Shear Moduli** using DFT-derived data from the OQMD. The approach involves ingesting compositional data, encoding it with periodic descriptors, training Gradient Boosting surrogate models validated via Leave-One-System-Out Cross-Validation (LOSO-CV), and generating a Pareto frontier via NSGA-II. 

**Critical Methodological Update**: Instead of K-Means clustering on composition (which is tautological for finding property decoupling), the project now uses **Local Correlation Estimation (LCE)** with a stratified permutation null model to identify regions where Bulk and Shear moduli are genuinely uncorrelated.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `xgboost`, `scipy`, `deap`, `matplotlib`, `seaborn`, `datasets`, `pyyaml`, `numpy`  
**Storage**: Local filesystem (`data/processed/`, `data/raw/`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Complete full pipeline within 6 hours on 2-core CPU; LOSO-CV must finish within 4 hours.  
**Constraints**: 
- Strict convex hull constraint for synthetic generation.
- Minimum 500 valid entries required; exit with error code 1 if not met.
- No GPU usage (CPU-first strategy).
- All random seeds pinned for reproducibility.
- NSGA-II population size and generations tuned to fit time budget.
**Scale/Scope**: Dataset size: a substantial collection of entries from the OQMD elastic subset, comfortably exceeding the 500-entry minimum.

## Constitution Check

| Principle | Status | Evidence / Action Plan |
|-----------|--------|------------------------|
| **I. Reproducibility** | PASS | `requirements.txt` will pin versions. `random.seed(42)` set globally. Data fetched via `datasets.load_dataset` from verified HuggingFace URLs. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` will be cross-referenced with the "Verified datasets" block. No invented URLs. |
| **III. Data Hygiene** | PASS | `data/raw/` will store checksums. `data/processed/` will contain derived files with clear naming. No in-place modification. |
| **IV. Single Source of Truth** | PASS | All figures and stats in `paper/` will be generated directly from `data/processed/` artifacts. No manual entry. |
| **V. Versioning Discipline** | PASS | A `versioning_hook` script will compute SHA-256 hashes of all `data/processed/*` artifacts and update `state/projects/PROJ-786-...yaml` automatically after each pipeline stage. |
| **VI. Computational Surrogate Validity** | PASS | Plan explicitly includes `uncertainty_variance` calculation in `model_validation_report.json`. The Pareto optimizer **reads** this report to filter unreliable points. Claims of decoupling require stratified permutation test (p<0.05). |
| **VII. Convex Hull Constraint** | PASS | NSGA-II generation logic will include a `check_convex_hull` function. Points outside will be discarded. Additionally, a **Rule of Mixtures Validator** (Voigt/Reuss bounds) will reject physically impossible predictions. |

## Project Structure

### Documentation (this feature)

```text
specs/786-multi-property-trade-offs/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py                  # Orchestration: Ingestion -> Encoding -> Training -> Optimization -> Analysis
├── ingestion.py             # FR-001: Data loading and filtering
├── encoding.py              # FR-002: Composition encoding + periodic descriptors
├── training.py              # FR-003: Gradient Boosting + LOSO-CV
├── optimization.py          # FR-004: NSGA-II + Convex Hull + Rule of Mixtures check
├── analysis.py              # FR-005/FR-006: Local Correlation Estimation (LCE), Sensitivity analysis
├── utils/
│   ├── convex_hull.py       # Hull logic for FR-004
│   ├── ilr_transform.py     # ilr logic for FR-005
│   ├── periodic_props.py    # Element descriptors
│   └── rule_of_mixtures.py  # Voigt/Reuss bound calculation
└── config.py                # Paths, seeds, hyperparameters

data/
├── raw/                     # Downloaded OQMD files (checksummed)
└── processed/
    ├── encoded_alloys.csv
    ├── loso_test_points.csv
    ├── model_validation_report.json
    ├── sensitivity_analysis.csv
    └── robustness_validation.json

tests/
├── unit/
│   ├── test_encoding.py
│   └── test_convex_hull.py
├── integration/
│   └── test_ingestion_pipeline.py
└── conftest.py
```

**Structure Decision**: Single project structure selected to minimize overhead. All logic is modularized into `code/` scripts to ensure `main.py` can orchestrate the full pipeline without manual intervention.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Local Correlation Estimation (LCE)** | Required to avoid the tautology of K-Means clustering on composition. LCE identifies decoupling based on local property variance, not spatial compactness. | K-Means on composition groups points by similarity in composition, which inherently groups points with similar property correlations, making "decoupling" a statistical artifact. |
| **Voigt/Reuss Bounds** | Required by SC-003 to ensure physical consistency. | Simple convex hull constraint in composition space does not guarantee physical validity in property space. |
| **Stratified Permutation Test** | Required by SC-002 to validate significance while accounting for local density. | Simple shuffling ignores the smooth function of composition, leading to inflated false positives. |
| **Versioning Hook** | Required by Constitution Principle V. | Manual hash updates are error-prone and violate reproducibility. |

## Methodological Rigor & Risk Mitigation

### 1. Decoupling Analysis (FR-005)
- **Problem**: K-Means on composition is tautological.
- **Solution**: Use **Local Correlation Estimation (LCE)**. A sliding window (k-nearest neighbors in ilr-space) calculates local correlation.
- **Null Model**: To validate significance, we shuffle property values *within* local neighborhoods (preserving compositional density) 1000 times. A region is "decoupled" only if its local correlation is lower than the majority of the null distribution (p < 0.05).

### 2. Physical Bounds (FR-004)
- **Problem**: Convex hull in composition space does not guarantee physical bounds in property space.
- **Solution**: Implement a **Rule of Mixtures Validator**. For every synthetic point, calculate Voigt (upper) and Reuss (lower) bounds for Bulk and Shear moduli. Reject any prediction that exceeds these theoretical limits.

### 3. System Density (FR-003)
- **Problem**: Sparse systems skew LOSO-CV R².
- **Solution**: Weight systems by sample size in the final R² calculation. Systems with < 20 points are flagged and excluded from the primary "R² > 0.6" success metric if they dominate the variance.

### 4. Reliability Mask
- **Problem**: Optimizing over extrapolated regions.
- **Solution**: The Pareto optimizer uses a **Reliability Mask**. Points with `uncertainty_variance` (from `model_validation_report.json`) above the 90th percentile are penalized or excluded.

## Execution Order

1. **Ingestion**: Download `materials-project/oqmd`, filter for Bulk/Shear, verify >500 entries.
2. **Encoding**: Generate `encoded_alloys.csv` with ilr features.
3. **Training**: Run LOSO-CV, generate `model_validation_report.json` and `loso_test_points.csv`.
4. **Optimization**: Run NSGA-II with Convex Hull + Voigt/Reuss checks + Reliability Mask. Output `pareto_frontier.csv`.
5. **Analysis**: Run LCE + Stratified Permutation Test. Output `sensitivity_analysis.csv`.
6. **Versioning**: Run `versioning_hook` to update `state/` YAML.