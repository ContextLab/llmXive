# Implementation Plan: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

**Branch**: `001-predict-alloy-diffusion` | **Date**: 2023-10-27 | **Spec**: `specs/001-predict-alloy-diffusion/spec.md`
**Input**: Feature specification from `/specs/001-predict-alloy-diffusion/spec.md`

## Summary

This project implements a computational pipeline to predict how alloying elements affect the diffusion activation energy in Face-Centered Cubic (FCC) metals. The approach ingests experimental data, engineers atomic descriptors (specifically size mismatch), trains Random Forest and Gradient Boosting regressors for prediction, and employs Linear Regression for statistical inference of the size mismatch hypothesis. The pipeline includes rigorous validation, threshold sensitivity analysis, and strict adherence to resource constraints (CPU-first, GitHub Actions free tier).

**Critical Methodological Correction**: The analysis distinguishes between **self-diffusion** (solute = host, used for baseline $Q_{host}$) and **solute diffusion** (solute != host, used for training). The original spec's filter for "self" diffusion was corrected to "solute" diffusion for the training set to ensure non-zero variance in the `size_mismatch` predictor.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `matplotlib`, `seaborn`, `periodictable==0.20.1` (pinned for descriptor consistency), `joblib`, `pytest`  
**Storage**: Local CSV/JSON files (`data/`, `models/`, `validation/`)  
**Testing**: `pytest` with unit tests for feature engineering and integration tests for the full pipeline  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Data Science / Computational Materials Science  
**Performance Goals**: Complete full pipeline (ingestion -> training -> validation) in ≤6 hours; Peak RAM ≤7 GB.  
**Constraints**: No synthetic data generation for primary analysis; strict filtering for FCC solute diffusion for training; no CUDA usage.  
**Scale/Scope**: Dataset size ≤10 MB (compressed); Model training on ≤50-200 rows (typical for specific alloy subsets).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ PASS | Plan mandates pinned `requirements.txt`, fixed random seeds, and raw data checksumming. |
| **II. Verified Accuracy** | ✅ PASS | Plan mandates the **Reference-Validator Agent** to verify all citations against primary sources before publication. |
| **III. Data Hygiene** | ✅ PASS | Plan includes `data_provenance.json`, checksums, and immutable raw data handling. |
| **IV. Single Source of Truth** | ✅ PASS | `data/curated/filtered.csv` is the SSoT for `baseline_shift_eV`. All statistics trace to this file and `code/processing/baseline.py`. |
| **V. Versioning Discipline** | ✅ PASS | Artifacts will carry content hashes; `updated_at` timestamps managed by the agent. |
| **VI. Resource Compliance** | ✅ PASS | Models (RF, GB, Linear) are CPU-tractable. No GPU required. Dataset size constrained to <10MB. |
| **VII. Descriptor Consistency** | ✅ PASS | Plan mandates `periodictable==0.20.1` in `requirements.txt` to ensure fixed, versioned constants for atomic radii and electronegativity. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-alloy-diffusion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── model_output.schema.yaml
    ├── validation_report.schema.yaml
    ├── baseline.schema.yaml
    └── atomic_descriptor.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-415-predicting-the-impact-of-alloying-on-the/
├── data/
│   ├── raw/                # Downloaded raw files (immutable)
│   └── curated/            # Filtered/processed CSVs + provenance JSON
│       ├── filtered.csv    # Solute diffusion data (Training Set)
│       └── baselines.csv   # Self diffusion data (Baseline Set)
├── code/
│   ├── data/
│   │   └── streaming_loader.py  # Data Availability Check & Streaming
│   ├── ingestion/          # Data loading and filtering scripts
│   ├── processing/
│   │   ├── feature_engineering.py
│   │   └── baseline.py     # FR-008: Baseline calculation script
│   ├── models/
│   │   ├── train_rf.py
│   │   ├── train_gb.py
│   │   └── train_linear.py
│   └── validation/
│       ├── sensitivity_analysis.py
│       └── stability_index_report.py
├── models/                 # Saved .pkl artifacts
├── validation/             # JSON reports and plots
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt
```

**Structure Decision**: Single project structure with modular subdirectories for `ingestion`, `processing`, `models`, and `validation` to ensure separation of concerns and testability.

## Complexity Tracking

No violations detected. The complexity is managed by:
1. **CPU-First**: Using classical ML (RF, GB, Linear) avoids GPU overhead.
2. **Streaming**: `streaming_loader.py` processes data in chunks if needed.
3. **Strict Filtering**: Early elimination of non-FCC/non-solute data reduces downstream compute load.

## FR/SC Coverage Map

| FR/SC ID | Plan Element | Description |
| :--- | :--- | :--- |
| **FR-001** | `code/data/streaming_loader.py` | Data Availability Check halts pipeline if no verified real dataset found. |
| **FR-002** | `code/processing/feature_engineering.py` | Calculates `size_mismatch` using pinned `periodictable` library. |
| **FR-003** | `code/models/train_rf.py`, `train_gb.py` | Grid Search RF/GB with complexity tie-breaking. |
| **FR-004** | `code/models/train_*.py` | Nested CV or 80/20 Hold-out split logic. |
| **FR-005** | `code/validation/sensitivity_analysis.py` | Threshold sweep and Stability Index calculation. |
| **FR-006** | `code/processing/baseline.py` | Checks for pure host baseline; halts with specific error if missing. |
| **FR-007** | `code/ingestion/ingest.py` | Generates `data/curated/data_provenance.json` with required fields. |
| **FR-008** | `code/processing/baseline.py` | Calculates `baseline_shift` and outputs to `data/curated/filtered.csv`. |
| **FR-009** | `code/validation/sensitivity_analysis.py` | Generates `validation/stability_index_report.json`. |
| **SC-001** | `code/models/train_*.py` | R² > 0.0 check against mean-predictor. |
| **SC-002** | `code/models/train_linear.py` | P-value < 0.05 and 95% CI check. |
| **SC-003** | `code/validation/sensitivity_analysis.py` | Stability Index ≤ 0.05 check. |
| **SC-004** | CI Workflow | Runtime ≤ 6h, RAM ≤ 7GB check. |