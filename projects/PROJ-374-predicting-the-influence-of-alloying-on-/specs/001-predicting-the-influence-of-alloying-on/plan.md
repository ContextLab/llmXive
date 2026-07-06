# Implementation Plan: Predicting the Influence of Alloying on the Seebeck Coefficient Using Public Data

**Branch**: `001-predicting-seebeck-alloying` | **Date**: 2026-06-27 | **Spec**: `specs/001-predicting-seebeck-alloying/spec.md`
**Input**: Feature specification from `specs/001-predicting-seebeck-alloying/spec.md`

## Summary

This project implements a CPU-tractable machine learning pipeline to predict the Seebeck coefficient of thermoelectric alloys based on compositional descriptors. The system ingests the electronic transport database (DOI: 10.1038/sdata.2017.85), filters for specific material families (Bismuth Telluride, Lead Telluride, Skutterudites) using a formula-to-family mapping, and engineers physicochemical features (mean atomic radius, electronegativity variance, VEC, atomic number variance) as mandated by FR-003. 

The analysis explicitly addresses statistical rigor by:
1.  Controlling for temperature (a known confounder) as a covariate.
2.  Using a Permutation Test (1,000 iterations) to validate that R² > 0.2 is statistically significant (p < 0.05) before classifying as "Success".
3.  Employing Repeated Cross-Validation for small datasets (N < 100) to ensure stable estimates.
4.  Enforcing a strict 95% retention threshold for filtered records (SC-005), halting the pipeline if not met.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn` (CPU-only), `mendeleev` (periodic table data), `matplotlib`, `requests`, `pyyaml`, `numpy`  
**Storage**: Local CSV/JSON files in `data/` (raw and processed); No external database.  
**Testing**: `pytest` for unit tests on feature engineering, stoichiometry parsing, and model evaluation logic.  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, 7 GB RAM, No GPU).  
**Project Type**: Data Science / Computational Materials Science  
**Performance Goals**: Complete full pipeline (ingestion to reporting) within 6 hours; Memory usage < 6 GB.  
**Constraints**: No GPU/CUDA; No large language model inference; Deterministic random seeds; Strict adherence to `spec.md` acceptance criteria.  
**Scale/Scope**: Single dataset (electronic transport DB); < 10k records expected; A set of engineered features, one categorical feature, and temperature will be used..

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `random_state` pinned in all sklearn calls. `requirements.txt` pins exact versions. Data checksums recorded in `state/`. |
| **II. Verified Accuracy** | **PASS** | Dataset DOI cited as `10.1038/sdata.2017.85`. No fabricated URLs. Citation validation logic included in `code/`. |
| **III. Data Hygiene** | **PASS** | Raw data downloaded to `data/raw/` with checksum. Processed data written to `data/processed/` as new files. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All R² values, p-values, and feature importances in the report are generated directly from `code/` outputs. No hand-typed values. |
| **V. Versioning Discipline** | **PASS** | Artifacts tracked via content hash in `state/projects/...yaml`. |
| **VI. Compositional Feature Integrity** | **PASS** | Feature formulas (mean radius, VEC, atomic number variance) are deterministic functions in `code/`. No stochastic generation. |
| **VII. Predictive Threshold Adherence** | **PASS** | Report logic explicitly classifies results as Success (>0.2 AND p<0.05), Inconclusive, or Failure. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-seebeck-alloying/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-374-predicting-the-influence-of-alloying-on-/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_ingest_and_clean.py       # FR-001, FR-002 (Stoichiometry), FR-003
│   ├── 02_engineer_features.py      # FR-003 (All 4 descriptors + Temp)
│   ├── 03_train_and_evaluate.py     # FR-004, FR-005, FR-008, SC-002 (Permutation)
│   ├── 04_visualize_and_report.py   # FR-006, FR-007, SC-005 (Retention Check)
│   ├── utils/
│   │   ├── periodic_data.py         # Mendeleev wrapper
│   │   ├── stoichiometry_parser.py  # Formula parsing logic
│   │   └── checksums.py             # Data hygiene utilities
│   └── tests/
│       ├── test_feature_engineering.py
│       ├── test_stoichiometry.py
│       └── test_model_metrics.py
├── data/
│   ├── raw/
│   │   └── electronic_transport_db.json  # Downloaded, checksummed
│   └── processed/
│       ├── cleaned_compositions.csv
│       └── final_features.csv
├── docs/
│   └── figures/
│       └── [generated_plots]/
└── state/
    └── projects/PROJ-374-predicting-the-influence-of-alloying-on-.yaml
```

**Structure Decision**: Single project structure chosen. The workflow is linear (Ingest -> Engineer -> Train -> Report). A single `code/` directory with distinct scripts for each phase ensures modularity while maintaining simplicity for the CI runner. `utils/` isolates domain-specific logic (periodic table lookups, stoichiometry parsing).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **N/A** | No complexity violations detected. The scope is contained within CPU limits and standard libraries. | N/A |

## Methodology Overview

### Phase 1: Data Ingestion, Stoichiometry Filtering, and Retention Check (FR-001, FR-002, SC-005)
1.  **Download**: Fetch data from DOI 10.1038/sdata.2017.85.
2.  **Parse & Map**: Use `stoichiometry_parser.py` to normalize formulas and `utils/mapping.json` to map formulas to families (Bi-Te, Pb-Te, Skutterudites).
3.  **Filter**: Retain only records matching target families AND specific stoichiometry ranges (e.g., Bi2Te3).
4.  **Retention Check**: Calculate retention rate. **If < 95%, halt pipeline with CRITICAL ERROR.**
5.  **Sanity Check**: Remove records with missing Seebeck or Temperature values.
6.  **Output**: `data/processed/cleaned_compositions.csv`.

### Phase 2: Feature Engineering (FR-003, VI)
For each valid record, calculate the following descriptors using `mendeleev`:
1.  **Mean Atomic Radius**: Weighted average.
2.  **Electronegativity Variance**: Variance.
3.  **Valence Electron Concentration (VEC)**: Weighted average.
4.  **Atomic Number Variance**: Variance (Retained per FR-003; collinearity noted).
5.  **Temperature**: Included as a covariate to control for confounding.
6.  **Material Family**: One-hot encoded.

### Phase 3: Modeling and Evaluation (FR-004, FR-005, FR-008, SC-002)
1.  **Split Strategy**:
    -   If N >= 100: 80/20 Stratified Split + 5-Fold CV on Train.
    -   If N < 100: Repeated 5-Fold CV (10 repeats) on full set (No hold-out).
2.  **Baseline**: Linear Regression.
3.  **Model**: `GradientBoostingRegressor` (n_estimators=100, random_state=42).
4.  **Significance Testing**:
    -   **Null Model**: Permutation test (iterations) on the target variable.
    -   **p-value**: Proportion of permuted R² >= Observed R².
    -   **Baseline Comparison**: F-test for improvement over Linear Regression.
5.  **Metrics**: R² (Mean), 95% CI, MAE, Permutation p-value, Baseline p-value.

### Phase 4: Visualization and Reporting (FR-006, FR-007)
1.  **Collinearity Check**: Calculate Variance Inflation Factor (VIF) and Pearson correlation matrix. Report VIF > 5.
2.  **Plots**: Scatter plots of Top 3 descriptors vs. Seebeck (with Temperature controlled).
3.  **Classification**:
    -   **Success**: R² > 0.2 AND p-value < 0.05.
    -   **Inconclusive**: 0.2 ≤ R² < 0.4 OR (R² > 0.2 but p >= 0.05).
    -   **Failure**: R² < 0.2 OR p >= 0.05.
4.  **Output**: `docs/figures/` and `docs/report.md`.