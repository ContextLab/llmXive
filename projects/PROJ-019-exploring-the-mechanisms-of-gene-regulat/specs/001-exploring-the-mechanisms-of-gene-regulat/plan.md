# Implementation Plan: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

**Branch**: `001-gene-regulation` | **Date**: 2023-10-27 | **Spec**: `spec.md`

## Summary

This project implements a reproducible pipeline to identify cell-type-specific transcription factor (TF) motifs driving gene regulation. The approach involves downloading ATAC-seq and ChIP-seq peak data for five major cell types from ENCODE., annotating these regions with gene symbols, and performing **differential enrichment analysis**. Unlike absolute enrichment (vs. genome), this pipeline tests whether a motif is enriched in Cell Type A peaks *relative to the union of peaks from the other four cell types*. This aligns with FR-004 and the spec's requirement to identify "cell-type-specific" signatures. The final output includes visualizations of enrichment profiles and cross-validation against independent ChIP-seq data using statistical enrichment tests.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `requests`, `pybedtools`, `fimo` (MEME suite), `pandas`, `scipy`, `seaborn`, `matplotlib`, `biopython`  
**Storage**: Local filesystem (`TMP_DIR`), no database required.  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, ~7GB RAM)  
**Project Type**: Computational Biology Pipeline / CLI  
**Performance Goals**: Complete full analysis within 6 hours on CPU-only runner; memory usage < 7GB.  
**Constraints**: No GPU; strict disk limits (a constrained capacity); robust error handling for network failures (exponential backoff); strict data provenance per Constitution.  
**Scale/Scope**: cell types, [deferred]-peaks per cell type, Approximately one thousand JASPAR motifs.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Ensured by pinning dependencies in `requirements.txt`, using fixed random seeds for any stochastic processes, and fetching data from canonical ENCODE URLs with checksums recorded.
- **II. Verified Accuracy**: All external dataset references (ENCODE, JASPAR) will be validated for reachability and format before analysis. Citations in reports will be checked against primary sources.
- **III. Data Hygiene**: Raw data will be downloaded to `data/raw/` with checksums. Intermediate files (parsed peaks, motif matches) will be stored in `data/interim/` with derivation logs. No in-place modifications.
- **IV. Single Source of Truth**: All figures and statistics in the final report will be generated directly from `data/processed/` files by scripts in `code/`. No manual entry.
- **V. Versioning Discipline**: Every artifact change updates the project's state file: `state/projects/PROJ-019-exploring-the-mechanisms-of-gene-regulat.yaml` `updated_at` timestamp.
- **VI. Public Dataset Provenance**: ENCODE accession IDs, release versions, and download dates will be explicitly recorded in `data/provenance.json`.
- **VII. Motif & Annotation Transparency**: JASPAR database version and motif IDs will be included in all result tables. GO term IDs will be cited for validation steps.

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── peak.schema.yaml
│   ├── motif_match.schema.yaml
│   ├── enrichment.schema.yaml
│   └── validation.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-019-exploring-the-mechanisms-of-gene-regulat/
├── code/
│   ├── __init__.py
│   ├── download.py          # ENCODE ingestion with retry logic (FR-001, FR-006)
│   ├── preprocess.py        # BED parsing, annotation, and Background Union aggregation (FR-002, FR-004)
│   ├── scan.py              # FIMO execution (FR-003)
│   ├── enrichment.py        # Fisher's test, BH correction (FR-004)
│   ├── visualize.py         # Heatmaps, validation plots (FR-005)
│   └── main.py              # Orchestrator
├── data/
│   ├── raw/                 # Downloaded ENCODE files
│   ├── interim/             # Parsed peaks, motif matches, background unions
│   ├── processed/           # Enrichment results, validation stats
│   └── provenance.json      # Checksums, versions, dates
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure with modular `code/` scripts to ensure isolation and reproducibility. The `data/` directory follows the standard raw/interim/processed hierarchy to enforce data hygiene (Constitution III). The `background.py` script has been removed; background generation is now a deterministic aggregation step in `preprocess.py` to align with FR-004.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The current structure is minimal and directly maps to the spec requirements. | N/A |
