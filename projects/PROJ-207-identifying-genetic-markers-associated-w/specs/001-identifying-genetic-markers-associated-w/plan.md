# Implementation Plan: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

**Branch**: `001-gene-regulation` | **Date**: 2024-01-15 | **Spec**: `specs/001-identifying-genetic-markers-associated-w/spec.md`
**Input**: Feature specification from `/specs/001-identifying-genetic-markers-associated-w/spec.md`

## Summary

This project implements a CPU-tractable GWAS pipeline to identify SNPs associated with Honeybee Colony Collapse Disorder (CCD) using *Apis mellifera* genomic data. The pipeline downloads **verified real data** from Hugging Face (derived from NCBI BioProject PRJNA639195/566029), aligns reads to `Amel_HAv3.1`, calls variants with FreeBayes, and performs logistic regression in PLINK. It applies Benjamini-Hochberg FDR correction, conducts threshold sensitivity analysis, and validates findings via LASSO logistic regression on a **held-out validation set**. 

**Critical Methodological Adjustment**: Given the sample size (n=120), the study is framed as **Candidate-Gene Exploratory**. The pipeline pre-filters SNPs to a known immune pathway (reducing the multiple testing burden to a manageable subset) to ensure statistical power for detecting large effect sizes (OR ≥ 2.5). All methods are designed to run within GitHub Actions free-tier limits (CPU, sufficient RAM, and the available time window).

## Technical Context

**Language/Version**: Python 3.11, Bash 5.0  
**Primary Dependencies**: `plink2`, `bwa`, `freebayes`, `scikit-learn`, `pandas`, `statsmodels`, `pyyaml`, `datasets`  
**Storage**: Local filesystem (`data/`), no external DB  
**Testing**: `pytest` (unit), `bash` (integration)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational biology pipeline / CLI  
**Performance Goals**: < 6h runtime, < 7 GB RAM peak  
**Constraints**: No GPU; CPU-first; observational study framing; real data only for scientific results.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Evidence / Action |
|-----------|-------------------|-------------------|
| I. Reproducibility | ✅ PASS | Random seeds pinned in `code/`; data fetched from verified HF URL with version pinning; `requirements.txt` pins versions. |
| II. Verified Accuracy | ⚠️ PARTIAL | External citations (HF dataset) are verified. Status passes only after real data fetch and checksum validation succeeds in Phase 1. |
| III. Data Hygiene | ✅ PASS | Checksums recorded in `state/`; raw data preserved; derivations written to new files. |
| IV. Single Source of Truth | ✅ PASS | All stats trace to `data/` rows and `code/` blocks; no hand-typed numbers. |
| V. Versioning Discipline | ✅ PASS | Content hashes tracked; `updated_at` timestamp on state file. |
| VI. Genomic Pipeline Standardization | ✅ PASS | Uses `bwa mem`, `FreeBayes`, `PLINK`; intermediate VCF/PLINK files archived. Validated on real data subset. |
| VII. Phenotype Covariate Control | ✅ PASS | Models explicitly include region, year, Varroa; results without these are invalid. Mediator bias analysis included. |

## Project Structure

### Documentation (this feature)

```text
specs/001-identifying-genetic-markers-associated-w/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-207-identifying-genetic-markers-associated-w/
├── code/
│   ├── 01_download_data.sh          # Fetches real HF dataset with SSL validation
│   ├── 02_harmonize_phenotypes.py   # Maps CCD criteria, handles missing Varroa
│   ├── 03_align_and_call.sh         # bwa mem + FreeBayes
│   ├── 04_filter_snps.py            # Pre-filters to immune pathway (Candidate-Gene)
│   ├── 05_collinearity_diag.py      # VIF/Correlation check
│   ├── 06_power_analysis.py         # Power calc with corrected alpha; halts if insufficient
│   ├── 07_gwas_plink.sh             # Logistic regression
│   ├── 08_apply_fdr.py              # BH FDR correction
│   ├── 09_threshold_sensitivity.py  # Sweep p-values
│   ├── 10_lasso_validation.py       # Hold-out validation (80/20 split)
│   ├── 11_prs_and_lr_test.py        # PRS + Likelihood-ratio test
│   ├── 12_annotate_genes.py         # Ensembl Bees API
│   └── 13_format_results.py         # Adds associational disclaimer
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
└── requirements.txt
```

**Structure Decision**: Single-project structure chosen to minimize overhead and align with GitHub Actions free-tier constraints. All scripts are modular and depend on explicit file paths in `data/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Candidate-Gene Pre-filtering | Required to make n=120 statistically valid for GWAS. Full GWAS is underpowered. | Full GWAS would yield null results due to multiple testing burden. |
| Mediator Bias Analysis | Required to address Varroa as a potential mediator. | Standard adjustment would obscure genetic signals. |

## Phase Breakdown

### Phase 0: Real Data Validation & Setup
- **Goal**: Verify real data fetch and pipeline integrity.
- **Tasks**:
  - Fetch verified Hugging Face dataset (`bee_genome_variants`) with SSL validation.
  - Validate dataset checksums and schema.
  - Run pipeline on a small subset (n=10) to confirm toolchain (bwa, FreeBayes, PLINK) works.
  - **Output**: `data/raw/verified_dataset_info.json`.

### Phase 1: Data Preprocessing & Harmonization
- **Goal**: Prepare data for analysis.
- **Tasks**:
  - **FR-001**: Download data from HF (SSL validated).
  - **FR-011**: Harmonize CCD diagnosis codes to CCD Working Group criteria.
  - **FR-011**: Check Varroa data coverage (≥90%). Halt if <80%.
  - **FR-012**: Run power analysis with corrected alpha. Halt if n < 80 or power < 0.8.
  - **FR-003**: Convert VCF to PLINK format.
  - **FR-003**: Pre-filter SNPs to immune pathway (Candidate-Gene approach).
  - **Output**: `data/interim/phenotypes_cleaned.fam`, `data/interim/snp_filtered.bim`.

### Phase 2: Collinearity & GWAS
- **Goal**: Run association analysis.
- **Tasks**:
  - **FR-010**: Run collinearity diagnostics (VIF). Flag r² > 0.8.
  - **FR-004**: Run PLINK logistic regression with covariates.
  - **FR-004**: Apply Benjamini-Hochberg FDR correction.
  - **Output**: `data/processed/gwas_results_fdr.tsv`.

### Phase 3: Sensitivity & Validation
- **Goal**: Robustness and predictive utility.
- **Tasks**:
  - **FR-005**: Threshold sensitivity sweep across a range of decreasing magnitudes.
 - **FR-006**: LASSO logistic regression on **held-out validation set** ([deferred] split).
  - **FR-007**: Compute PRS and likelihood-ratio test.
  - **FR-008**: Map SNPs to genes (Ensembl Bees).
  - **FR-009**: Generate results with explicit associational disclaimer.
  - **Output**: `data/processed/validation_metrics.json`, `data/processed/final_report.md`.
