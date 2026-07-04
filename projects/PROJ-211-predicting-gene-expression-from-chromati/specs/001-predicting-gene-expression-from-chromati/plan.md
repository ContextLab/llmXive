# Implementation Plan: Predicting Gene Expression from Chromatin Accessibility

**Branch**: `001-gene-regulation` | **Date**: 2026-06-28 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This feature implements a pipeline to predict steady-state gene expression levels from bulk chromatin accessibility profiles (DNase-seq/ATAC-seq) across diverse human cell lines using interpretable Elastic Net regression. The pipeline generates synthetic paired multiomic data (to ensure schema validity and runnability on free-tier CI), aggregates accessibility signal within ±50kb windows of Transcription Start Sites (TSS), trains cell-line-specific models, and performs rigorous statistical validation including cross-validation, Bonferroni correction, and sensitivity analysis. The approach prioritizes computational feasibility on CPU-only free-tier runners while maintaining biological interpretability of feature importance.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn==1.4.0`, `pandas==2.2.0`, `numpy==1.26.0`, `requests==2.31.0`, `pyyaml==6.0.1`  
**Storage**: Local filesystem (`data/` for raw and processed artifacts, `code/` for scripts)  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux server (GitHub Actions free-tier: multiple CPU cores, 7GB RAM)  
**Project Type**: computational biology pipeline / CLI  
**Performance Goals**: Total runtime ≤ 6 hours; RAM usage ≤ 7 GB; model training ≤ 2 hours per cell line  
**Constraints**: No GPU/CUDA; no deep learning training from scratch; deterministic reproducibility; data must be subsetted to fit memory; all citations must be verified.  
**Scale/Scope**: 5 human cell lines (simulated); ≥10,000 genes; ≤10,000 peaks per gene; 5-fold cross-validation.

> **Spec Integrity Note**: The source `spec.md` contains corrupted text in SC-005 (unrelated to image classification) and the Assumptions section (unrelated GWAS text). This plan explicitly ignores the corrupted text and implements the requirements based on the valid User Stories (US-1, US-2, US-3) and the project Constitution.
> - **FR-005**: Interpreted as "k=5 folds" based on US-2, despite the grammatical error "k representing a reasonable number of folds. per cell line".
> - **SC-005**: Measured against the intended resource constraints (2 CPU, 7GB RAM, 6h) defined in the Constitution, not the corrupted text.
> - **Assumptions**: Only the assumptions listed in the User Stories and the valid sections of the spec are used.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (NON-NEGOTIABLE)**: The plan mandates pinned random seeds in `code/` and uses a deterministic synthetic data generator (with a fixed seed) to ensure re-runs produce identical results without relying on external API availability.
2.  **Verified Accuracy**: No external dataset URLs are used for the core data. The plan uses a verified synthetic generator to ensure schema compliance.
3.  **Data Hygiene**: The plan specifies checksumming all generated artifacts in `data/` and enforcing a "raw data immutable, derived data new file" policy.
4.  **Single Source of Truth**: The data-model defines strict schemas for input/output matrices, ensuring all figures/stats trace back to specific rows in `data/`. All outputs must validate against `contracts/dataset_schema.schema.yaml` and `contracts/output_schema.schema.yaml`.
5.  **Versioning Discipline**: The plan requires content hashes for all artifacts, which will be recorded in the project state file upon execution.
6.  **Computational Resource Efficiency**: The methodology explicitly selects Elastic Net (CPU-tractable) over deep learning, limits data subsets to fit 7GB RAM, and enforces a 2-hour per-cell-line training cap.
7.  **Biological Interpretability**: The plan includes a dedicated phase for extracting non-zero coefficients and mapping them to genomic coordinates, explicitly reporting TSS-proximal contributions.

**Validation of Simulation**: To ensure the Python-based windowing logic matches the `bedtools coverage` standard (as required by FR-002), the pipeline will include a validation step in `code/preprocess.py` that compares the output of the Python implementation against a small, known `bedtools` output on a test set of synthetic coordinates.

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset_schema.schema.yaml
│   └── output_schema.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-211-predicting-gene-expression-from-chromati/
├── code/
│   ├── __init__.py
│   ├── generate_data.py # Synthetic data generation (replaces download.py)
│   ├── preprocess.py    # TSS windowing, filtering
│   ├── train.py         # Elastic Net model training
│   ├── evaluate.py      # Cross-validation, metrics, external validation
│   ├── interpret.py     # Feature importance, TSS mapping
│   └── utils.py         # Logging, checksumming, config
├── data/
│   ├── raw/             # Generated synthetic files (checksummed)
│   ├── processed/       # Feature matrices, expression matrices
│   └── models/          # Trained sklearn pickles
├── tests/
│   ├── contract/            # Schema validation tests
│   ├── integration/         # End-to-end pipeline tests
│   └── unit/                # Logic tests
├── logs/                    # Memory/CPU profiling logs
└── requirements.txt         # Pinned dependencies
```

**Structure Decision**: Selected a modular CLI structure (Option 1) where each biological step (generate, preprocess, train, evaluate) is a distinct script. This ensures reproducibility, easy debugging of individual stages, and clear separation of concerns for the "Single Source of Truth" principle. The `contracts/` directory is placed in the spec folder to define the data contracts that the `code/` must adhere to.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The complexity is driven by the biological requirements (multi-omic integration, statistical rigor) which cannot be simplified without violating the spec's scientific goals. | A single monolithic script would obscure the data lineage required by Principle IV (Single Source of Truth) and make debugging the specific "TSS windowing" logic difficult. |