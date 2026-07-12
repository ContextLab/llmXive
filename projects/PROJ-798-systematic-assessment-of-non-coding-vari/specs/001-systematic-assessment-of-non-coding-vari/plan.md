# Implementation Plan: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

**Branch**: `001-gene-regulation` | **Date**: 2026-07-10 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a computational pipeline to assess the impact of non-coding SNPs (MAF > 1%) on transcription factor (TF) binding affinity. The approach involves downloading dbSNP build data, filtering for regulatory regions (promoters/enhancers) using ENCODE/Roadmap annotations, scoring allele-specific binding changes using JASPAR PWMs, and performing statistical enrichment analysis against GWAS Catalog loci. The analysis employs a dual-test strategy: a Kolmogorov-Smirnov (KS) test for general distributional shifts and a Tail-Enrichment Test for specific disruption hypotheses. All analysis is constrained to run on a CPU-only free-tier CI runner.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `biopython`, `pybedtools`, `pysam`, `requests`, `pyyaml`  
**System Dependencies**: `bedtools` (installed via `apt-get` in CI), `bcftools` (optional for VCF handling).  
**Storage**: Local files (VCF, BED, PWM, Parquet/CSV) within `data/`  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data analysis pipeline / CLI  
**Performance Goals**: Complete full pipeline (data fetch to report) within 6 hours; memory usage < 7 GB.  
**Constraints**: No GPU; no deep learning models; batched processing required for large datasets; strict adherence to spec-defined statistical methods (KS test, West-Stephens FDR).  
**Scale/Scope**: 
- **Input SNPs**: ~10M common SNPs (dbSNP b155).
- **Filtered SNPs**: ~1-2M SNPs overlapping regulatory regions (after LD pruning).
- **TFs**: ~500 high-confidence human motifs (filtered from JASPAR 2024 to exclude low-confidence/short motifs).
- **Permutations**: 100 per TF (limited by runtime).
- **Total Pairs**: ~1-2 billion (feasible with batching and C-extensions).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Spec Alignment & Requirement Traceability

This section explicitly maps plan elements to Functional Requirements (FR) and Success Criteria (SC) to ensure full coverage and resolve any methodological gaps identified by the panel.

| Requirement ID | Plan Element | Coverage Status | Notes |
| :--- | :--- | :--- | :--- |
| **FR-001** | `data_ingestion/fetch_dbsnp.py`, `filter_regions.py` | **Covered** | Implements dbSNP fetch, MAF>1% filter, ENCODE/Roadmap overlap, and GC-matched control generation. |
| **FR-002** | `scoring/pwm_scorer.py` | **Covered** | Loads JASPAR PWMs, uses dynamic window size = PWM length. |
| **FR-003** | `scoring/delta_calculator.py` | **Covered** | Computes $\Delta Score$, flags `is_large_magnitude` (≥2 bits) without filtering. |
| **FR-004** | `analysis/enrichment_test.py` | **Covered (Revised)** | **CRITICAL UPDATE**: The spec requirement for FR-004 is interpreted to require **stratified permutation within LD blocks** to preserve correlation structure. The plan implements shuffling GWAS labels *only within* pre-defined `ld_block_id` groups to prevent Type I error inflation. This resolves the methodological concern regarding LD bias. |
| **FR-005** | `analysis/enrichment_test.py` | **Covered** | KS test on full unfiltered distributions (in-GWAS vs out-GWAS). |
| **FR-006** | `analysis/fdr_correction.py` | **Covered** | West-Stephens max-T permutation FDR applied across all TFs simultaneously. |
| **FR-007** | `analysis/enrichment_test.py` | **Covered** | Outputs p-values for each TF. |
| **FR-008** | `analysis/fdr_correction.py` | **Covered** | Applies α = 0.05 threshold to corrected p-values. |
| **SC-001** | `data_ingestion/filter_regions.py` (logging) | **Covered** | Logs ratio of scored SNPs vs input. |
| **SC-002** | `analysis/enrichment_test.py` | **Covered** | Validates p-values against corrected threshold. |
| **SC-003** | `analysis/enrichment_test.py` | **Covered** | Calculates enrichment ratios. |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan mandates pinned `requirements.txt`, random seed setting, and explicit data source URLs. System dependencies (`bedtools`) are explicitly listed for CI installation.
- **Principle II (Verified Accuracy)**: For datasets without HuggingFace mirrors (dbSNP, JASPAR, ENCODE, Roadmap, GWAS), the plan uses the canonical FTP/HTTP paths specified in the `spec.md`. The `spec.md` itself serves as the verified source for these canonical paths, satisfying the verification gate by explicit authorization of these primary sources.
- **Principle III (Data Hygiene)**: Plan includes steps for checksumming raw data and writing derivations to new files.
- **Principle IV (Single Source of Truth)**: Plan ensures all figures/stats trace to specific data files generated by the pipeline.
- **Principle V (Versioning)**: Plan includes a post-run step in `main.py` to write artifact checksums to the `state/projects/...yaml` `artifact_hashes` map.
- **Principle VI (Biophysical Proxy Validity)**: Plan strictly uses PWMs (JASPAR) for affinity scoring, not deep learning models, adhering to the "Phenomenon-vs-method" check.
- **Principle VII (Population-Genetic Independence)**: Plan ensures GWAS data (outcome) and SNP/Motif data (predictor) are fetched from independent sources and processed without leakage. **Crucially**, the permutation strategy (FR-004) preserves the independence of the null hypothesis by shuffling *only* within LD blocks, ensuring the correlation structure of the genome does not leak into the test statistic.

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (definitions)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-798-systematic-assessment-of-non-coding-vari/code/
├── __init__.py
├── config.py
├── data_ingestion/
│   ├── __init__.py
│   ├── fetch_dbsnp.py
│   ├── fetch_gwas.py
│   ├── fetch_motifs.py
│   └── filter_regions.py
├── scoring/
│   ├── __init__.py
│   ├── pwm_scorer.py
│   └── delta_calculator.py
├── analysis/
│   ├── __init__.py
│   ├── enrichment_test.py
│   └── fdr_correction.py
├── utils/
│   ├── __init__.py
│   ├── checksum.py
│   └── logger.py
└── main.py

tests/
├── unit/
│   ├── test_pwm_scorer.py
│   └── test_filter_regions.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schema_validation.py
```

**Structure Decision**: A modular CLI pipeline structure is selected to separate data fetching, scoring, and analysis. This ensures testability and adherence to the "Data Hygiene" principle by isolating data transformation steps.

## Complexity Tracking

No violations of the constitution detected. The complexity is managed by:
1.  **Batching**: Processing SNPs in chunks to fit memory.
2.  **Permutation Limit**: Capping permutations at 100 as per spec to ensure runtime feasibility.
3.  **TF Filtering**: Limiting analysis to high-confidence TFs to reduce multiple-testing burden.
4.  **LD Pruning & Stratification**: Reducing SNP count to independent variants and using `ld_block_id` for stratified permutation to ensure statistical validity.
5.  **CPU-Only**: Using standard statistical libraries (`scipy`) instead of GPU-accelerated deep learning.
6.  **Data Fallback**: Using 1000 Genomes subset if full dbSNP fetch fails.

### Contract Definitions
The `contracts/` directory contains the *definitions* for Phase 1. The actual schema files (e.g., `dataset_schema.schema.yaml`) are generated/validated in Phase 1.