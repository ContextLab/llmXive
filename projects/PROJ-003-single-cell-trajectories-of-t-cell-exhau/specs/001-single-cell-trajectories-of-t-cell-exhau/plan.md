# Implementation Plan: Single-Cell Trajectories of T-Cell Exhaustion

**Branch**: `001-single-cell-trajectories-t-cell-exhaustion` | **Date**: 2026-07-20 | **Spec**: `specs/001-single-cell-trajectories-of-t-cell-exhau/spec.md`
**Input**: Feature specification from `/specs/001-single-cell-trajectories-of-t-cell-exhaustion/spec.md`

## Summary

This project implements a reproducible computational pipeline to reconstruct transcriptional trajectories of T-cell exhaustion using scVelo and pseudotime alignment on four specific public scRNA-seq datasets (GSE, GSE127465, GSE111075, and GSE138852). The primary goal is to identify early fork-points in these trajectories that correlate with checkpoint therapy responsiveness. The technical approach involves downloading raw count matrices, preprocessing with Seurat v4 parameters (via Python wrappers or R-to-Python conversion), executing scVelo for velocity estimation on CPU-only hardware, detecting statistically significant branch points via permutation testing of *therapy response labels*, and validating findings across datasets using bootstrap resampling and therapy response signatures.

## Technical Context

**Language/Version**: Python 3.11 (Primary), R 4.3 (Preprocessing via `rpy2` or pre-processed files)  
**Primary Dependencies**: `scvelo`, `scanpy`, `seurat-wrappers` (or `reticulate` bridge), `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `requests`, `wget`  
**Storage**: Local file system (`.h5ad`, `.csv`, `.tsv`), GitHub Actions cache for intermediate files  
**Testing**: `pytest` (unit tests for data loading, integration tests for pipeline stages), `pytest-cov` for coverage  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU cores, ~7 GB RAM, ≤6 hours total) without GPU or CUDA.  
**Project Type**: Computational Biology Pipeline / Research Tool  
**Performance Goals**: Complete full pipeline (4 datasets) within 6 hours; single dataset velocity run < 45 mins; memory usage < 6GB peak  
**Constraints**: No GPU/CUDA; no manual authentication for data download; strict reproducibility (random seeds); observational data (no causal claims); datasets must be fetched programmatically without credentials.  
**Scale/Scope**: ~4 datasets, ~k-50k cells total (depending on filtering), ~k genes.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PARTIAL** | Plan mandates pinned `requirements.txt`, random seeds in `code/`, and programmatic data fetching via `wget`/`curl` from verified sources *if accessible*. Pipeline halts if datasets are inaccessible.|
| **II. Verified Accuracy** | **FAIL** | All dataset citations in `research.md` will be validated against the "Verified datasets" block, but currently, NO datasets have verified sources.  This is a blocking issue requiring either open substitutes or re-scoping.|
| **III. Data Hygiene** | **PASS** | Plan includes checksumming raw data upon download; derivations written to new filenames; PII scan integration. |
| **IV. Single Source of Truth** | **PASS** | Pipeline outputs (`.h5ad`, `.csv`) will be the sole source for figures and statistics in the final report. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes; `state/` YAML updated on artifact change. |
| **VI. Biological Trajectory Consistency** | **PASS** | Plan explicitly separates predictor (fork-point genes) from outcome (therapy response) and validates against independent signatures to ensure they are not mechanically derived from the same raw signal used to construct the trajectory.|
| **VII. Clinical Relevance Grounding** | **PASS** | Findings will be mapped to therapy response signatures (FR-008) and framed as associational, not causal.|

## Project Structure

### Documentation (this feature)

```text
specs/001-single-cell-trajectories-of-t-cell-exhaustion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── download_data.py       # FR-001: Download & cache raw matrices
│   ├── preprocess.py          # FR-002: QC, normalization, Seurat params
│   ├── velocity_analysis.py   # FR-003: scVelo execution (CPU)
│   ├── fork_point_detection.py# FR-004: Divergence & branch detection
│   ├── ranking.py             # FR-005: Gene ranking & CSV output
│   ├── validation.py          # FR-006, FR-008: Bootstrap & therapy sig
│   └── report_gen.py          # FR-007: Heatmap & final report
├── data/
│   ├── raw/                   # Downloaded raw matrices (checksummed)
│   ├── processed/             # Normalized, velocity graphs (.h5ad)
│   └── results/               # CSVs, heatmaps, reports
├── tests/
│   ├── unit/
│   │   ├── test_download.py
│   │   └── test_preprocess.py
│   └── integration/
│       └── test_pipeline.py
└── state/
    └── projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau.yaml
```

**Structure Decision**: Single project structure chosen to maintain tight coupling between data processing, analysis, and reporting, facilitating reproducibility on a single CI runner.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Principle I/II**: Data access is uncertain. | Mitigation plan in place. | No alternative without data availability.|

## Phase Breakdown & FR/SC Mapping

### Phase 0: Data Acquisition & Verification
*Addresses: FR-001, SC-005*
1.  **Action**: Implement `download_data.py` to fetch GSE136103, GSE127465, GSE111075, and GSE138852.
2.  **Constraint Check**: Verify datasets are accessible without auth. If a dataset requires auth, the pipeline will *halt* or switch to an open substitute (as per SC-005).
3.  **Output**: Checksummed raw files in `data/raw/`.

### Phase 1: Preprocessing & Quality Control
*Addresses: FR-002, SC-001*
1.  **Action**: Implement `preprocess.py` to filter cells (>20% mito), normalize (Seurat v4 params), and convert to `.h5ad`.
2.  **Constraint Check**: Ensure memory usage < 6GB. If dataset too large, implement streaming or sampling strategy (SC-001).
3.  **Output**: Clean count matrices and QC metrics.

### Phase 2: Velocity & Pseudotime Estimation
*Addresses: FR-003, SC-001*
1.  **Action**: Implement `velocity_analysis.py` using `scvelo` on CPU. Use stochastic model for speed. If resources permit a subset of the data can be analyzed with the dynamical model.
2.  **Constraint Check**: Verify runtime < 45 mins/dataset.
3.  **Output**: `.h5ad` files with velocity graphs and pseudotime.

### Phase 3: Fork-Point Identification
*Addresses: FR-004, FR-005, SC-004*
1.  **Action**: Implement `fork_point_detection.py`. Calculate divergence scores *based on a permutation test of therapy response labels*.
2.  **Constraint Check**: Ensure p-values are calculated via permutation testing. Frame results as associational (SC-004).
3.  **Output**: List of significant branch points and ranked genes.

### Phase 4: Cross-Dataset Validation
*Addresses: FR-006, FR-008, SC-002, SC-003, SC-006*
1.  **Action**: Implement `validation.py` for bootstrap resampling (a sufficient number of iterations) and therapy signature enrichment. Perform functional alignment of trajectories via UMAP projection using shared marker genes before calculating Spearman correlation. If therapy response labels are unavailable in GSE138852, SC-006 is marked as 'Not Applicable'.
2.  **Constraint Check**: Verify Spearman correlation (≥ 0.80) and Jaccard index thresholds. Ensure p < 0.01 for bootstrap tests.
3.  **Output**: Validation statistics, heatmaps, final report.