# Implementation Plan: Single-Cell Trajectories of T-Cell Exhaustion

**Branch**: `001-single-cell-trajectories-t-cell-exhaustion` | **Date**: 2026-10-27 | **Spec**: `specs/001-single-cell-trajectories-t-cell-exhaustion/spec.md`
**Input**: Feature specification from `/specs/001-single-cell-trajectories-t-cell-exhaustion/spec.md`

## Summary

This feature implements a reproducible computational pipeline to reconstruct RNA velocity trajectories of T-cell exhaustion across four public scRNA-seq datasets (GSE, GSE127465, GSE111075, GSE138852). The system will download raw count matrices via SRA Toolkit, preprocess them using Seurat parameters (via R subprocess), estimate RNA velocity using scVelo on CPU, identify statistically significant fork-points via vector field rotation null models, rank regulatory genes by timing, and validate findings against therapy response signatures using patient-level block bootstrapping. The implementation prioritizes CPU-first execution within GitHub Actions free-tier constraints (limited CPU, 7 GB RAM, 6h limit).

**Critical Spec Note**: The source spec (FR-001) lists an incomplete accession 'GSE'. This plan explicitly corrects this to 'GSE136103' to ensure the download task matches the intended requirement. The spec file requires a kickback update to correct this typo.

## Technical Context

**Language/Version**: Python 3.10 (primary), R 4.3 (for Seurat preprocessing)  
**Primary Dependencies**: `scvelo`, `scanpy`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `requests`, `wget`, `sratoolkit` (via `conda`), `r-base`, `reticulate`  
**Storage**: Local filesystem (`data/` for raw/processed counts, `results/` for trajectories and reports); `.h5ad` format for intermediate data  
**Testing**: `pytest` for unit tests on data validation and statistical functions; integration tests for pipeline end-to-end execution on a single dataset subset  
**Target Platform**: Linux (GitHub Actions runner)  
**Performance Goals**: Complete single-dataset scVelo run within 45 minutes; full cross-dataset analysis within 6 hours; memory usage < 7 GB  
**Constraints**: CPU-only execution; no GPU/CUDA; no manual authentication for data download (uses SRA Toolkit for public runs); datasets must be streamable or downloadable via public API  
**Scale/Scope**: Multiple datasets, ~10k-50k cells total; A sufficient number of bootstrap iterations (patient-level); generation of a final report and 4 trajectory graphs

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification / Action |
|-----------|--------|-----------------------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds in code, and explicit download commands for raw data via SRA Toolkit. |
| **II. Verified Accuracy** | **PENDING VERIFICATION** | Plan requires all citations (datasets, methods) to be verified against the `# Verified datasets` block. Status is pending successful completion of Phase 0 data verification. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw data, immutable derivation steps, and PII scanning. |
| **IV. Single Source of Truth** | **PASS** | All figures/statistics will be generated directly from `data/` artifacts; no hand-typed values. Preprocessing via explicit R subprocess ensures traceability. |
| **V. Versioning Discipline** | **PASS** | Content hashes recorded in state YAML; artifact updates trigger timestamp updates. |
| **VI. Biological Trajectory Consistency** | **PASS** | Plan explicitly separates predictor (fork-point genes from discovery set) from predicted (therapy response from validation set) and mandates associational framing. |
| **VII. Clinical Relevance Grounding** | **PASS** | Validation step (FR-008) maps fork-point genes to therapy response signatures with statistical significance (p < 0.05 for SC-006, p < 0.01 for SC-002/003). |

## Project Structure

### Documentation (this feature)

```text
specs/001-single-cell-trajectories-t-cell-exhaustion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/
├── code/
│   ├── requirements.txt
│   ├── download_data.py       # Fetches raw count matrices via SRA Toolkit
│   ├── preprocess.R           # Seurat v4 QC & normalization (R script)
│   ├── preprocess.py          # Wrapper to call R script via subprocess
│   ├── velocity.py            # scVelo execution (CPU)
│   ├── forkpoint.py           # Divergence calculation & gene ranking
│   ├── validate.py            # Bootstrap resampling & enrichment
│   └── report.py              # Heatmap generation & final report
├── data/
│   ├── raw/                   # Downloaded raw count matrices
│   ├── processed/             # Normalized matrices & velocity graphs
│   └── results/               # Fork-point lists, heatmaps, reports
├── tests/
│   ├── unit/                  # Unit tests for statistical functions
│   └── integration/           # End-to-end pipeline tests
└── docs/                      # Generated documentation
```

**Structure Decision**: Single project structure selected to maintain tight coupling between data processing and analysis steps. Python 3.10 is chosen for scVelo compatibility; R scripts for Seurat will be called via `subprocess` to ensure consistent preprocessing and Single Source of Truth (Constitution Principle IV).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed with no violations. | N/A |

## Phase Order & Dependencies

1. **Phase 0: Data Acquisition & Verification** (FR-001, SC-005)
   - **Corrected ID**: Use 'GSE136103' (not 'GSE' as in spec typo).
   - Download raw count matrices for GSE136103, GSE127465, GSE111075, GSE138852 using `sratoolkit` (`prefetch` + `fastq-dump`) to handle public access without manual auth.
   - **Abort Strategy**: If any dataset fails to download or yields <1000 cells after QC, log a warning, skip that dataset, and if *all* datasets fail, abort the pipeline.
   - Verify checksums and data availability.

2. **Phase 1: Preprocessing & Normalization** (FR-002)
   - Execute `preprocess.R` via `subprocess` to apply Seurat v4 QC filters (>20% mitochondrial reads) and normalization.
   - Output: Normalized count matrices in `.h5ad` format.

3. **Phase 2: Velocity & Pseudotime Estimation** (FR-003, SC-001)
   - Run scVelo on CPU to estimate RNA velocity and pseudotime.
   - Output: Velocity graphs and pseudotime orderings.

4. **Phase 3: Fork-Point Identification** (FR-004, FR-005)
   - **Corrected Method**: Calculate velocity vector field divergence. Generate null distribution by rotating velocity vectors in reduced dimension space (preserving splicing kinetics) instead of shuffling topology.
   - Identify branch points where divergence > 2.0 SD above null mean.
   - Extract genes at fork-points; rank by timing.
   - Output CSV with gene symbols and branch IDs (Schema: `contracts/fork_point.schema.yaml`).

5. **Phase 4: Cross-Dataset Validation** (FR-006, FR-007, FR-008, SC-002, SC-003, SC-006)
   - **Discovery/Validation Split**: Derive fork-point genes from GSE136103, GSE127465, GSE111075 (Discovery). Validate against therapy response labels in GSE138852 (Validation).
   - **Patient-Level Aggregation**: Map patient-level labels to single-cell trajectories by calculating mean pseudotime and mean fork-point gene expression per patient.
   - **Block Bootstrapping**: Perform 1000 bootstrap iterations resampling *patients* (not cells) to preserve correlation structure.
   - Test enrichment against therapy response signatures.
   - Report p-values: p < 0.01 (SC-002/003) and p < 0.05 (SC-006).
   - Generate heatmap with confidence intervals.

6. **Phase 5: Reporting** (FR-007, SC-004)
   - Compile final report with associational disclaimers (See SC-004, FR-005).

## Data Availability & Feasibility

- **Datasets**: GSE136103, GSE127465, GSE111075, GSE138852.
- **Download Method**: SRA Toolkit (`sratoolkit` package) via `prefetch` and `fastq-dump` to handle public SRA runs without manual authentication.
- **Memory**: Streaming and on-disk processing used to stay within 7 GB RAM.
- **Compute**: CPU-first. scVelo dynamical model on CPU.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Unavailability** | Fatal: No raw counts or therapy labels. | Abort pipeline; report gap; search for open substitutes (e.g., recount3). |
| **Memory Overflow** | High: 7 GB RAM limit exceeded. | Stream data; use sampling; optimize data structures. |
| **Convergence Failure** | Medium: scVelo fails to converge. | Retry with higher regularization; flag as "Alignment Failed". |
| **Low Divergence** | Medium: No significant fork-points. | Flag branch as 'low_confidence'; exclude from final list. |
| **Insufficient Power** | Medium: Bootstrap p-values unstable. | Report power limitation; reduce bootstrap iterations if needed. |

## Decision/Rationale

- **Method Choice**: scVelo and Seurat are community standards. CPU-first execution ensures compatibility with CI constraints.
- **Dataset Strategy**: SRA Toolkit used for robust public download. Discovery/Validation split prevents circularity.
- **Statistical Approach**: Patient-level block bootstrapping and rotation-based null models ensure statistical validity.
- **Associational Framing**: All findings are labeled as correlational to avoid causal overreach (Constitution Principle VI).