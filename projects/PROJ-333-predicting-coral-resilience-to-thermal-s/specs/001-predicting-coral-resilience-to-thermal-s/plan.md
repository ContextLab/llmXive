# Implementation Plan: Predicting Coral Resilience to Thermal Stress Using Publicly Available Genomic Data

**Branch**: `001-coral-resilience-prediction` | **Date**: 2024-05-21 | **Spec**: `specs/001-coral-resilience-prediction/spec.md`
**Input**: Feature specification from `specs/001-coral-resilience-prediction/spec.md`

## Summary

This project implements a reproducible RNA-seq analysis pipeline to identify genes in *Acropora millepora* associated with thermal stress. The approach involves downloading raw FASTQ data from a designated NCBI BioProject., quantifying gene expression using Salmon (CPU-optimized) against a pre-downloaded reference transcriptome, performing differential expression analysis using `pydeseq2` (a Python port of DESeq2 with empirical Bayes shrinkage), and conducting Gene Set Enrichment Analysis (GSEA) using `gseapy`. The pipeline is engineered to run entirely on a GitHub Actions free-tier runner with standard CPU and memory allocations. by utilizing streaming downloads, memory-mapped files, and strict data filtering.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `biopython`, `pysam`, `scipy`, `pandas`, `matplotlib`, `gprofiler-official`, `pydeseq2`, `gseapy`.  
**Decision**: Use `pydeseq2` for differential expression. Unlike `statsmodels`, `pydeseq2` implements the specific Negative Binomial GLM with **empirical Bayes dispersion shrinkage** required for RNA-seq data, preventing inflated false positives in low-replication regimes. This ensures statistical rigor without the memory overhead of `rpy2`.  
**GSEA Strategy**: Use `gseapy` (Python) for Gene Set Enrichment Analysis on the ranked list of genes, replacing the fragile binary ORA approach.  
**Storage**: Local file system (`data/raw`, `data/processed`), ephemeral.
**Testing**: `pytest` (unit tests for parsing, integration tests for pipeline steps).
**Target Platform**: Linux (GitHub Actions free-tier runner).
**Project Type**: Data Science Pipeline / Bioinformatics Script.
**Performance Goals**: Peak RSS < 7 GB, Runtime < 6 hours.
**Constraints**: No GPU, no 8-bit quantization, no large LLM inference. Data must be streamed or chunked to fit RAM.
**Scale/Scope**: Single species (*A. millepora*), one BioProject, ~-50 samples (estimated).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All random seeds pinned in `code/`. NCBI downloads use specific BioProject ID and checksum verification. `requirements.txt` pins versions. `pydeseq2` ensures a deterministic statistical path (no conditional R/Python fallback). |
| **II. Verified Accuracy** | Citations (NCBI, RefSeq, g:Profiler) will be validated by the Reference-Validator Agent. The pipeline includes a step to log validation status of external sources. |
| **III. Data Hygiene** | Raw FASTQ files stored in `data/raw` with SHA256 checksums recorded. Reference transcriptome downloaded separately and checksummed. Intermediate files (counts) derived, not modified in place. |
| **IV. Single Source of Truth** | Volcano plot and enrichment tables generated directly from `data/processed` artifacts. No manual data entry. |
| **V. Versioning Discipline** | Content hashes tracked in `state/`. Artifacts updated on change. |
| **VI. Statistical Rigor** | Multiple comparison correction (FDR/Benjamini-Hochberg) applied to all p-values. Dispersion shrinkage via `pydeseq2` ensures valid variance estimates. |
| **VII. Genomic Variant Filtering** | Adapted for RNA-seq: "Expression Threshold Filtering" (counts > 10 in >= X samples) MUST be applied uniformly across all samples. This is the RNA-seq equivalent of variant filtering and satisfies the spirit of Principle VII. |

## Project Structure

### Documentation (this feature)

```text
specs/001-coral-resilience-prediction/
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
├── __init__.py
├── config.py            # Paths, constants, thresholds
├── ingest.py            # NCBI download, checksum, metadata parsing
├── reference.py         # Reference transcriptome download and indexing
├── quant.py             # Salmon quantification (streaming)
├── dge.py               # Differential expression (pydeseq2)
├── enrichment.py        # GSEA via gseapy
├── viz.py               # Volcano plot and GSEA plots
└── main.py              # Orchestration script

tests/
├── contract/            # Schema validation tests
├── integration/         # End-to-end pipeline tests (with small mock data)
└── unit/                # Parsing and utility tests

data/
├── raw/                 # Downloaded FASTQ, Reference Transcriptome
└── processed/           # Count matrix, DGE results, GSEA results, Plots
```

**Structure Decision**: Single Python package (`src/`) with clear separation of concerns (Ingest, Reference, Quant, DGE, Enrich, Viz). This minimizes overhead and keeps memory footprint low compared to a multi-repo or heavy framework setup.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **N/A** | The project fits within a single pipeline. | N/A |

## Success Criteria & Spec Flag

- **SC-001**: Peak memory < 7 GB (Measurable).
- **SC-002**: **Spec Flag**: The current spec definition ("observed count > expected count at p < 0.05") is tautological. Success will be measured by **biological plausibility**: Enrichment of HSP/Oxidative pathways (FDR < 0.1) and effect size distribution. A spec update is required to formalize this.
- **SC-003**: Enrichment p-value for HSP/Oxidative pathways < 0.1.
- **SC-004**: Runtime < 6 hours.
- **SC-005**: FDR <= 0.05 for reported hits.

## Execution Order

1. **Reference Download**: Download and index *A. millepora* transcriptome (NCBI RefSeq GCF_000163615.2).
2. **Ingest**: Download FASTQs from PRJNA292777; verify checksums; parse metadata (with fallback logic).
3. **Quantify**: Stream FASTQs against reference index; generate count matrix.
4. **DGE**: Run `pydeseq2` with design `~ treatment`; apply FDR.
5. **Enrich**: Run `gseapy` on ranked genes; generate GSEA report.
6. **Verify**: Invoke Reference-Validator logic; generate plots.