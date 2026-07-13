# Implementation Plan: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

**Branch**: `001-cold-work-recrystallization` | **Date**: 2026-07-14 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-cold-work-recrystallization/spec.md`

## Summary

This project implements a CPU-tractable machine learning pipeline to predict "time-to-peak softening" in aluminum alloys based on cold work percentage, annealing temperature, and alloy composition (Mg, Si, Cu, Mn). The approach utilizes a Random Forest Regressor from `scikit-learn`, strictly adhering to the 2-core/7GB RAM constraints of the GitHub Actions free tier.

**Critical Data Strategy**: Due to the absence of verified experimental datasets in the provided "Verified datasets" block, the pipeline utilizes a **Noisy Synthetic Baseline Generator**. This generator creates data based on established physical trends (Avrami kinetics) but injects significant heteroscedastic noise and unmodeled factors to simulate real-world experimental conditions. This ensures the model is tested on its ability to recover signals from noise, avoiding tautological validation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `pyyaml`, `requests`  
**Storage**: Local file system (`data/` for raw/processed CSVs, `artifacts/` for models/reports)  
**Testing**: `pytest` (unit tests for data validation, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions Free Runner)  
**Project Type**: Computational Science / Data Analysis Pipeline  
**Performance Goals**: Complete full pipeline (ingest → validate → train → evaluate) within 60 minutes on 2 vCPU.  
**Constraints**: CPU-only execution; dataset capped at a manageable scale for preliminary analysis; no GPU/CUDA; strict memory limits (<7GB RAM).  
**Scale/Scope**: <5,000 experimental records; A set of predictor features.; A single target variable.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/`. The **Synthetic Generator Script** (and its seed) is the canonical source. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | **Compliant** | The "Verified Source" for this iteration is the deterministic synthetic generator code. No external URLs are fabricated. If real data is added later, it must be checksummed and verified against primary sources. |
| **III. Data Hygiene** | **Compliant** | Raw data (generated or fetched) is checksummed. The generator script hash and seed are recorded. Transformations produce new files (e.g., `raw.csv` → `validated.csv`). No in-place edits. |
| **IV. Single Source of Truth** | **Compliant** | All figures and stats trace back to specific rows in `data/validated.csv` and code in `code/`. The synthetic generator is the SSoT for data content. |
| **V. Versioning Discipline** | **Compliant** | Content hashes of the generator script and the resulting CSV are recorded in `state/projects/...yaml`. |
| **VI. Computational Kinetic Stability** | **Compliant** | Pipeline enforces CPU-only Random Forest. Feature engineering is deterministic. Memory bounds enforced via dataset sampling. |
| **VII. Experimental Data Fidelity** | **Compliant** | Data directory segregates raw vs. derived. Test set is held out *before* feature selection. R² threshold is a **hard gate** for acceptance; failure halts the stage, it is not merely flagged. |

## Project Structure

### Documentation (this feature)

```text
specs/001-cold-work-recrystallization/
├── plan.md              # This file
├── research.md          # Phase 0 output (contains dataset strategy)
├── data-model.md        # Phase 1 output (defines entities)
├── quickstart.md        # Phase 1 output (execution guide)
├── contracts/           # Phase 1 output (derived from data-model.md)
│   ├── dataset.schema.yaml
│   └── model-output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/
├── data/
│   ├── raw/                 # Downloaded raw files OR generated synthetic files (checksummed)
│   ├── processed/           # Cleaned, validated, normalized CSVs
│   └── split/               # train.csv, test.csv
├── code/
│   ├── __init__.py
│   ├── ingest.py            # Data ingestion (Real fetch attempt -> Synthetic fallback) & validation
│   ├── train.py             # Model training and feature importance
│   ├── validate.py          # Sensitivity analysis (Input Perturbation) and metrics
│   ├── utils.py             # Constants, VIF calculation, unit normalization, noise generation
│   └── requirements.txt     # Pinned dependencies
├── artifacts/
│   ├── models/              # Saved .pkl models
│   ├── reports/             # JSON/CSV reports (VIF, sensitivity, metrics)
│   └── figures/             # Generated plots (if any)
├── tests/
│   ├── unit/                # Validation logic tests
│   └── integration/         # End-to-end pipeline tests
└── README.md
```

**Structure Decision**: Selected "Single project" structure. The separation of `data/raw` vs `data/processed` enforces Constitution Principle III. The `contracts/` schemas are derived directly from the entity definitions in `data-model.md`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The plan adheres strictly to the spec's requirement for a Random Forest Regressor on CPU. No deep learning or complex microservices are introduced. | N/A |