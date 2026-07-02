# Implementation Plan: Quantifying the Impact of Transposable Element Activity on Gene Expression Variation in Drosophila

**Branch**: `001-gene-regulation` | **Date**: 2024-01-15 | **Spec**: `specs/001-quantifying-the-impact-of-transposable-e/spec.md`

## Summary

This project implements a reproducible pipeline to quantify the association between Transposable Element (TE) presence and gene expression variation in *Drosophila* using the Drosophila Genetic Reference Panel (DGRP). The technical approach involves downloading genotype and expression data, performing TE‑aware quantification, defining proximal TE‑gene pairs, controlling for population structure via Principal Component Analysis (PCA), and fitting linear models with Benjamini–Hochberg correction. The plan explicitly addresses the requirement for TE‑aware quantification (Constitution Principle VII), robust permutation testing (Freedman‑Lane residual shuffling) to satisfy SC compliance, power‑analysis filtering, and clear output artifacts for SC requirements. All steps are designed to run on a free‑tier GitHub Actions runner (2 CPU, ~7 GB RAM, ≤6 h).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pybedtools`, `requests`, `pyyaml`, `matplotlib`, `seaborn`, `scipy`  
**Storage**: Local CSV/VCF/TSV files under `data/`; no external database.  
**Testing**: `pytest` with unit tests for data parsing, model fitting, and contract validation.  
**Target Platform**: Linux (GitHub Actions free‑tier: 2 CPU, ~7 GB RAM).  
**Constraints**: No GPU, memory < 6 GB, all libraries CPU‑only.  
**Scale/Scope**: Sample subset of 50 DGRP lines, ~5 000 TE‑gene pairs (mock data for CI).  

> **Note on Data**: No verified public URL currently provides a DGRP VCF with TE calls *and* matched TE‑aware RNA‑seq quantifications. The pipeline therefore includes a **Mock Mode** for CI testing (synthetic data adhering to `dataset.schema.yaml`). When real data become available, users can point `config.yaml` to the appropriate files and the same pipeline will run without modification.

## Constitution Check

| Principle | Status | Verification Logic |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `random_seed` pinned in `config.yaml`; all downloads checksum‑verified; deterministic pipelines. |
| **II. Verified Accuracy** | **PASS** | `validate_citations.py` checks any external URLs against the verified list; no new URLs invented. |
| **III. Data Hygiene** | **PASS** | Raw → processed → derived folders; `checksums.json` records SHA‑256 for every file; no in‑place edits. |
| **IV. Single Source of Truth** | **PASS** | All statistics written to `results/associations.csv`; paper generation reads only this file. |
| **V. Versioning Discipline** | **PASS** | Content hashes stored in `state.yaml`; any change updates `updated_at`. |
| **VI. Population‑Structure Control** | **PASS** | PCA on genome‑wide SNPs (Task T007) and inclusion of PC1‑PC3 in the linear model (Task T011). |
| **VII. TE‑Aware Quantification** | **PASS** | **Task T006** runs TEtranscripts (or mock equivalent) and validates `quantification_method == "TEaware"` before downstream analysis. |

## Project Structure

```text
src/
├── __init__.py
├── config.py                # Loads config.yaml, sets seeds
├── data_loader.py           # Fetches VCF/FASTQ, generates mock data, checksums
├── preprocessing.py         # PCA, TE‑gene pairing, monomorphic & power filters
├── quantification.py        # TE‑aware expression quantification (TEtranscripts)
├── association.py           # Linear models, VIF, BH correction, R² metrics
├── permutation.py           # Freedman‑Lane residual shuffling
├── replication.py           # Independent dataset validation
├── visualization.py         # Null‑distribution plot, R² reduction plot
├── utils.py                 # Logging, checksumming, error handling
└── cli.py                   # Entry point, orchestrates tasks
tests/
├── test_preprocessing.py
├── test_association.py
├── test_permutation.py
├── test_contracts.py        # Validates outputs against schemas
└── conftest.py              # Fixtures for mock data
data/
├── raw/                     # Downloaded VCFs, FASTQs, GTFs (or mock)
├── processed/               # PCA matrix, TE‑gene pairs, filtered genotypes
└── derived/                 # Association results, plots, metrics
config.yaml                    # Project configuration (seeds, paths, thresholds)
requirements.txt               # Pinned dependencies
```

## Implementation Phases & Tasks

### Phase 0: Research & Data Strategy
* **T001** – Survey public repositories (FlyBase, SRA, modENCODE) for DGRP TE‑genotype + TE‑aware expression data; document gaps.  
* **T002** – Design mock data generator schema matching `dataset.schema.yaml`.

### Phase 1: Data Loading & Preprocessing
| Task ID | Description | Output / Artifact |
|---|---|---|
| **T003** | `data_loader.py` – download VCF, FASTQ, GTF; fallback to mock generator if unavailable. | `data/raw/` |
| **T004** | Compute SHA‑256 checksums for every raw file; write `checksums.json`. | `data/checksums.json` |
| **T005** | `preprocessing.py` – compute genome‑wide SNP PCA (PC1‑PC3). | `data/processed/pca.csv` |
| **T006** | **TE‑Aware Quantification** – run TEtranscripts (or mock) on FASTQ to produce `gene_TE_expression.tsv`; verify `quantification_method == "TEaware"` in metadata. | `data/processed/expression_TEaware.tsv` |
| **T007** | Define proximal TE‑gene pairs (≤5 kb upstream/downstream) using Release 6 GTF. | `data/processed/te_gene_pairs.tsv` |
| **T008** | Flag ambiguous pairs (TE within 5 kb of >1 gene) → `ambiguous_flag`. | column in `te_gene_pairs.tsv` |
| **T009** | Exclude monomorphic TEs (frequency < 5 % or > 95 %). | filtered genotype matrix |
| **T010** | **Power Filter** – compute Minor Allele Count (MAC); enforce `MAF ≥ 0.10` (≥5 carriers in 50 lines). Flag pairs with `mac < 5` as `power_flag`. | `mac` column in genotype table |
| **T011** | Assemble final analysis dataset (expression, genotype, PCs) for each retained pair. | `data/processed/analysis_input.tsv` |

### Phase 2: Association & Robustness
| Task ID | Description | Output |
|---|---|---|
| **T012** | Fit linear model `gene_expression ~ TE_presence + PC1 + PC2 + PC3` (OLS). Compute effect size, 95 % CI, p‑value. | `results/temp/model_coeffs.tsv` |
| **T013** | Compute VIF for TE vs. PCs; set `vif_flag` if VIF > 5. | `vif.tsv` |
| **T014** | Apply Benjamini–Hochberg correction across **all** tested pairs (including ambiguous). | `results/temp/bh_adjusted.tsv` |
| **T015** | **Freedman‑Lane Permutation** (100 iters): residual shuffling of reduced model (Y ~ PCs) → null t‑stat distribution. | `results/permutation/null_t_stats.tsv` |
| **T016** | Generate null‑distribution plot with observed t‑stat vertical line and a significance threshold. | `results/plots/null_distribution.png` |
| **T017** | Compute R² with PCs and without PCs; calculate reduction metric. | `results/population_structure_control.csv` |
| **T018** | Assemble final association table (including `vif_flag`, `ambiguous_flag`, `mac`, `null_statistic_95th`). | `results/associations.csv` |
| **T019** | **Rare‑Variant Burden Analysis** (optional): aggregate rare TE insertions per gene and test via burden regression. | `results/burden_analysis.tsv` |

### Phase 3: Replication & Reporting
| Task ID | Description | Output |
|---|---|---|
| **T020** | Load independent expression dataset (if provided) and run association using the same TE‑gene pairs. | `results/replication/raw.tsv` |
| **T021** | Compare primary and replication effect sizes; compute direction concordance and replication p‑values. | `results/replication/comparison.tsv` |
| **T022** | Summarize replication metrics (total tested, concordant count, concordance rate). | `results/replication_summary.csv` |
| **T023** | Validate all outputs against `contracts/*.schema.yaml`. | CI test pass/fail |
| **T024** | Generate final report (markdown) linking all tables and figures. | `docs/report.md` |

## Task Dependency & Ordering

1. **Download** → **Checksum** → **PCA** → **TE‑aware Quantification** → **Pair Definition** → **Monomorphic & Power Filters** → **Analysis Input**  
2. **Linear Model** → **VIF** → **BH Correction** → **Permutation** → **Null Plot** → **R² Metric** → **Final Association Table**  
3. **Replication** → **Comparison** → **Summary** → **Validation** → **Report**

All data‑generation tasks precede any analysis that consumes their outputs, satisfying the required computational ordering.

## Success Metric Generation (SC‑004 & SC‑005)

* **SC‑004** – `results/population_structure_control.csv` contains `r_squared_with_pcs`, `r_squared_without_pcs`, and `reduction`.  
* **SC‑005** – `results/plots/null_distribution.png` shows the full null histogram, a vertical line for the observed t‑statistic, and a highlighted 95th‑percentile threshold line.

## Edge‑Case Handling

* **Monomorphic TEs** – filtered out (FR‑008).  
* **Rare TEs (MAF < 10 %)** – excluded from primary OLS analysis; optional burden test (Task T019) captures them.  
* **Zero/near‑zero expression** – log2(TPM + 1) transformation applied; values < 0.001 become 0 after transformation, OLS handles them.  
* **Ambiguous TE‑gene proximity** – flagged (`ambiguous_flag`) and retained; downstream reporting includes the flag.  
* **Missing expression for a line** – that line is omitted from the specific gene's regression (FR‑009).  
* **High collinearity (VIF > 5)** – flagged (`vif_flag`) and reported; no causal claim is made (FR‑007).

## Optional Extensions (Future Work)

* Mixed‑model implementation (e.g., EMMAX/REML) for improved LD control – discussed in research.md.  
* Integration with real DGRP TE‑genotype + TE‑aware RNA‑seq datasets when they become publicly available.