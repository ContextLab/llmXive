# Implementation Plan: Predicting the Ductility of Additively Manufactured Nickel-Based Superalloys

**Branch**: `224-ductility-prediction` | **Date**: 2026-06-25 | **Spec**: `specs/224-ductility-prediction/spec.md`
**Input**: Feature specification from `/specs/224-ductility-prediction/spec.md`

## Summary

This feature implements a data-driven pipeline to quantify the influence of laser-based additive manufacturing (AM) process parameters (laser power, scan speed, hatch spacing, layer thickness, and derived energy density) on the ductility of nickel-based superalloys. The approach combines a rigorous **Literature Synthesis** (FR-001 to FR-004) to construct a unified dataset from verified sources, multicollinearity handling via Variance Inflation Factor (VIF) analysis (FR-005), interpretable Linear Mixed-Effects (LME) modeling (FR-006 to FR-009), and a predictive XGBoost regressor (FR-010 to FR-012). 

**Critical Note on Data**: Due to the absence of a single verified HuggingFace dataset for "additive-manufacturing-superalloys" in the provided input block, this plan relies on **manual curation of supplementary tables** from the four cited papers as the primary data source. The pipeline is designed to handle small sample sizes (N < 100) by using **Leave-One-Alloy-Family-Out (LOAFO)** cross-validation and framing statistical inference as **exploratory** rather than confirmatory.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `xgboost`, `pyyaml`, `requests`, `lxml` (for table parsing)  
**Storage**: Local CSV/Parquet files under `data/`, model artifacts under `artifacts/`  
**Testing**: `pytest` (unit tests for data cleaning, integration tests for model training)  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, ~7GB RAM)  
**Project Type**: Data Science / Computational Materials Science  
**Performance Goals**: Full pipeline execution ≤ 600 seconds; model inference ≤ 2 seconds.  
**Constraints**: No GPU/CUDA; memory footprint < 7GB; dataset size ≤ 250 records (estimated from literature); strict VIF ≤ 5 threshold.  
**Scale/Scope**: Single dataset merge (from multiple papers)

The specific value to remove/generalize: 'multiple'

Rewritten passage:, Linear Mixed-Effects (LME) model (with conditional feature set), XGBoost model, final report.

## Constitution Check

*GATE: Must pass before Phase 0 research. Note: Principles II and VII are currently marked WARN due to data source gaps.*

| Principle | Status | Verification Method |
|-----------|--------|---------------------|
| I. Reproducibility | **PASS** | Random seeds pinned in `code/`; external datasets fetched via script from canonical sources (Papers/HF). |
| II. Verified Accuracy | **WARN** | Primary HF dataset missing from verified block. Plan relies on paper tables. Citations verified against provided block (none match). |
| III. Data Hygiene | **PASS** | Data files checksummed; transformations produce new files; no in-place modification. |
| IV. Single Source of Truth | **PASS** | All statistics trace to `data/` rows and `code/` blocks; no hand-typed values in report. |
| V. Versioning Discipline | **PASS** | Artifacts hashed; `state` updated on change. |
| VI. Modeling Transparency | **PASS** | Model types, hyperparameters, seeds, and library versions documented in `research.md` and `contracts/`. |
| VII. External Data Provenance | **WARN** | No verified URL for "additive-manufacturing-superalloy" HF collection. Provenance tracked via paper DOIs. |

## Project Structure

### Documentation (this feature)

```text
specs/224-ductility-prediction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── build_record.schema.yaml
│   ├── mixed_effects_result.schema.yaml
│   └── report_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── acquisition.py          # Fetches from Papers (tables) and HF (if available)
│   ├── cleaning.py             # Unit conversion, missing value handling, Composition Mapping
│   └── preprocessing.py        # VIF calculation, feature engineering (conditional)
├── models/
│   ├── lme_model.py            # Linear Mixed-Effects fitting (statsmodels)
│   └── xgboost_model.py        # Gradient Boosting fitting (xgboost)
├── analysis/
│   ├── sensitivity.py          # Sensitivity analysis across alpha thresholds
│   └── reporting.py            # Generates final report (PDF/Markdown + PDPs)
├── tests/
│   ├── test_data_cleaning.py
│   └── test_models.py
├── requirements.txt
└── main.py                     # Orchestration script
```

**Structure Decision**: Single `code/` directory with modular sub-packages. This minimizes overhead for a data-science pipeline and aligns with the "Single Source of Truth" principle by keeping data processing and modeling logic co-located.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mixed-Effects Model | Required to account for alloy-family random effects (FR-006). | Simple linear regression would ignore hierarchical structure of data (multiple builds per alloy family), violating FR-006. |
| VIF Filtering | Required to handle collinearity between Energy Density and its components (FR-005). | Including all predictors would inflate variance and produce unstable coefficients, violating SC-004. |
| XGBoost + LME | Dual-model approach required to capture non-linearities (XGBoost) while maintaining interpretability (LME). | Using only XGBoost would violate the requirement for standardized coefficients and confidence intervals (FR-006). |
| LOAFO CV | Required for small N (<100) to avoid data starvation in test sets. | Standard Train/Val/Test split would leave too few samples for meaningful metrics. |

## Scientific Soundness & Limitations

- **Data Scarcity**: The dataset is expected to be small (N < 100). Statistical significance (p-values) will be treated as **exploratory**. The plan uses bootstrapping to estimate stability where possible.
- **Feature Collinearity**: Energy Density is a deterministic function of other parameters. The plan explicitly compares two model specifications: (1) Components-only, and (2) Energy Density-only (if VIF > 5). This avoids tautological validation.
- **External Validity**: Results are limited to the specific alloys and process ranges found in the four cited papers. No claim is made to generalize beyond this scope.
- **Physics Gap**: The data is empirical, not physics-simulated. The model learns correlations, not causal mechanisms.
