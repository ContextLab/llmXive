# Implementation Plan: Quantitative Analysis of Gene Expression Dynamics during Human Brain Development

**Branch**: `001-gene-regulation` | **Date**: 2026-08-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a quantitative pipeline to analyze gene regulatory network (GRN) rewiring during human brain development. Using a high-resolution human fetal brain single-cell RNA-seq atlas, the system will integrate time-resolved expression data, infer stage-specific GRNs using a sliding-window pseudotime approach with GRNBoost2, and identify topological "rewiring events." These events are then correlated with neurological disorder risk genes from GWAS catalogs using hypergeometric enrichment and permutation tests. Results are validated topologically against an independent single-cell cohort and expressionally against bulk RNA-seq time courses.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scanpy`, `harmonypy`, `arboreto` (GRNBoost2), `monocle3` (via `py-monocle` or `scanpy` trajectory), `scipy`, `statsmodels`, `pandas`, `matplotlib`, `GEOparse`  
**Storage**: H5AD (AnnData) for expression matrices, JSON/CSV for network edges and enrichment results  
**Testing**: `pytest` for pipeline stages and contract validation  
**Target Platform**: Linux (GitHub Actions Runner / Kaggle GPU escape hatch)  
**Project Type**: Research Analysis Pipeline  
**Performance Goals**: Process $\ge 50,000$ cells; 1,000 permutation iterations within 6 hours.  
**Constraints**: 7 GB RAM / 14 GB Disk (CPU-first); results must be associational only.  
**Scale/Scope**: Human Fetal Brain scRNA-seq Atlas (Primary) + Independent scRNA-seq Cohort (Validation) + Bulk RNA-seq (Cross-check).

## Constitution Check

| Principle | Requirement | Plan Alignment |
|-----------|-------------|----------------|
| I. Reproducibility | Pinned seeds & canonical sources | All scripts will use `random_state=42`; data fetched from verified scRNA-seq atlas sources. |
| II. Verified Accuracy | Citation validation | All external GWAS references will be passed through the Reference-Validator Agent. |
| III. Data Hygiene | Checksums & No in-place mods | `data/raw/` is read-only; `data/processed/` stores versioned `.h5ad` and `.csv` files. |
| IV. Single Source of Truth | Traceability | Figures and tables generated directly from processed data files via `code/` scripts. |
| V. Versioning | Content hashing | State YAML updated after each major artifact generation. |
| VI. Network Topology | Sliding-window GRN | Implemented via `arboreto` (GRNBoost2) over pseudotime windows (Task 4-5). |
| VII. Disorder Correlation | GWAS mapping & Validation | Hypergeometric tests + 1,000 permutations + validation against independent scRNA-seq cohort and bulk expression (Task 7-9). |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
src/
├── data_pipeline/       # Acquisition, QC, Harmony, LISI
├── network_inference/    # Pseudotime, GRNBoost2, Rewiring
├── clinical_analysis/    # GWAS mapping, Enrichment, Permutations
└── utils/               # Logging, paths, statistical helpers
tests/
├── contract/            # Schema validation tests
├── integration/         # End-to-end pipeline tests
└── unit/                # Individual function tests
```

**Structure Decision**: Single project structure (Option 1) as this is a linear research pipeline.

## Implementation Phases

### Phase 0: Data Acquisition & Preprocessing
1. **Data Loader**: Implement loader for selected human fetal brain scRNA-seq atlas to extract expression and metadata (age, donor) $\rightarrow$ `data/raw/atlas_raw.h5ad`. (**FR-001**)
2. **QC & Normalization**: Filter cells/genes, normalize counts, and detect developmental window gaps (halt if $< 10$ cells in a window). (**FR-011**, **SC-001**, **SC-007**)
3. **Batch Integration**: Apply Harmony for donor correction. Calculate LISI scores; abort if LISI $< 1.2$. Measure variance explained by stage vs batch. (**FR-002**, **FR-012**, **SC-002**, **SC-008**)

### Phase 1: Dynamic Network Inference
4. **Trajectory & Windowing**: Compute pseudotime (Monocle3/Slingshot) and partition cells into sliding windows. (**FR-003**)
5. **GRN Reconstruction**: Run GRNBoost2 for each window to infer TF-target edges. Calculate edge weights and hub stability. (**FR-003**, **FR-004**)
6. **Rewiring Analysis**: Identify "rewiring events" (edge weight diffs). Perform sensitivity analysis by sweeping thresholds $\{0.01, 0.05, 0.1\}$ and calculate Jaccard similarity. (**FR-010**, **SC-005**)

### Phase 2: Clinical Correlation & Validation
7. **GWAS Mapping**: Map external disorder risk genes to rewired hubs. Perform hypergeometric enrichment tests. (**FR-005**, **SC-004**)
8. **Statistical Significance**: Execute 1,000 permutation tests. Apply Benjamini-Hochberg correction. Report p-values as $p < 1/N$ if zero extremes found. (**FR-006**, **FR-009**, **FR-013**, **SC-003**, **SC-009**)
9. **Multi-level Validation**: 
    - **Topological**: Validate rewiring events using an independent single-cell RNA-seq cohort.
    - **Expression**: Validate hub importance using bulk RNA-seq time courses (BrainSpan) by checking for significant differential expression of hubs in the corresponding windows. (**FR-014**, **SC-006**)

### Phase 3: Results Generation
10. **Visualization & Reporting**: Generate network topology plots (Plotly/Cytoscape format) and result tables. Ensure all claims are framed as "associational." (**FR-007**, **FR-008**)
