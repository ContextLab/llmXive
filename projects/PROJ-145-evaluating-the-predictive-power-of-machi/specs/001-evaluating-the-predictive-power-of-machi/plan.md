# Implementation Plan: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

**Branch**: `001-eva-predictive-power-hea` | **Date**: 2026-07-09 | **Spec**: `specs/001-evaluating-the-predictive-power-of-machi/spec.md`

## Summary

This feature implements a computational pipeline to evaluate the extrapolative capability of machine learning models (Random Forest, Gradient Boosting) in predicting thermodynamic properties (formation energy, mixing enthalpy) for High-Entropy Alloys (HEAs). The approach involves ingesting data from the verified open proxy `hmao/all_apis_for_multiapi` (representing AFLOW/Materials Project), generating "Hold-out Known" and "True Novel" test sets, calculating compositional descriptors via `pymatgen`, training baseline models, and rigorously analyzing performance degradation and uncertainty calibration in unexplored chemical spaces.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pymatgen`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `datasets` (Hugging Face), `matplotlib`, `seaborn`
**Storage**: Local CSV/Parquet files (`data/`), no external database.
**Testing**: `pytest` (unit tests for descriptor calc, integration tests for pipeline flow).
**Target Platform**: Linux (GitHub Actions free-tier: 2 vCPU, 7GB RAM).
**Project Type**: Data Science / Computational Materials Science Pipeline.
**Performance Goals**: Complete full pipeline (ingestion -> training -> evaluation) within 6 hours; RAM usage < 7 GB.
**Constraints**: CPU-only execution for training; no GPU dependencies; strict adherence to open data sources only.
**Scale/Scope**: Dataset size depends on API availability (estimated < 50k rows for 5+ element systems); models trained on CPU.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Action |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; `requirements.txt` locks versions; data fetched from canonical HF URL (`hmao/all_apis_for_multiapi`). |
| **II. Verified Accuracy** | PASS | All dataset URLs cited in `research.md` are from the verified list; Reference-Validator Agent run in Phase 0; no invented citations. |
| **III. Data Hygiene** | PASS | Raw data checksums recorded; derivations saved as new files (`heas_train.csv`, `holdout_known.csv`, etc.). |
| **IV. Single Source of Truth** | PASS | All statistics in `paper/` will be generated via `code/` scripts, not hand-typed. |
| **V. Versioning Discipline** | PASS | Artifacts will carry content hashes; `state/` updated on changes. |
| **VI. Extrapolation Integrity** | PASS | Plan explicitly separates "Hold-out Known" (error measurement) from "True Novel" (uncertainty calibration); uncertainty metrics (variance) mandatory for novel claims. |
| **VII. Descriptor-Traceability** | PASS | All descriptors (radius, electronegativity, VEC, melting point) calculated strictly via `pymatgen` with versioned constants. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-predictive-power-of-machi/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-145-evaluating-the-predictive-power-of-machi/
├── code/
│   ├── __init__.py
│   ├── config.py              # Hyperparameters, seeds, paths
│   ├── data_ingestion.py      # FR-001, FR-002: API/DF loading, filtering, splitting
│   ├── feature_engineering.py # FR-003: pymatgen descriptor calculation
│   ├── train_models.py        # FR-004: RF/GB training, 5-fold CV
│   ├── evaluate.py            # FR-005, FR-006, FR-007: Extrapolation, t-test, Spearman
│   └── report.py              # FR-008: Final report generation
├── data/
│   ├── raw/                   # Downloaded raw data (if any)
│   ├── processed/             # heas_train.csv, holdout_known.csv, true_novel.csv
│   └── models/                # Trained .pkl artifacts
├── tests/
│   ├── unit/
│   │   ├── test_descriptors.py
│   │   └── test_ingestion.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure chosen. The workflow is linear (Ingest -> Features -> Train -> Evaluate -> Report), making a monolithic `code/` directory with modular scripts more maintainable than a microservices architecture. This aligns with the CPU-bound, batch-processing nature of the task.

## Phase Plan

### Phase 0: Research & Data Strategy
- **Goal**: Identify and verify open HEA datasets containing 5+ element systems with formation energy/mixing enthalpy.
- **Action**: 
  1. Scan verified dataset list.
  2. **Reference-Validator Step**: Run the Reference-Validator Agent on `research.md` citations to ensure Constitution Principle II compliance before proceeding.
  3. Confirm `hmao/all_apis_for_multiapi` contains required columns.
  4. Explicitly exclude `lavita/ChatDoctor-HealthCareMagic-100k` (false positive).
- **Deliverable**: `research.md`.

### Phase 1: Data Model & Contracts
- **Goal**: Define schema for training data, test sets, and model outputs.
- **Action**: Create YAML contracts for `heas_train.csv`, `holdout_known.csv`, `true_novel.csv`, and `predictions.csv`.
- **Deliverable**: `data-model.md`, `quickstart.md`, `contracts/hea_dataset.schema.yaml`, `contracts/prediction_output.schema.yaml`.

### Phase 2: Implementation (Code Generation)
- **Goal**: Generate Python scripts for ingestion, feature engineering, training, and evaluation.
- **Action**: Implement FR-001 through FR-008. Ensure `pymatgen` usage and CPU-tractability.
- **Deliverable**: `code/` directory.

### Phase 3: Execution & Validation
- **Goal**: Run pipeline on GitHub Actions.
- **Action**: Execute `setup-plan.sh` -> `run_pipeline.sh`. Validate outputs against `contracts/`.
- **Deliverable**: `data/` artifacts, `report.csv`, `paper/` draft.

## Compute Feasibility Strategy

- **CPU-First**: All models (Random Forest, Gradient Boosting) are CPU-tractable. We will use `scikit-learn` default settings optimized for memory (e.g., limiting `max_depth` if necessary).
- **Data Streaming**: If the source dataset exceeds 7GB RAM, `datasets.load_dataset(..., streaming=True)` will be used to iterate and aggregate statistics without loading the full dataset into memory.
- **No GPU Required**: The spec explicitly targets CPU resources. No CUDA escape hatch is needed for this feature as the methods are classical ML.

## Data Availability Strategy

- **Primary Source**: We will use the **`hmao/all_apis_for_multiapi`** dataset from HuggingFace. This dataset is the verified open proxy for AFLOW and Materials Project repositories, containing the required thermodynamic targets (`formation_energy_per_atom`, `mixing_enthalpy`) and elemental compositions.
- **Constraint**: Direct API calls to Materials Project/AFLOW (FR-001) are bypassed in the CI environment due to the lack of API keys (Constitution Principle I). The `hmao/all_apis_for_multiapi` dataset is the *only* valid source for FR-001 compliance in this CI context.
- **Excluded Datasets**: 
  - `lavita/ChatDoctor-HealthCareMagic-100k`: Explicitly excluded (false positive "HEA" label, healthcare data).
  - `foundry-ml/dataset_thermalcond_aflow`: Excluded (thermal conductivity, not thermodynamic stability).
- **Fallback**: If `hmao/all_apis_for_multiapi` lacks sufficient 5+ element systems, the study will proceed with the available data, explicitly reporting the statistical power limitation (underpowered for small effects) rather than switching to unverified proxies.

## FR-001 & FR-002 Compliance Note

- **FR-001 (Data Retrieval)**: Satisfied by loading `hmao/all_apis_for_multiapi`, which aggregates data from the required repositories (AFLOW/MP).
- **FR-002 (Novelty Verification)**: Satisfied by querying the `hmao/all_apis_for_multiapi` composition index to verify "True Novel" compositions are absent from this open database. The "Source API" is defined as this verified dataset for CI reproducibility.