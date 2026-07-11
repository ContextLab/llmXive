# Implementation Plan: Predicting Yield Strength of BCC Alloys

**Branch**: `001-bcc-yield-strength` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-bcc-yield-strength/spec.md`

## Summary

This project implements a machine learning pipeline to predict the yield strength of Body-Centered Cubic (BCC) alloys using public data. The approach involves downloading the MPEA database (via manual ingestion due to lack of verified URL), filtering for BCC-phase alloys, engineering compositional descriptors (atomic radius mismatch, VEC, mixing entropy/enthalpy) and/or Isometric Log-Ratio (ILR) transformations, and training regression models (Random Forest, Gradient Boosting, Ridge) with rigorous Repeated Cross-Validation and statistical testing. The pipeline is constrained to run on CPU-only GitHub Actions free-tier runners.

**Critical Constraint**: Due to the lack of a verified programmatic URL for the MPEA dataset, the pipeline requires manual data ingestion. This is a known reproducibility compromise documented in the Constitution Check.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `periodictable`, `pyyaml`, `requests`, `joblib`, `scipy` (for statistical tests)  
**Storage**: Local CSV/Parquet files under `data/` (raw and processed)  
**Testing**: `pytest` (unit tests for feature engineering, integration tests for pipeline stages)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, No GPU)  
**Project Type**: Data Science / Machine Learning Pipeline  
**Performance Goals**: Full pipeline runtime ≤ 6 hours; Memory usage ≤ 7 GB; Dataset subset to fit RAM.  
**Constraints**: No GPU acceleration; No large-LLM inference; Data must be filtered for BCC phase only; Minimum sample size (N ≥ 80) required for training; Feature sets must be mutually exclusive (ILR OR scalar descriptors).  
**Scale/Scope**: Single dataset processing (MPEA); Model training on ≤ 500 rows (estimated after filtering); Feature engineering for a small set of elements.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy | Status |
|-----------|---------------------|--------|
| **I. Reproducibility** | All random seeds pinned in `code/`; dependencies pinned in `requirements.txt`; data fetched from canonical DOI (if available) or verified URL; checksums recorded. | **Pass** |
| **II. Verified Accuracy** | Citations in `research.md` restricted to verified URLs in the input block. **NOTE**: MPEA has NO verified URL. Manual ingestion is required. This is a **Partial Pass**; the pipeline cannot be fully automated without manual intervention. | **Partial Pass** |
| **III. Data Hygiene** | Raw data preserved in `data/raw/`; derived data in `data/processed/`; checksums calculated for all files; no in-place modifications. | **Pass** |
| **IV. Single Source of Truth** | All statistics in reports trace to specific `code/` scripts and `data/` files; no hand-typed numbers in `paper/`. | **Pass** |
| **V. Versioning Discipline** | Artifact hashes tracked in state file; `updated_at` timestamps managed by Advancement-Evaluator. | **Pass** |
| **VI. Compositional Feature Integrity** | Feature calculation formulas (δ, VEC, etc.) documented in `data-model.md`; periodic table reference pinned (e.g., `periodictable` lib); derivation notes in code. | **Pass** |
| **VII. Crystal-Structure Specificity** | Filtering logic explicitly checks `crystal_structure` == "BCC" (or equivalent) before any downstream processing; mixed-phase entries excluded. | **Pass** |

## Project Structure

### Documentation (this feature)

```text
specs/001-bcc-yield-strength/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Subsequent deliverable (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-525-predicting-the-yield-strength-of-bcc-all/
├── data/
│   ├── raw/                 # Downloaded raw files (e.g., MPEA)
│   └── processed/           # Filtered, normalized, engineered data
├── code/
│   ├── __init__.py
│   ├── 01_download.py       # Data ingestion and filtering (RAW ONLY)
│   ├── 02_engineer.py       # Feature engineering (descriptors & ILR)
│   ├── 03_train.py          # Model training and validation (CV only)
│   ├── 04_evaluate.py       # Permutation importance, CI, and stability analysis
│   ├── utils/
│   │   ├── periodic_table.py # Element property lookup
│   │   └── metrics.py        # Custom metrics and stats
│   └── main.py              # Pipeline orchestrator
├── tests/
│   ├── unit/
│   │   ├── test_engineering.py
│   │   └── test_filters.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to minimize overhead. Data flows linearly from `data/raw` to `data/processed` via scripts in `code/`. Tests are split by unit (logic) and integration (pipeline).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual Feature Sets (ILR vs Descriptors)** | Scientific hypothesis requires comparing traditional descriptors against compositional closure-robust ILR transforms. **Clarification**: This is a **Meta-Analysis of Two Separate Runs** (one run with descriptors, one with ILR), not simultaneous training, to respect FR-003.2 mutual exclusivity. | Using only one set would limit the scientific contribution and fail to address the "compositional closure" problem explicitly mentioned in the spec. |
| **Repeated 5-Fold CV + Bootstrapping** | Small dataset size (N ≥ 80) requires robust variance estimation to avoid overfitting and ensure statistical significance. **Clarification**: No 80/20 holdout for primary analysis to preserve power; split only used as diagnostic if N > 200. | Simple train/test split would yield high variance estimates and unreliable confidence intervals for R². |
| **Strict BCC Filtering** | Crystal structure is a fundamental physical property affecting yield strength; mixing phases introduces noise. | Including non-BCC phases would invalidate the specific research question and violate Principle VII. |
| **Circular Validation Check** | Prevents tautological learning if yield strength is derived from CALPHAD using the same parameters as predictors. | Ignoring this would result in a mathematically trivial model rather than a physical prediction. |

## Implementation Phases

### Phase 0: Data Ingestion & Filtering (FR-001, FR-002, US-1, US-4)
1. **Input**: `data/raw/mpea_raw.csv` (Manual download required).
2. **Logic**:
   - Verify file integrity (checksum if available).
   - Filter for `crystal_structure` containing "BCC" (case-insensitive).
   - Exclude entries with missing `yield_strength` or non-numeric values.
   - Normalize `elemental_composition` to sum to 1.0.
   - **Crucial**: Reject any pre-filtered files; only raw data is accepted.
3. **Output**: `data/processed/bcc_filtered.csv`.
4. **Check**: If N < 80, **HALT** with "Data Scarcity Warning".

### Phase 1: Feature Engineering (FR-003, FR-003.1, FR-003.2, US-2)
1. **Input**: `data/processed/bcc_filtered.csv`.
2. **Logic**:
   - Calculate scalar descriptors: δ, VEC, Mixing Entropy, Mixing Enthalpy.
   - **Circular Check**: Verify `yield_strength_source`. If CALPHAD-derived, flag or exclude.
   - Calculate ILR-transformed features (if selected).
   - **Exclusivity**: Run two separate pipelines: one with descriptors, one with ILR. Do not combine.
3. **Output**: `data/processed/features_descriptors.csv` and `data/processed/features_ilr.csv`.

### Phase 2: Model Training & Validation (FR-005, US-3)
1. **Input**: Feature CSVs.
2. **Logic**:
   - **Primary Validation**: Repeated k-Fold CV (10 repetitions) on the **entire** dataset.
   - **Bootstrapping**: Resample dataset (with replacement) multiple times.; run full CV on each resample; record mean CV score.
   - **Models**: Train RF, GB, Ridge for each feature set.
   - **Holdout**: Only if N > 200, perform 80/20 split as a diagnostic; otherwise, rely on CV.
3. **Output**: `data/processed/model_results.json` (with CV scores, CIs).

### Phase 3: Evaluation & Reporting (FR-006, SC-001, SC-002, SC-003, US-3)
1. **Input**: Model results.
2. **Logic**:
   - **Model Comparison**: Friedman test + Nemenyi post-hoc (Bonferroni corrected) on CV scores.
   - **Feature Stability**: Calculate Spearman rank correlation of importance across CV repetitions. Flag if < 0.8.
   - **Uncertainty Check**: Compare MAE against MPEA metadata uncertainty (default threshold).
   - **Power Disclaimer**: Report results as "Estimation of Bounds" with caution on Type II error.
3. **Output**: `data/processed/performance_report.csv`, `data/processed/feature_importance.png`.

## Risk Management

| Risk | Mitigation |
|------|------------|
| **No Verified URL** | Manual ingestion with checksum verification; documented as reproducibility compromise. |
| **Small N (<80)** | Pipeline halts with warning; no training attempted. |
| **Circular Validation** | Explicit check for CALPHAD-derived yield strengths; exclusion or flagging. |
| **Overfitting** | Repeated CV + Bootstrapping; no holdout for small N to preserve power. |
| **Feature Collinearity** | Mutual exclusivity of ILR and Descriptors; ILR used to address closure. |

## Compute Feasibility

- **CPU Only**: `scikit-learn` models (RF, GB, Ridge) are CPU-tractable.
- **Memory**: Dataset subset to ~7 GB RAM; processing of <500 rows is trivial.
- **Runtime**: Repeated CV (10 reps) + 1000 Bootstrap resamples on <500 rows is estimated < 2 hours on 2-core CPU.
- **No GPU**: No CUDA dependencies; standard `torch` (CPU) or pure `numpy`/`sklearn`.

## Success Criteria Mapping

- **SC-001**: Measured via CV R² distribution against null baseline (mean prediction).
- **SC-002**: MAE compared against a pressure threshold in report.
- **SC-003**: Spearman correlation of feature importance calculated and reported.
- **SC-004**: Runtime tracked and logged; must be < 6 hours.