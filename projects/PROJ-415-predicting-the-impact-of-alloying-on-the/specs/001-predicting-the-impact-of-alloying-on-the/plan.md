# Implementation Plan: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

**Branch**: `001-predict-alloy-diffusion` | **Date**: 2023-10-27 | **Spec**: `specs/001-predict-alloy-diffusion/spec.md`
**Input**: Feature specification from `/specs/001-predict-alloy-diffusion/spec.md`

## Summary

This project implements a computational pipeline to predict how alloying affects diffusion activation energy in Face-Centered Cubic (FCC) metals. The approach ingests **verified real-world** diffusion data (NIST/Materials Project/Literature), filters for FCC self-diffusion events, engineers atomic descriptors (specifically size mismatch using Metallic Radii), and trains Random Forest, Gradient Boosting, and Linear Regression models. The plan prioritizes statistical rigor (p-values, bootstrap CIs, power analysis) and robustness (threshold sensitivity analysis) while strictly adhering to CPU-only constraints for GitHub Actions execution.

**Critical Constraint**: This pipeline **MUST NOT** proceed with synthetic or mock data for hypothesis validation. If verified real-world data is not retrieved or is insufficient (N < 50), the pipeline halts with a "Data Insufficiency" error.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `pyyaml`, `requests`, `pymatgen`  
**Storage**: Local CSV/JSON artifacts (no external database); data cached in `data/`  
**Testing**: `pytest` with `pytest-cov`  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7 GB RAM, No GPU)  
**Project Type**: Data Science / Computational Materials Science  
**Performance Goals**: Complete training and validation within 6 hours; memory usage < 6 GB; dataset size < 10 MB.  
**Constraints**: No CUDA/GPU; no deep learning training from scratch; strict reproducibility (pinned seeds).  
**Scale/Scope**: ~-200 data points (observational); model types; A set of threshold sensitivity points will be evaluated to determine the optimal configuration..

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`; `requirements.txt` pins all deps; data fetched from canonical sources (NIST/Materials Project). |
| **II. Verified Accuracy** | **PASS (Conditional)** | Citations in `research.md` and `paper/` will be validated against primary sources (NIST/Materials Project). **If verified source is unreachable or data is insufficient, the pipeline halts** rather than using synthetic data. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed in `state/`; transformations produce new files (e.g., `curated.csv`); no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in paper trace to `data/` rows and `code/` blocks; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes; `updated_at` timestamps updated on state change. |
| **VI. Computational Resource Compliance** | **PASS** | Models (RF/GB/Linear) are CPU-tractable; dataset size constrained < 10 MB; runtime < 6h. |
| **VII. Descriptor Consistency** | **PASS** | Atomic descriptors use fixed, versioned periodic table constants (Metallic Radii for FCC). Sensitivity check for descriptor choice included. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-alloy-diffusion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Global constants, seeds, paths
├── data/
│   ├── ingestion.py     # FR-001: Load, filter, standardize
│   ├── curation.py      # FR-001: Handle missing values, logs
│   ├── descriptors.py   # FR-002: Compute size_mismatch, etc.
│   └── acquisition.py   # NEW: Fetch from NIST/Materials Project
├── models/
│   ├── training.py      # FR-003, FR-004: RF, GB, Linear, GridSearch
│   └── inference.py     # FR-005: Prediction & coefficient extraction
├── validation/
│   ├── stats.py         # FR-005: Bootstrap CI, p-values, Power Analysis
│   └── sensitivity.py   # FR-005, SC-003: Threshold sweep
├── utils/
│   ├── logging.py       # Standardized logging
│   └── constants.py     # Periodic table data (versioned)
└── main.py              # Orchestration entry point

tests/
├── contract/
│   ├── test_schema.py   # Validate against contracts/*.schema.yaml
│   └── test_data.py     # Validate data types/ranges
├── integration/
│   └── test_pipeline.py # End-to-end flow
└── unit/
    ├── test_descriptors.py
    ├── test_models.py
    └── test_sensitivity.py

data/
├── raw/                 # Downloaded raw files (checksummed)
├── curated/             # Filtered/processed CSVs
└── artifacts/           # Model pickles, JSON reports

models/
├── final_rf.pkl
├── final_gb.pkl
└── linear_coef.json

reports/
└── validation_report.json
```

**Structure Decision**: Single project structure (`code/`, `tests/`, `data/`) selected for simplicity and direct alignment with the computational pipeline nature of the spec. No frontend/backend split required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The project scope (3 models, 1 feature, sensitivity analysis) fits within a single modular Python package. | N/A |

## FR/SC Mapping

| Spec ID | Plan Phase/Step | Description |
| :--- | :--- | :--- |
| **Phase 0: Data Availability Check** | `data/acquisition.py` | Fetch data from NIST/Materials Project. **Halt if source unreachable or N < 50**. |
| **FR-001** | `data/ingestion.py`, `data/curation.py` | Load CSV, filter `crystal_structure == "FCC"` & `diffusion_mode == "self"`, standardize units, log exclusions. |
| **FR-002** | `data/descriptors.py` | Compute `size_mismatch` = `(solute_r - host_r) / host_r` using **Metallic Radii**. |
| **FR-003** | `models/training.py` | Train RF & GB with `GridSearchCV` (5-fold, max_depth 3-10, n_est 50-200) maximizing R². |
| **FR-004** | `models/training.py` | 5-fold CV for tuning; separate R², RMSE, MAE on held-out test set. |
| **FR-005** | `models/inference.py`, `validation/stats.py`, `validation/sensitivity.py` | Linear Reg with **Host Metal fixed effects** for coef/p-value; Bootstrap 95% CI; Power Analysis; Threshold sweep a low-energy range (Stability = SD of classification rate). |
| **FR-006** | `validation/sensitivity.py` | Define baseline shift as `E_solute_measured - E_pure_host_measured` (Experimental Ground Truth). |
| **SC-001** | `validation/stats.py` | Compare RF/GB R² against mean-predictor baseline. |
| **SC-002** | `validation/stats.py` | Verify `size_mismatch` p-value < 0.05 and 95% CI. |
| **SC-003** | `validation/sensitivity.py` | Report classification rate stability (SD across sweep). |
| **SC-004** | `config.py`, CI Config | Ensure runtime < 6h, RAM < 7GB on GitHub Actions free tier. |