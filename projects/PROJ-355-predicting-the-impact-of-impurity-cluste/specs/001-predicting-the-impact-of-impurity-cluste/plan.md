# Implementation Plan: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Branch**: `[001-impurity-clustering-segregation]` | **Date**: 2025-01-15 | **Spec**: `spec.md`
**Input**: Feature specification from `spec.md`

## Summary

This feature implements a computational pipeline to predict how impurity clustering at grain boundaries (GBs) influences segregation energy. The approach involves downloading bulk configurations from Materials Project and OQMD, constructing GB supercells, computing clustering descriptors (RDF, pair correlation, Voronoi counts) specifically within the interface region, and training a lightweight regression model (RandomForest or Linear Regression) to predict segregation energy. 

**Critical Constraint**: The plan strictly adheres to the constraint of running on a GitHub Actions free-tier runner (CPU-only, limited RAM) by sampling data and using CPU-tractable libraries. **Scientific Constraint**: To avoid circularity, if segregation energy labels are generated via simulation, the descriptors must be computed from a structurally perturbed representation or a distinct potential, or the study must explicitly limit claims to "potential-dependent trends." No heuristics or surrogate models will be used for label generation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymatgen` (structure handling), `scikit-learn` (modeling), `numpy`, `pandas`, `ase` (atomistic simulation interface), `statsmodels` (statistical testing), `requests` (data fetching), `jsonschema` (contract enforcement).  
**Storage**: Local file system (`data/raw`, `data/processed`, `results`).  
**Testing**: `pytest` with unit tests for descriptor computation and integration tests for the full pipeline.  
**Target Platform**: Linux (GitHub Actions runner).  
**Project Type**: Computational research pipeline / CLI.  
**Performance Goals**: Full pipeline execution (data download, descriptor calc, model training) within 6 hours on 2 CPU cores.  
**Constraints**: 
- No GPU usage; no deep learning.
- Data subset to fit ~ GB RAM.
- Retry logic for external APIs: **FR-001** mandates at most 3 failed attempts before marking the dataset as inaccessible and logging a `[DATA_UNAVAILABLE]` error.
- Contract Enforcement: All data inputs/outputs MUST be validated against `contracts/` schemas using `jsonschema` before processing.

**Scale/Scope**: Sampled dataset (target N=30-1000 configurations); 3+ alloy systems.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`. `requirements.txt` pins versions. Data fetched via deterministic scripts. |
| **II. Verified Accuracy** | PASS | The Reference-Validator Agent runs **before** `download.py`. It parses `data/metadata.yaml` to verify that `download_source` URLs match a whitelist of verified repositories. If a URL is not whitelisted, the pipeline halts. |
| **III. Data Hygiene** | PASS | Raw data checksums recorded in `state/`. Derivations create new files; no in-place edits. |
| **IV. Single Source of Truth** | PASS | All metrics (R², RMSE) saved as JSON in `results/`. **Immediately after generation**, the JSON file is hashed (SHA256) and the hash is recorded in `state/...yaml`, linking the output to the specific code commit. |
| **V. Versioning Discipline** | PASS | Artifacts hashed; `state` updated on change. |
| **VI. Materials Data Provenance** | PASS | Bulk configs sourced strictly from MP/OQMD as per spec; dataset IDs recorded in `data/metadata.yaml`. |
| **VII. Model Evaluation Transparency** | PASS | 5-fold CV (or LOOCV) with fixed seed; metrics saved to JSON with code version link. |

## Project Structure

### Documentation (this feature)

```text
specs/001-impurity-clustering-segregation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-355-predicting-the-impact-of-impurity-cluste/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, hyperparameters
│   ├── data/
│   │   ├── download.py        # FR-001: MP/OQMD fetch with retry logic (max 3 attempts)
│   │   ├── gb_builder.py      # US-1: GB supercell construction
│   │   └── descriptors.py     # FR-002: RDF, Pair, Voronoi computation
│   ├── modeling/
│   │   ├── train.py           # FR-004: Model training & CV
│   │   ├── evaluate.py        # FR-005, FR-006: Sensitivity & Hypothesis testing
│   │   └── utils.py           # Collinearity detection (VIF), Contract validation
│   └── main.py                # Pipeline orchestration
├── data/
│   ├── raw/                   # Downloaded bulk configs
│   ├── processed/             # GB structures, descriptors, energies
│   └── metadata.yaml          # Provenance records
├── results/
│   ├── metrics.json           # R², RMSE, p-values
│   └── sensitivity_report.json
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to minimize overhead and ensure tight coupling between data processing and modeling steps, essential for reproducibility on constrained CI runners.

**Contract Enforcement**: 
- `code/data/download.py` validates output against `contracts/dataset.schema.yaml` before saving.
- `code/modeling/train.py` validates input dataset against `contracts/dataset.schema.yaml` before training.
- `code/modeling/evaluate.py` validates output against `contracts/output_schema.schema.yaml` before saving.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | The complexity of GB construction and descriptor calculation is inherent to the physics problem; no simpler alternative exists that satisfies the scientific requirements. |