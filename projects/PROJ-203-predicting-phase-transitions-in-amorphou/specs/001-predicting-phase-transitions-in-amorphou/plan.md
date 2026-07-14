# Implementation Plan: Predicting Phase Transitions in Amorphous Solids Using Machine Learning

**Branch**: `001-predicting-phase-transitions` | **Date**: 2026-07-15 | **Spec**: `specs/001-predicting-phase-transitions/spec.md`
**Input**: Feature specification from `/specs/001-predicting-phase-transitions/spec.md`

## Summary

This project implements a two-stage pipeline to predict glass-transition temperatures (Tg) and crystallization propensity in amorphous solids. 
1. **Phase 0 (Offline/HPC)**: Generates short-range structural descriptors (RDF, bond angles, coordination numbers) from Molecular Dynamics (MD) simulations for diverse compositions. This phase is computationally intensive and runs on external HPC resources or local workstations, *not* within the CI limits.
2. **Phase 1 (CI)**: Trains and evaluates Random Forest models on the pre-computed dataset. This phase adheres to strict compute constraints (limited CPU resources, 7GB RAM, 6h limit) and ensures simulation-to-experiment independence by using MD-derived predictors against experimentally derived labels (if available).

The system explicitly separates the heavy simulation workload from the CI pipeline to ensure feasibility.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `shap`, `mdtraj`, `openmm` (or `lammps` via `pylammps` if available in CPU wheel), `pyyaml`.  
**Storage**: Local file system (`data/` for raw/processed CSV/Parquet, `models/` for `.pkl` artifacts).  
**Testing**: `pytest` with `pytest-cov`.  
**Target Platform**: 
- **Phase 0**: External HPC/Workstation (CPU/GPU, >64GB RAM).
- **Phase 1**: GitHub Actions Free Tier (Linux, 2 CPU, ~7 GB RAM, ~14 GB disk, no GPU).  
**Project Type**: Computational Science / Data Pipeline / ML Research.  
**Performance Goals**: 
- **Phase 1 (CI)**: End-to-end ML pipeline (training + analysis) ≤ 6 hours on pre-computed data.
- **Target Metric**: Tg prediction RMSE ≤ 15 K (only applicable if real experimental data is available).  
**Constraints**: No GPU, no deep learning training, no 8-bit quantization. MD simulations capped at a fixed duration per composition (Phase 0); truncated if exceeded.  
**Scale/Scope**: A target of several hundred compositions across 3 chemical families (oxides, sulfides, organics).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`. External datasets fetched via `datasets` library or direct URL with checksum verification. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | **FAIL** (Pending Data) | Citations in `research.md` and `paper/` will be validated against the `# Verified datasets` block. **Current Status**: No verified URL for thermal property datasets provided in the prompt block. The CI pipeline will fail if real data is not provided. |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw/`. Derived data in `data/processed/`. Checksums recorded in state file. No in-place modification. |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to `data/processed/` rows. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | PASS | Artifacts hashed; state file updated on change. |
| **VI. Simulation-to-Experiment Independence** | PASS | Predictors (MD) strictly separated from labels (Experimental Tg/Tx). Labels sourced *only* from external databases (Glass Data/NIST) if available; otherwise, flagged as 'simulated' and excluded from hypothesis testing. |
| **VII. Computational Feasibility** | **PARTIAL** | MD generation (Phase 0) requires external HPC resources. Phase 1 (CI) fits within 6h on pre-computed data. The simulation workload is offloaded. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-phase-transitions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-203-predicting-phase-transitions-in-amorphou/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py
│   ├── data/
│   │   ├── download.py       # Fetches experimental data (if available)
│   │   ├── simulate.py       # MD simulation wrapper (LAMMPS/OpenMM) - Phase 0 only
│   │   └── extract.py        # Descriptor generation (RDF, angles) - Phase 0 only
│   ├── models/
│   │   ├── train.py          # RF Training & CV
│   │   └── evaluate.py       # Metrics & SHAP analysis
│   └── utils/
│       ├── validators.py     # Data integrity checks
│       └── plots.py          # Visualization helpers
├── data/
│   ├── raw/                  # Raw downloads (checksummed)
│   └── processed/            # Feature-engineered CSVs/Parquets (Input for CI)
├── models/                   # Trained .pkl artifacts
├── tests/
│   ├── unit/
│   └── integration/
└── docs/                     # Generated reports
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `models/`) is selected to minimize overhead and fit the 14GB disk limit. This aligns with the "Computational Science" project type, keeping data and code co-located for reproducibility on CI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **MD Simulation Step (Phase 0)** | Required to generate structural descriptors (RDF, angles) not present in static databases. | Using only compositional features (e.g., atomic radius) fails FR-001 and the core hypothesis that *local structure* drives Tg. |
| **Truncation Logic (Phase 0)** | Required to meet HPC time limits and ensure consistency. | Running full trajectories for all compositions would exceed resource quotas. |
| **SHAP Analysis (Phase 1)** | Required for FR-004 (Interpretability) and FR-005 (Family comparison). | Global feature importance (Gini) is insufficient for detecting family-specific non-linear interactions. |
| **Two-Stage Pipeline** | Required to separate extended simulation from 6h CI limit. | Attempting to run a large-scale number of simulations in CI is impossible on 2 CPU cores. |

## Phase Definitions

### Phase 0: Data Generation (Offline/HPC)
*Executed on external resources. Output: `data/processed/descriptors.parquet`.*
1. **Simulation**: Run MD for a representative set of compositions. Cap at a duration appropriate for each composition.
2. **Extraction**: Generate RDF, bond angles, coordination numbers.
3. **Labeling**: Fetch experimental Tg/Tx (if available) or flag as 'missing'.
4. **Validation**: Check for energy convergence. Exclude non-relaxed states.

### Phase 1: Model Training & Analysis (CI)
*Executed on GitHub Actions. Input: `data/processed/descriptors.parquet`.*
1. **Data Loading**: Load pre-computed dataset. Verify `data_quality_flag`.
2. **Preprocessing**: Handle missing labels (exclude if 'missing' or 'simulated' for hypothesis testing).
3. **Model Training**: Train Random Forest (Regressor/Classifier) with k-fold CV.
4. **Collinearity Diagnostics**: Calculate VIF for all predictors (FR-007).
5. **Sensitivity Analysis**: Vary crystallization threshold (low, medium, high) and report FPR/Class Balance (FR-006, SC-004).
6. **Interpretability**: Generate SHAP values and family-specific plots (FR-004, FR-005).
7. **Reporting**: Generate `docs/reports/metrics.json`, `docs/reports/sensitivity_analysis.csv`, `docs/reports/collinearity_report.json`.

## FR/SC Mapping

| Requirement | Phase/Step | Output Artifact |
| :--- | :--- | :--- |
| **FR-001** (Descriptors) | Phase 0, Step 2 | `data/processed/descriptors.parquet` |
| **FR-002** (Labeling) | Phase 0, Step 3 | `data/processed/labels.csv` |
| **FR-003** (Model Training) | Phase 1, Step 3 | `models/tg_regressor.pkl` |
| **FR-004** (SHAP) | Phase 1, Step 6 | `docs/reports/shap_plots/` |
| **FR-005** (Multiple Comparison) | Phase 1, Step 6 | `docs/reports/shap_plots/` (with Bonferroni correction) |
| **FR-006** (Sensitivity) | Phase 1, Step 5 | `docs/reports/sensitivity_analysis.csv` |
| **FR-007** (Collinearity) | Phase 1, Step 4 | `docs/reports/collinearity_report.json` |
| **FR-008** (Timescale) | Phase 0, Step 1 | `data/processed/descriptors.parquet` (with cooling rate metadata) |
| **SC-001** (RMSE) | Phase 1, Step 3 | `docs/reports/metrics.json` |
| **SC-002** (ROC-AUC) | Phase 1, Step 3 | `docs/reports/metrics.json` |
| **SC-003** (Stability) | Phase 1, Step 6 | `docs/reports/shap_plots/` |
| **SC-004** (Threshold Sensitivity) | Phase 1, Step 5 | `docs/reports/sensitivity_analysis.csv` |
| **SC-005** (Compute Feasibility) | Phase 1, Step 3 | `logs/ci_timing.log` |

## Risk Assessment

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Missing Experimental Data** | High | If no verified URL is provided, the CI run defaults to 'Pipeline Validation' mode. Hypothesis testing (RMSE target) is skipped. |
| **MD Simulation Timeout** | High | Strict timeout per comp; truncate to final 500 steps. Exclude non-relaxed states. |
| **Collinearity** | Medium | Calculate VIF; report collinearity diagnostics (FR-007). |
| **Overfitting** | Medium | Use k-fold cross-validation.; limit tree depth; report power limitations if RMSE > 15 K. |
| **Cooling Rate Mismatch** | High | Acknowledge physical impossibility. Rely on 'Cooling-Rate Invariance' assumption. Filter known sensitive compositions. |