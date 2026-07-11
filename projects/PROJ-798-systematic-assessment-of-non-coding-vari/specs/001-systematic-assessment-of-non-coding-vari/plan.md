# Implementation Plan: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

**Branch**: `001-gene-regulation` | **Date**: 2026-07-10 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-systematic-assessment-of-non-coding-vari/spec.md`

## Summary

This project implements a computational pipeline to assess the impact of non-coding Single Nucleotide Polymorphisms (SNPs) on Transcription Factor (TF) binding. The system ingests common human SNPs (MAF > 1%) from **dbSNP Common**, filters them to regulatory regions (promoters/enhancers), calculates allele-specific binding affinity changes ($\Delta Score$) using JASPAR 2024 Position Weight Matrices (PWMs) with **dynamic windowing** (PWM length), and performs statistical enrichment analysis against GWAS Catalog loci. 

The pipeline uses a **two-part null model**: 
1. **Label Permutation** (swapping Ref/Alt alleles) to test the *directionality* of effects while preserving exact genomic sequence context (GC content). This replaces position shuffling to avoid confounding sequence composition.
2. **GWAS Label Permutation** (shuffling GWAS status among SNPs with similar scores) to test the *enrichment of magnitude* while preserving the score distribution.
3. **Matched Null Cohort** generation to control for local sequence composition bias (k-mer frequency, GC content) in the background.

The enrichment test uses the **full distribution** of $\Delta Scores$ via a Kolmogorov-Smirnov (KS) test, eliminating selection bias from arbitrary "top-k" cutoffs. The pipeline is designed to run entirely on CPU within the constraints of a free-tier GitHub Actions runner (limited CPU, 7 GB RAM, 6 hours) via **batched processing** and a **two-stage permutation** strategy (100 permutations for screening, 1000 for candidates).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `biopython`, `pybedtools` (via `bedtools` binary), `scipy`, `requests`, `pyyaml`, `tqdm`, `statsmodels`  
**Storage**: Local filesystem (`data/raw`, `data/derived`, `data/interim`), Parquet/CSV formats  
**Testing**: `pytest` (unit and integration tests against synthetic data)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: CLI/Scientific Pipeline  
**Performance Goals**: Complete full analysis within 6 hours; memory usage < 7 GB.  
**Constraints**: No GPU; strict adherence to CPU-only libraries; no large-model training; dataset sampling required if raw sizes exceed RAM.  
**Scale/Scope**: [deferred] common SNPs (source: dbSNP Common release, filtered to Chromosomes 1-22, MAF > 1%) to fit runtime constraints.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (Principle I)**: All random seeds are pinned in `code/config.py`. External datasets are fetched from canonical sources (NCBI dbSNP FTP, JASPAR, ENCODE) with MD5 checksums recorded in `data/manifest.json`.
2.  **Verified Accuracy (Principle II)**: All citations (dbSNP, JASPAR, ENCODE, GWAS) are validated against primary sources via specific FTP paths and checksums. The plan explicitly avoids inventing URLs; where verified sources are missing, the implementation uses standard programmatic loaders or documented FTP paths with checksum verification.
3.  **Data Hygiene (Principle III)**: Raw data is downloaded once, checksummed, and never modified. Derived files (filtered SNPs, scores) have new filenames and derivation logs.
4.  **Single Source of Truth (Principle IV)**: Final statistics and figures are generated directly from `data/derived` artifacts by `code/` scripts, not hand-typed.
5.  **Versioning Discipline (Principle V)**: Artifacts carry content hashes. The `state` file is updated on artifact changes.
6.  **Biophysical Proxy Validity (Principle VI)**: The plan strictly uses PWM-based log-odds scoring (JASPAR) as the proxy for affinity, avoiding deep learning models to maintain the "phenomenon" focus.
7.  **Population-Genetic Independence (Principle VII)**: The pipeline ensures that the input SNPs (dbSNP) and the GWAS enrichment targets are independent of the motif scoring calculation. **Specifically**, the 'Label Permutation' and 'GWAS Label Permutation' null models ensure that the scoring phase (which uses sequence context) does not leak GWAS signals, and the enrichment phase uses a null that preserves the score distribution while breaking the GWAS association.

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── snp_schema.schema.yaml
    ├── pwm_schema.schema.yaml
    ├── score_schema.schema.yaml
    └── result_schema.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Entry point for CLI
├── config.py            # Configuration and paths
├── data/
│   ├── __init__.py
│   ├── downloaders.py   # Scripts for FTP/API downloads
│   ├── preprocess.py    # Filtering and cleaning
│   └── loaders.py       # Loading JASPAR/BED files
├── analysis/
│   ├── __init__.py
│   ├── scorer.py        # PWM scoring logic
│   ├── permutations.py  # Null distribution generation (Label & GWAS)
│   └── enrichment.py    # GWAS overlap and FDR
├── utils/
│   ├── __init__.py
│   └── io.py            # Parquet/CSV handling
└── tests/
    ├── __init__.py
    ├── test_scorer.py
    ├── test_enrichment.py
    └── test_data_hygiene.py
```

**Structure Decision**: A modular CLI structure (`code/`) is selected to separate data ingestion, analysis logic, and testing. This ensures reproducibility (Principle I) and allows independent unit testing of the scoring engine (US-2) before running the full pipeline.

## Complexity Tracking

| Complexity | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Label Permutation Null | Position shuffling confounds GC content and local sequence context. Label permutation (Ref/Alt swap) preserves the exact genomic context while breaking the allele-score association, validly testing the hypothesis. | Position shuffling would introduce false positives due to sequence bias. |
| Two-Stage Permutation | A large number of iterations (1000 TFs * 1000 perms) exceeds 6h runtime on 2-CPU. | A single-stage 1000-perm test for all TFs is infeasible. Two-stage permutation testing (a lower number for screening, a higher number for candidates) reduces load while maintaining power. |
| Batched Processing | The full dbSNP Common set (millions of variants) exceeds 7GB RAM. | Processing all SNPs at once causes OOM. Batching (Chromosome 1-22) is required to fit the free-tier runner's memory limit. |
| West-Stephens FDR | FR-006 requires accounting for dependence between correlated TF motifs. | Standard Benjamini-Hochberg assumes independence, invalid for overlapping TF binding sites. |
| Matched Null Cohort | Controls for local sequence composition bias (GC content, k-mer frequency) which confounds PWM scores and GWAS enrichment. | Random shuffling or simple background models fail to account for these biases, leading to spurious correlations. |

## Tasks

### US-1: Data Ingestion and Regulatory Context Filtering

- **T001**: Initialize project structure and `config.py`. [S]
- **T002**: Define `snp_schema.schema.yaml` and `pwm_schema.schema.yaml` contracts. [S]
- **T003**: **Deviation Approval**: Document and validate the deviation from FR-002 (fixed ±10bp) to "Dynamic Window" (PWM length) based on mathematical validity of log-odds scores. [S]
- **T003b**: **Verification Task**: Run a pilot test on a small subset of PWMs to verify that Dynamic Window logic produces valid log-odds scores (matches manual calculation). [S]
- **T004**: **Compute Feasibility Check**: Calculate estimated runtime for Two-Stage Permutation (100 + 1000) on [deferred] SNPs and 1000 TFs. If > 6h, activate "Analytical Approximation" fallback. [S]
- **T010**: Download **dbSNP Common** (GRCh38) VCFs for Chromosomes 1-22. Filter for MAF > 1%, Quality Score > 20, and canonical alleles (A/C/G/T). *Source: `ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b151_GRCh38p13/VCF/00-Common/`*. [P]
- **T010b**: Download **JASPAR 2024** PWMs. *Source: `jaspar2024` package or `jaspar.genereg.net`*. [P]
- **T011**: Download ENCODE BED files: `wgEncodeRegTssV4` (promoters) and `wgEncodeRegEnhancerV4` (enhancers). *Source: ENCODE Portal (`https://www.encodeproject.org/search/?type=regulatory_region&file_type=bed`)*. [P]
- **T012**: Generate **Non-Regulatory Baseline** cohort: SNPs matched for MAF and distance to TSS but located >5kb from any regulatory element. [S]
- **T012b**: Generate **Matched Null Cohort**: SNPs matched for local k-mer frequency and GC content to the regulatory SNPs, used as a sequence-composition-matched background. [S]
- **T013**: Intersect SNPs (T010) with Regulatory Regions (T011) and Baseline (T012) using `bedtools intersect`. [S]
- **T014**: Output `filtered_snps.parquet` conforming to `specs/001-systematic-assessment-of-non-coding-vari/contracts/snp_schema.schema.yaml`. [S]

### US-2: Allele-Specific Binding Affinity Scoring

- **T017**: Load JASPAR CORE Human PWMs from T010b. Parse as PWM objects. [S] (Depends on T010b)
- **T018**: Extract sequence context for each SNP. **Dynamic Window**: Window size = PWM length (L), centered on variant. (Approved deviation in T003). [S] (Depends on T014, T017)
- **T018b**: Verify that Dynamic Window logic produces valid log-odds scores for all PWMs. [S]
- **T019**: Calculate $\Delta Score = Score_{alt} - Score_{ref}$ for each SNP-TF pair. **No arbitrary threshold filtering** (full distribution used). [S]
- **T019b**: **Biological Significance Filter**: Filter SNPs with $|\Delta Score| < 1.0$ bits (configurable) to remove biologically irrelevant noise. [S]
- **T020**: Output `scores.parquet` conforming to `score_schema.schema.yaml`. [S]

### US-3: Statistical Enrichment and GWAS Overlap Analysis

- **T025**: **Permutation Test (Label)**: For each TF, generate null distribution by **swapping Ref/Alt labels** (100 permutations) to test directionality. [P]
- **T026**: Identify candidate TFs with p < 0.1 in Stage 1. [S]
- **T027**: Download GWAS Catalog lead SNPs. *Source: `https://www.ebi.ac.uk/gwas/api/`*. [S]
- **T028**: **Permutation Test (GWAS Label)**: For candidate TFs, generate null distribution with 1000 permutations by **shuffling GWAS status** among SNPs with similar scores to test magnitude enrichment. [S]
- **T029**: **Threshold Validation**: Apply α = 0.05 corrected threshold to FDR-adjusted p-values. Record significance. [S]
- **T029c**: **FDR Verification**: Run a pilot on synthetic correlated data to verify that 'Simultaneous Label Permutation' + West-Stephens controls FDR at 0.05. [S]
- **T030**: Calculate enrichment ratio (Observed vs Expected) using the full distribution KS-test against the **Matched Null Cohort** (T012b). [S]
- **T030c**: **Threshold Validation Step**: Explicitly apply the 0.05 threshold as a distinct validation step to satisfy SC-002. [S]
- **T031**: Output `enrichment_results.csv` conforming to `result_schema.schema.yaml`. [S]

