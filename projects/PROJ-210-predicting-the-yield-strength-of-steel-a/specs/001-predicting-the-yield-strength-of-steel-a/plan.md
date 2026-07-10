# Implementation Plan: Predicting the Yield Strength of Steel Alloys from Composition and Heat Treatment Parameters

**Branch**: `001-gene-regulation` | **Date**: 2026-06-28 | **Spec**: `specs/001-predicting-the-yield-strength-of-steel-a/spec.md`
**Input**: Feature specification from `/specs/001-predicting-the-yield-strength-of-steel-a/spec.md`

## Summary

This project implements a computational pipeline to predict the yield strength of steel alloys (in MPa) using elemental composition and heat treatment parameters. The core technical approach involves ingesting raw tabular data, engineering specific interaction features (e.g., C/Mn ratios, C × Cooling Rate) with non-linear orthogonalization to mitigate collinearity, and training a suite of models (GAM with splines, Regularized Linear Regression, Random Forest, XGBoost) in CPU-only mode. The plan prioritizes rigorous statistical validation via nested permutation tests (with constant spline complexity) and sensitivity analysis (using Kuncheva index) to distinguish genuine synergistic effects from model artifacts, strictly adhering to free-tier CI resource constraints (≤6 GB RAM, 2 CPU cores, **≤4 hours runtime**).

> **Note on Resource Constraints**: The Constitution Principle VI mandates ≤4 hours runtime and ≤6 GB RAM. The project plan strictly adheres to these limits. The Spec.md Assumptions block (stating ≤6 hours and ≤7 GB RAM) contradicts the Constitution; this plan follows the Constitution, and the Spec contradiction is flagged for kickback.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `xgboost`, `shap`, `matplotlib`, `pandas`, `numpy`, `pyyaml`, `requests`, `pygam`  
**Storage**: Local CSV/Parquet files under `data/` (raw, processed, and derived); no external database.  
**Testing**: `pytest` (unit tests for data pipelines, contract tests for schema validation).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational research pipeline / CLI tool.  
**Performance Goals**: Complete full pipeline (ingest → model → eval) within **≤4 hours**; RAM usage **≤6 GB** during peak training.  
**Constraints**: No GPU/CUDA; no large-LLM inference; all models must run on CPU; data subset to ≤10,000 rows if necessary to fit memory.  
**Scale/Scope**: Single dataset ingestion, model types, primary target variable (Yield Strength), sensitivity sweep over multiple p-value thresholds.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`; data fetched from canonical HuggingFace sources (if available) or fails hard; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` restricted to the "# Verified datasets" block; no invented URLs. |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw/`; checksums recorded in `state/`; transformations write new files. |
| **IV. Single Source of Truth** | PASS | All figures/stats in `paper/` trace to `code/` outputs and `data/` rows; no hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Content hashes used for artifacts; `updated_at` timestamp updated on artifact changes. |
| **VI. Numerical Stability & Resource Bounding** | PASS | Models limited to CPU; grid search capped at a finite number of points; data subset to ≤10k rows; RAM monitored (≤6 GB); runtime capped at **4h** (per Constitution). |
| **VII. Interaction Effect Validation** | PASS | Validation relies on SHAP interaction values and PDPs, not just feature importance; **nested permutation tests (with constant spline complexity)** used for significance. Explicitly mapped in `src/models/evaluate.py` (Step 4). |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-the-yield-strength-of-steel-a/
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
│   ├── ingest.py          # FR-001, FR-002: Fetch, clean, normalize
│   ├── features.py        # FR-003, FR-010: Ratios, interactions, non-linear orthogonalization
│   └── loader.py          # Data loading utilities
├── models/
│   ├── train.py           # FR-004: Train GAM, Linear, RF, XGBoost
│   ├── evaluate.py        # FR-005, FR-007, FR-008, FR-009, FR-011: SHAP, PDP, Nested Permutation (Principle VII)
│   └── sensitivity.py     # FR-006: Threshold sweep (p-value), Kuncheva index
├── utils/
│   ├── config.py          # Paths, seeds, thresholds
│   └── validators.py      # Schema validation
├── main.py                # Orchestration script
└── requirements.txt       # Pinned dependencies

data/
├── raw/                   # Downloaded datasets (checksummed)
├── processed/             # Cleaned, engineered datasets
└── results/               # Model artifacts, plots, stats

tests/
├── unit/                  # Logic tests
├── contract/              # Schema validation tests
└── integration/           # End-to-end pipeline tests
```

**Structure Decision**: Single project structure selected. The workflow is linear (Ingest → Feature Eng → Train → Eval), making a monolithic `src/` layout with modular sub-packages (`data`, `models`, `utils`) optimal for maintainability and reproducibility on CI.

**Requirements Mapping**: The Functional Requirements (FR-001 through FR-012) referenced in this structure are **inherited from `spec.md`**. This plan implements them as specified.

**Principle VII Mapping**: The validation of Principle VII (Interaction Effect Validation) is explicitly implemented in `src/models/evaluate.py` via the nested permutation test and PDP generation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Non-Linear Orthogonalization** | Required by FR-010 and Principle VII to prevent collinearity while preserving non-linear main effect structure. | Simple linear orthogonalization would fail to remove non-linear main effect variance, confounding interaction SHAP values. |
| **Nested Permutation Tests (Constant Spline)** | Required by FR-009 and Principle VII to prevent selection bias and model misspecification errors. | Standard permutation tests would leak information or use misspecified baselines, inflating Type I errors. |
| **Sensitivity Sweep (Kuncheva Index)** | Required by FR-006 to validate robustness of findings against arbitrary cutoffs using a metric robust to feature count. | Jaccard index is unstable for small feature sets; Kuncheva index provides a robust stability measure. |
| **-Fold Repeated CV** | Required for small datasets (N < 500) to reduce variance in performance estimates. | 3-fold CV is too unstable for small N, leading to unreliable feature selection. |