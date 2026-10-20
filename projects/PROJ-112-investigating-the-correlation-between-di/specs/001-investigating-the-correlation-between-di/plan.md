# Implementation Plan: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

**Branch**: `001-gene-regulation` | **Date**: 2026-10-20 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The pipeline will (0) **download the American Gut Project (AGP) and UK Biobank (UKBB) 16S rRNA datasets** (or fall back to a user‑provided open dataset if UKBB is not publicly accessible), (1) ingest and harmonize these data, (2) clean covariates, (3) apply a Bayesian‑multiplicative replacement + centered log‑ratio (CLR) transformation, (4) run covariate‑adjusted Spearman partial correlations **with standard‑error (SE) via Fisher Z**, (5) run **MaAsLin2 on CLR‑transformed counts** (not raw counts) adjusting for age, BMI, sex, antibiotic use, and batch, (6) apply Benjamini‑Hochberg FDR correction, (7) produce a **single merged result file** (`results/association_combined.tsv`) that satisfies `correlation_result.schema.yaml`, (8) perform differential abundance testing with ANCOM‑II and DESeq2, (9) conduct cross‑cohort validation, (10) run a measurement‑error simulation using **synthetic data with known effect sizes**, (11) conduct **model‑appropriate power analyses** for both Spearman correlation and the MaAsLin2 linear model, and (12) generate reproducible summary tables and a markdown report. All steps are CPU‑only and fit within the GitHub Actions free‑tier limits.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**:  
  `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `biom-format`, `rpy2` (for R packages `Maaslin2`, `ANCOMII`, `DESeq2`, `zCompositions`), `datasets`, `pyyaml`
- **Storage**: Local filesystem under `data/` (raw, harmonized, analysis matrices) and `results/`
- **Testing**: `pytest` + schema validation (`contracts/` YAML)
- **Target Platform**: Linux GitHub Actions free tier (2 CPU, ~7 GB RAM, no GPU)
- **Constraints**: All R packages run on CPU via `rpy2`. Streaming loaders keep RAM < 5 GB. The main microbiome matrix is processed in chunked fashion to stay within available memory constraints. Expected wall‑time ≤ 5 h on the GitHub Actions free tier.  

## Constitution Check
| Principle | Compliance | Action / Note |
|-----------|------------|----------------|
| I. Reproducibility | ✅ PASS – deterministic scripts, pinned seeds, `requirements.txt` | All steps can be re‑run on a fresh runner. |
| II. Verified Accuracy | ✅ PASS – no external citations beyond verified‑datasets block. | Only URLs from the block are referenced. |
| III. Data Hygiene | ✅ PASS – raw files immutable, SHA‑256 checksums recorded, no PII. | Checksums stored in `state/projects/...yaml`. |
| IV. Single Source of Truth | ✅ PASS – every statistic traced to a row in `data/` and a line in `code/`. | Logging includes source identifiers. |
| V. Versioning Discipline | ✅ PASS – content hashes stored; `updated_at` managed automatically. | Handled by the platform. |
| VI. Compositional Data Analysis | ✅ PASS – CLR applied before correlation; MaAsLin2 receives CLR data; ANCOM‑II & DESeq2 used per assumptions. | Pseudocount added where needed. |
| VII. Cross‑Cohort Validation | ✅ PASS – replication required in both AGP and UKBB; if UKBB unavailable, pipeline runs with single‑cohort flag. | Implemented in Phase 9. |

## Project Structure
```text
specs/001-gene-regulation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── correlation_result.schema.yaml
│   └── diff_abundance.schema.yaml
└── tasks.md   # generated later
```

## Implementation Phases & FR/SC Mapping
| Phase | Tasks | FR(s) Addressed | SC(s) Addressed |
|-------|-------|-----------------|-----------------|
| **0 – Variable‑Fit & Cohort Availability** | - Verify that each downloaded cohort contains **all** required columns: `fiber_intake_g`, `age`, `bmi`, `sex`, `antibiotic_use`, `batch`, `read_depth`, and a taxon count matrix.<br>- If any required column is missing in a cohort, **exclude that cohort** and set `single_cohort=True`. | FR‑001, FR‑002 | SC‑006 |
| **1 – Data Ingestion** | - Implement **`src/ingestion/agp_loader.py`** to download AGP 16S tables & metadata via the public AGP URL, compute SHA‑256 checksums, and save raw files under `data/raw/agp/`.<br>- Implement **`src/ingestion/ukbb_loader.py`** to attempt download of the UKBB gut‑microbiome release via its open portal; if unavailable, log a warning and proceed with AGP only. Both scripts will raise a clear error if required columns are absent.<br>- Raw files are saved under `data/raw/` with checksums recorded. | FR‑001 | SC‑006 |
| **2 – Harmonization & QC** | - Convert any fiber units to g/day.<br>- Filter samples: `read_depth` ≥ 5 000 and `0 ≤ fiber_intake_g ≤ 200`. | FR‑001, FR‑002 | SC‑006 |
| **3 – Covariate Cleaning** | - Compute per‑sample missingness; drop samples with >20 % missing covariates (including `batch`).<br>- Median impute numeric covariates; mode impute categorical. | FR‑008 (via clean covariates) | SC‑001 |
| **4 – CLR Transformation** | - Apply Bayesian‑multiplicative replacement (`zCompositions`) with pseudocount = 1e‑6, then CLR to the taxon count matrix. | FR‑003, VI (Constitution) | SC‑001 |
| **5 – Association Analyses** | - **Partial Spearman**: Regress covariates from both `fiber_intake_g` and each CLR‑taxon, compute Spearman ρ on residuals, calculate SE via Fisher Z, and obtain raw p‑values.<br>- **MaAsLin2**: Run on **CLR‑transformed** counts with covariates `age`, `bmi`, `sex`, `antibiotic_use`, `batch`.<br>- Apply Benjamini‑Hochberg FDR separately for each method.<br>- **Merge** Spearman and MaAsLin2 outputs into `results/association_combined.tsv` (matches `correlation_result.schema.yaml`). | FR‑004, FR‑005, FR‑006 | SC‑001, SC‑002, SC‑003 |
| **6 – Differential Abundance** | - Define high/low fiber groups per cohort using the 75th/25th percentile of `fiber_intake_g`.<br>- Run **ANCOM‑II** on relative abundances.<br>- Run **DESeq2** on raw counts.<br>- Output TSVs with columns required by `diff_abundance.schema.yaml`. | FR‑007, FR‑009 | SC‑002, SC‑003 |
| **7 – Cross‑Cohort Validation** | - Flag a taxon as **replicated** only if (i) q < 0.05 in **both** cohorts **and** (ii) effect direction matches.<br>- Compute replication rate (% to two decimals). | FR‑008 | SC‑006 |
| **8 – Measurement‑Error Simulation** | - Generate synthetic data where the true β for fiber → taxa is set to 0.1.<br>- Add Gaussian noise (SD = 10 % of mean fiber) to the simulated fiber values.<br>- Re‑run both association methods on the noisy data.<br>- Report bias = (estimated − true)/true for each taxon; summarize median absolute bias. | FR‑010 | SC‑005 |
| **9 – Power Analyses** | - **A priori**: Document required N per cohort to detect β ≈ 0.1 with 80 % power at α = 0.05 **using methods that match the statistical tests**:<br> • For Spearman correlation on CLR‑transformed data, use `statsmodels.stats.power.NormalIndPower` (approximation for correlation testing).<br> • For the MaAsLin2 linear model, use `statsmodels.stats.power.FTestPower` (appropriate for multiple‑regression F‑tests).<br>- **Post‑hoc**: Compute achieved power for the smaller cohort using the same methods. If the smaller cohort fails the a priori requirement, emit **FR‑013** warning and halt downstream analyses (Phase 10 is skipped).<br>- **Note**: We explicitly avoid `TTestIndPower`, which assumes a two‑sample t‑test and would be mismatched to our primary analyses. | FR‑012, FR‑013 | SC‑004 |
| **10 – Summary & Reporting** | - Compute absolute median `fiber_intake_g` for high‑ and low‑fiber groups per cohort.<br>- Assemble tables of significant taxa (β, q, direction), differential‑abundance results, replication flags, measurement‑error bias, and power metrics.<br>- Generate `results/final_report.md` (markdown) and `results/replication_table.csv`. | FR‑008, FR‑009, FR‑011 | SC‑001, SC‑003, SC‑007 |
| **11 – Contract Validation** | - Run `pytest tests/contract/` against the three JSON‑Schema contracts. | All FRs (output conformity) | All SCs (output correctness) |

## Edge‑Case Handling (explicit in spec)
- **Zero‑inflated taxa** → Bayesian replacement before CLR (pseudocount = 1e‑6).  
- **Missing covariates** → Exclude samples >20 % missing; median/mode impute remainder.  
- **Sample‑size disparity** → Report in summary; if the smaller cohort fails the a priori sample‑size target, the pipeline stops with a clear warning (FR‑013).  

## Compute Feasibility
All R packages run on CPU via `rpy2`. Streaming loaders (`datasets.load_dataset(..., streaming=True)`) are used only for optional helper datasets and keep RAM < 5 GB. The main microbiome matrix is processed in chunked fashion to stay under the 7 GB RAM limit. Expected wall‑time ≤ 5 h on the GitHub Actions free tier.  

---



