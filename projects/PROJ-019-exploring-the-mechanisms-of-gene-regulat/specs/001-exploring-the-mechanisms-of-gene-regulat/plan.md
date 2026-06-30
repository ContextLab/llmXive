# Implementation Plan: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

**Branch**: `001-gene-regulation` | **Date**: 2024-05-21 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This feature implements a computational pipeline to analyze ATAC-seq and ChIP-seq peak data from ENCODE for five cell types (GM12878, K562, HepG2, H1-hESC, IMR90). The goal is to identify cell-type-specific transcription factor (TF) motifs using FIMO/HOMER, compute enrichment via Fisher's exact test with Benjamini-Hochberg correction, and validate findings against independent ChIP-seq data. The pipeline is constrained to run on CPU-only CI (2 cores, 7GB RAM, 14GB disk) within 6 hours.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pybedtools`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `requests`, `tqdm`, `pyyaml`  
**Storage**: Local filesystem (`TMP_DIR`), temporary BED/JSON files. No database.  
**Testing**: `pytest` (unit tests for parsers, integration tests for pipeline stages).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Data analysis pipeline / CLI.  
**Performance Goals**: Complete full analysis (download to viz) in ≤6 hours.  
**Constraints**: No GPU, ≤7GB RAM usage peak, ≤14GB disk usage, exponential backoff for network.  
**Scale/Scope**: 5 cell types, ~2GB raw download, ~10k-100k peaks per cell type (estimated).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | **PASS** | Plan mandates pinned `requirements.txt`, random seeds, and re-runnable scripts from `data/`. |
| II. Verified Accuracy | **PASS** | Plan requires citing only verified URLs from the dataset block; external ChIP-seq validation data will be sourced from public repositories with explicit versioning. |
| III. Data Hygiene | **PASS** | Plan includes checksumming raw downloads, no in-place modification, and derivation logging. |
| IV. Single Source of Truth | **PASS** | All figures/stats trace to `data/` artifacts and `code/` blocks. |
| V. Versioning Discipline | **PASS** | Artifact hashes will be recorded in state YAML; content hashes for scripts. |
| VI. Public Dataset Provenance | **PASS** | Plan explicitly requires recording ENCODE accession IDs, release versions, and download dates for all peak files. |
| VII. Motif & Annotation Transparency | **PASS** | Plan mandates retaining original motif IDs and database versions (JASPAR) in result tables. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── ingest/
│   ├── download.py          # ENCODE download with backoff
│   ├── parse.py             # BED parsing & annotation
│   └── __init__.py
├── analysis/
│   ├── motif_scan.py        # FIMO/HOMER wrapper (CPU)
│   ├── enrichment.py        # Fisher's test & BH correction
│   └── __init__.py
├── viz/
│   ├── heatmap.py           # Clustering & silhouette score
│   ├── validation.py        # ChIP-seq overlap
│   └── __init__.py
├── main.py                  # Orchestration
└── utils/
    ├── config.py            # Paths, thresholds
    └── io.py                # Checksums, logging

tests/
├── contract/                # Schema validation tests
├── integration/             # End-to-end pipeline tests
└── unit/                    # Parser, stats logic tests

data/
├── raw/                     # Downloaded ENCODE files
├── processed/               # Annotated peaks, motif matches
└── results/                 # Enrichment tables, plots

requirements.txt
```

**Structure Decision**: Single project structure (`src/` based) selected for simplicity and CI compatibility. Modular separation (`ingest`, `analysis`, `viz`) ensures testability and adherence to Constitution Principle I (Reproducibility).

## Complexity Tracking

No violations detected. The pipeline complexity is justified by the need to handle genomic coordinate systems, statistical corrections, and multi-step validation, all within strict resource constraints.
