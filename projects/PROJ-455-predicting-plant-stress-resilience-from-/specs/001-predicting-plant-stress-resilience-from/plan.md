# Implementation Plan: Predicting Plant Stress Resilience from Publicly Available Metabolomic Data

**Branch**: `001-predict-plant-stress-resilience` | **Date**: 2026-06-25 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-predicting-plant-stress-resilience/spec.md`

## Summary
This project implements a predictive pipeline to forecast plant stress resilience using publicly available metabolomic data. Due to the current absence of verified real-world plant metabolomic datasets with paired pre-stress/post-stress metrics, the project proceeds with a **Mechanism-Guided Synthetic Generator**. This generator simulates metabolomic profiles and recovery metrics based on known biological pathways (e.g., proline, ABA) to serve as a controlled testbed for validating the pipeline logic (FR-001 to FR-012). The approach involves ingesting data (via a Mock Adapter for synthetic data, with a Real Adapter stub for future GEO/Zenodo use), filtering, normalizing heterogeneous recovery measures to a unified index, and training Random Forest and SVM models. The pipeline emphasizes cross-stress generalizability (simulated via distinct stress vectors), statistical validation via permutation testing, and biological plausibility checks against known stress-response pathways (KEGG). All operations are constrained to run on CPU-only CI (2 cores, 7GB RAM) within 6 hours.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `requests`, `biopython` (for KEGG mapping), `pyyaml`, `pytest`  
**Storage**: Local file system (`data/`, `code/`); CSV/Parquet intermediate files.  
**Testing**: `pytest` (contract tests, unit tests for preprocessing logic, benchmarking).  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM).  
**Project Type**: Data Science Pipeline / CLI  
**Performance Goals**: Full pipeline (ingest → train → validate) ≤ 6 hours on CPU.  
**Constraints**: No GPU; no deep learning; **Datasets with >10% missing values are REJECTED** (FR-003); strict memory management (streaming/chunking if needed).  
**Scale/Scope**: Limited to available public datasets; currently uses Mechanism-Guided Synthetic Data. If real data is added later, the pipeline will switch to the Real Adapter.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Action |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | **PASS** | All random seeds (numpy, sklearn) will be pinned in `code/`. Synthetic data generation parameters will be fixed. |
| **II. Verified Accuracy** | **CONDITIONAL PASS** | No real plant metabolomic datasets are currently verified. The project proceeds with a **Mechanism-Guided Synthetic Generator** whose ground truth (predictive metabolites) is explicitly defined and verifiable. This satisfies accuracy requirements for a *pipeline validation* study. |
| **III. Data Hygiene** | **PASS** | Synthetic data will be checksummed upon generation. Transformations will write new files (no in-place edits). |
| **IV. Single Source of Truth** | **PASS** | Results in `paper/` will be generated programmatically from `data/` artifacts. |
| **V. Versioning Discipline** | **PASS** | Content hashes for `data/` and `code/` will be recorded in `state/`. |
| **VI. Biological Plausibility** | **PASS** | Feature importance will be validated against KEGG pathways (Jaccard ≥ 0.3 or p < 0.05). The synthetic generator embeds known pathways (proline, ABA) as ground truth to enable this validation. |
| **VII. Cross-Stress Generalizability** | **PASS** | LODO and cross-stress (train drought, test salinity) evaluations are mandated phases. The synthetic generator will simulate distinct stress vectors to ensure these tests are non-trivial. |

## Project Structure

### Documentation (this feature)
```text
specs/001-predict-plant-stress-resilience/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)
```text
projects/PROJ-455-predicting-plant-stress-resilience-from-/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── ingest.py       # FR-001, FR-002, FR-003 (Includes Mock and Real Adapters)
│   │   └── preprocess.py   # FR-002.1, FR-009
│   ├── models/
│   │   ├── train.py        # FR-004, FR-005
│   │   └── validate.py     # FR-006, FR-007, FR-010
│   ├── analysis/
│   │   └── pathway.py      # FR-008, FR-012
│   └── main.py             # Orchestration
├── data/
│   ├── raw/                # Downloaded, checksummed (or generated synthetic)
│   ├── processed/          # Normalized, imputed
│   └── results/            # Model outputs, metrics
├── contracts/              # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── model_result.schema.yaml
│   └── recovery.schema.yaml
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to minimize overhead for a data pipeline. Modular separation (`data`, `models`, `analysis`) ensures testability and adherence to FRs.

## Complexity Tracking
*No violations detected. The single-project structure is sufficient for a linear data pipeline.*

## Phase Mapping to Requirements
- **Phase 0 (Research)**: Dataset verification, method selection (RF vs SVM), KEGG mapping strategy, definition of Mechanism-Guided Synthetic Generator parameters.
- **Phase 1 (Data Model)**: Define schemas for `MetabolomicProfile`, `RecoveryMetric`, `ModelResult`.
- **Phase 2 (Implementation)**:
  - **Step 2.1 (Data Ingestion)**: Implement FR-001, FR-002, FR-003. **Action**: Implement `ingest.py` with a **Mock Adapter** (generates mechanism-guided synthetic data) and a **Real Adapter** (stub for NCBI GEO/Zenodo).
  - **Step 2.2 (Preprocessing)**: Implement FR-002.1, FR-009, FR-011. **Action**: Include logic to simulate heterogeneous metrics (biomass, survival) to test normalization.
  - **Step 2.3 (Model Training)**: Implement FR-004, FR-005.
  - **Step 2.4 (Validation)**: Implement FR-006, FR-007, FR-010. **Action**: Implement **LODO Simulation** by splitting synthetic data into virtual datasets with distinct noise profiles.
  - **Step 2.5 (Biological Validation)**: Implement FR-008, FR-012. **Action**: Validate against the ground-truth pathways embedded in the synthetic generator.
  - **Step 2.6 (Benchmarking)**: **Action**: Run full pipeline with a timer to verify SC-005 (≤6 hours).
- **Phase 3 (Testing)**: Verify SC-001 to SC-005.
