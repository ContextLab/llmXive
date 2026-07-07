# Implementation Plan: Predicting Coral Resilience to Thermal Stress Using Publicly Available Genomic Data

**Branch**: `001-coral-resilience-prediction` | **Date**: 2024-05-21 | **Spec**: `specs/001-coral-resilience-prediction/spec.md`
**Input**: Feature specification from `specs/001-coral-resilience-prediction/spec.md`

## Summary

This feature implements a reproducible RNA-seq analysis pipeline to identify genes associated with thermal stress in *Acropora millepora*. The approach ingests raw FASTQ data from NCBI BioProject **PRJNA321023** (confirmed thermal stress RNA-seq), quantifies expression using Salmon (CPU-optimized), performs differential expression analysis with DESeq2 (R), and generates biological insights via volcano plots and pathway enrichment. The pipeline is strictly constrained to run on GitHub Actions free-tier runners with limited CPU resources, constrained memory, and no GPU, by streaming data and subsampling where necessary.

## Technical Context

**Language/Version**: Python 3.11, R 4.3+ (via `rpy2` or separate R script), Bash 5.0
**Primary Dependencies**: `pandas`, `numpy`, `requests`, `biopython`, `rpy2`, `matplotlib`, `scikit-learn`, `pyyaml`, `pytest`, `memory-profiler`, `Salmon` (via conda/apt), `DESeq2` (via Bioconductor).
**Storage**: Local filesystem (`data/` for raw/processed, `results/` for outputs). No external DB.
**Testing**: `pytest` (unit/contract), `memory-profiler` (performance), shell script validation.
**Target Platform**: Linux (GitHub Actions Ubuntu runner).
**Project Type**: Computational Biology Pipeline / CLI.
**Performance Goals**: Peak RSS < 7 GB; Runtime < 6 hours.
**Constraints**: No GPU; No large model training; Must handle NCBI network timeouts; Must explicitly label results as "associational".
**Scale/Scope**: One BioProject (PRJNA321023), approx. 10-20 samples, ~30k genes.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinning random seeds in `code/` and fetching external datasets (NCBI) from canonical sources on every run. `requirements.txt` will pin versions.
- **II. Verified Accuracy**: All citations (NCBI, g:Profiler) will be verified against primary sources via `verify_citations.py`. The plan includes a `contracts/` schema to validate output structure against the spec.
- **III. Data Hygiene**: The pipeline will compute and record SHA256 checksums for all downloaded FASTQ files in `data/`. No in-place modification of raw data; derivations go to `data/processed/`.
- **IV. Single Source of Truth**: The plan defines a strict data flow: `raw` -> `quantified` -> `dge_results` -> `plots`. All figures in the final report will trace to specific rows in `data/processed/`.
- **V. Versioning Discipline**: Content hashes for all artifacts will be tracked in the project state file.
- **VI. Statistical Rigor**: The plan explicitly includes Benjamini-Hochberg FDR correction (FR-004) and mandates labeling results as "associational" (FR-006).
- **VII. Genomic Variant Filtering (RNA-seq Equivalent)**: While this is not a GWAS study, the Constitution's requirement for "uniform filtering" is satisfied by applying a **Low Count Gene Filter** (keep genes with count >= 10 in at least 3 samples) uniformly across the dataset before DESeq2 analysis. This ensures consistency and removes noise, satisfying the spirit of Principle VII for expression data.

## Traceability Map

| Requirement | Implementation Mechanism | Location |
| :--- | :--- | :--- |
| **FR-001** (NCBI Timeout) | `ingest.py` uses `requests` with `max_retries=3` and exponential backoff. Downloads from **PRJNA321023**. | `code/ingest.py` |
| **FR-002** (RAM Constraint) | Salmon runs with a specified memory limit parameter. and streaming mode. | `code/quantify.py` |
| **FR-003** (DGE) | DESeq2 `DESeqDataSetFromMatrix` with design `~ batch + condition` OR `~ temperature_celsius` if continuous. | `code/dge_analysis.R` |
| **FR-004** (FDR) | `p.adjust(method="BH")` in DESeq2 results. | `code/dge_analysis.R` |
| **FR-005** (Visualization) | `matplotlib` for Volcano; `gprofiler-official` for enrichment. | `code/viz.py`, `code/enrichment.py` |
| **FR-006** (Associational) | Hard-coded header in `results/report.md` stating "Observational Study". | `code/main.py` |

## Batch Effect & Gradient Mitigation

The dataset PRJNA321023 may contain samples processed in different batches or across a temperature gradient. To address construct validity:
1.  **Metadata Inspection**: Upon ingestion, the pipeline will parse the phenotype file.
    *   If `temperature_celsius` is present and continuous: The DESeq2 design will be set to `~ temperature_celsius`.
    *   If only `condition` (Heat/Control) is present: The design will be `~ batch + condition`.
2.  **Batch Check**: If batch metadata is missing, the pipeline will run `prcomp` on the variance-stabilized data. If the first principal component correlates strongly (r > 0.7) with the sequencing lane or date (if inferable), a warning will be logged, and the results will be flagged as "Potential Batch Confounding".

## Project Structure

### Documentation (this feature)

```text
specs/001-coral-resilience-prediction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── utils.py             # Logging, checksum, error handling
├── ingest.py            # NCBI download, FASTQ streaming
├── quantify.py          # Salmon wrapper (R or Python)
├── dge_analysis.R       # DESeq2 pipeline
├── viz.py               # Volcano plot generation
├── enrichment.py        # g:Profiler API wrapper
├── verify_citations.py  # Reference-Validator Agent logic
└── main.py              # Orchestration script

data/
├── raw/                 # Downloaded FASTQ, Phenotype CSV
├── processed/           # Quant.sf, Count matrix, DGE results
└── checksums.txt        # SHA256 logs

tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   └── test_utils.py
├── contract/
│   ├── __init__.py
│   └── test_schemas.py
└── integration/
    ├── __init__.py
    └── test_pipeline.py

results/
└── plots/               # Volcano plots, enrichment tables
```

**Structure Decision**: A single `code/` directory with modular scripts is selected to minimize overhead and fit the free-tier runner constraints. R is used specifically for DESeq2 as it is the standard for this analysis and available via Bioconductor, while Python handles I/O and orchestration.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dual Language (Python + R) | DESeq2 is native to R and lacks a robust, memory-efficient Python equivalent for this specific workflow. | Using a pure Python approximation (e.g., `scanpy`) would compromise statistical rigor required by FR-004 and SC-005. |
| Streaming I/O | FASTQ files can exceed RAM if loaded entirely into memory. | Loading full files into a Pandas DataFrame would likely trigger OOM errors on the 7GB runner. |
| No GWAS Tools | The study is RNA-seq, not GWAS. | Using `plink2` is irrelevant for expression data and would violate the data model. |

## Success Criteria (Refined)

- **SC-001**: Peak memory usage (RSS) < 7 GB.
- **SC-002**: Number of significant genes (FDR < 0.05, log2FC > 1.0) > expected count under null. *Refined: Success requires effect size > 1.0, not just p-value.*
- **SC-003**: Enrichment p-value for HSP/Oxidative pathways < 0.05 (FDR) AND gene count > 5. *Refined: Requires statistical significance and non-trivial effect size.*
- **SC-004**: Runtime < 6 hours.
- **SC-005**: FDR of reported hits <= 0.05.