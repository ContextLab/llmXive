# Implementation Plan: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

**Branch**: `001-gene-regulation` | **Date**: 2026-10-20 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The pipeline will (1) download 16S rRNA amplicon tables and associated metadata for the American Gut Project (AGP) and UK Biobank (UKBB) **or** a user‑provided open dataset that contains the required variables, (2) harmonize units, filter implausible values and low‑depth samples, (3) clean covariates (including sequencing batch), (4) apply a Bayesian‑multiplicative replacement **only** for Spearman correlation (CLR transformation), (5) compute associations between fiber intake and each taxon using (a) Spearman ρ on CLR‑transformed abundances and (b) MaAsLin2 on **raw counts** adjusting for age, BMI, sex, antibiotic use **and batch**, (6) apply Benjamini‑Hochberg FDR correction across taxa, (7) perform differential abundance testing with ANCOM‑II (relative abundances) and DESeq2 (raw counts) on high‑ vs low‑fiber groups, (8) conduct a **post‑hoc power analysis** for the smaller cohort and a categorical‑fiber sensitivity analysis, (9) evaluate replication across cohorts, (10) generate summary tables and a final report. All steps are reproducible, CPU‑only, and respect the project constitution.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `biom-format`, `rpy2` (for MaAsLin2, ANCOM‑II, DESeq2, `zCompositions`), `datasets` (Hugging Face), `pyyaml`
- **Storage**: Local filesystem under `data/` (raw, harmonized, analysis matrices) and `results/`
- **Testing**: `pytest` + schema validation (`contracts/` YAML)
- **Target Platform**: Linux GitHub Actions free tier (2 CPU, ~7 GB RAM, no GPU)
- **Constraints**: All R packages run on CPU via `rpy2`. Streaming loaders (`datasets.load_dataset(..., streaming=True)`) keep RAM < 5 GB. Expected wall‑time ≤ 5 h on the GitHub Actions runner.

## Constitution Check
| Principle | Compliance | Action |
|-----------|------------|--------|
| I. Reproducibility | ✅ PASS – seeds pinned, deterministic scripts, `requirements.txt` fixed. |
| II. Verified Accuracy | ✅ PASS – only URLs from the verified‑datasets block are cited. |
| III. Data Hygiene | ✅ PASS – checksums recorded, raw files immutable, no PII. |
| IV. Single Source of Truth | ✅ PASS – every statistic traced to a row in `data/` and a line in code. |
| V. Versioning Discipline | ✅ PASS – content hashes stored in project state; `updated_at` managed automatically. |
| VI. Compositional Data Analysis | ✅ PASS – CLR applied only where appropriate; ANCOM‑II and DESeq2 used per their assumptions. |
| VII. Cross‑Cohort Validation | ✅ PASS – analysis proceeds on any available cohort; single‑cohort results are flagged and reported. |

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

```text
src/
├── ingestion/
│   ├── unified_loader.py      # orchestrates fallback logic
│   ├── agp_loader.py          # loads AGP mirror (requires fiber variable)
│   ├── ukbb_loader.py         # loads UKBB mirror (requires fiber variable)
│   └── harmonize.py           # unit conversion, filtering
├── preprocessing/
│   ├── covariate_handler.py   # missingness, exclusion (>20%), imputation, batch handling
│   ├── clr_transform.py       # Bayesian replacement + CLR (Spearman only)
│   └── power_analysis.py      # post‑hoc power calculation
├── analysis/
│   ├── association.py         # Spearman ρ (CLR) & MaAsLin2 (raw counts)
│   ├── differential.py        # ANCOM‑II (relative) & DESeq2 (raw counts)
│   └── validation.py          # cross‑cohort replication logic
├── reporting/
│   ├── summary.py             # median fiber, replication rates, power report
│   └── paper_gen.py           # markdown report generation
└── utils/
    ├── checksum.py
    └── config.py
```

## Implementation Phases & FR/SC Mapping
| Phase | Tasks | FR(s) Addressed | SC(s) Addressed |
|-------|-------|-----------------|-----------------|
| **0 – Data Availability & Variable Fit** | - Verify presence of `fiber_intake_g`, `age`, `bmi`, `sex`, `antibiotic_use`, `batch` in each dataset. <br> - If a cohort lacks any required variable, **continue with the other cohort** and set `single_cohort=True`. | FR‑001, FR‑002 | SC‑006 |
| **1 – Download & Ingest** | - `src/ingestion/unified_loader.py` downloads AGP (`openmicrobiome/human_gut_microbiome`) and UKBB (`openmicrobiome/ukbb_gut_microbiome`) **only if** they contain all required variables; otherwise raises a clear `DataUnavailableError` with guidance. <br> - Record SHA256 checksums. | FR‑001 | SC‑006 |
| **2 – Harmonize & Filter** | - Convert fiber units to g/day. <br> - Exclude samples with reads < 5,000 or fiber > 200 g/day. | FR‑001, FR‑002 | SC‑006 |
| **3 – Covariate Cleaning** | - Compute per‑sample missingness; drop samples >20 % missing covariates (including batch). <br> - Median/mode impute remaining missing values. | FR‑008 (via clean covariates) | SC‑001 |
| **4 – CLR Transformation (Spearman only)** | - Apply Bayesian‑multiplicative replacement (`zCompositions`) then CLR on taxon counts for Spearman correlation. | FR‑003, VI (constitution) | SC‑001 |
| **5 – Association Analysis** | - **Spearman correlation** on CLR matrix (fiber vs. each taxon). <br> - **MaAsLin2** on **raw counts** with covariates: age, BMI, sex, antibiotic_use, **batch**. <br> - Apply Benjamini‑Hochberg FDR across taxa. | FR‑004, FR‑005 | SC‑001, SC‑002 |
| **6 – Differential Abundance** | - Define high/low fiber groups using cohort‑specific 75th/25th percentiles. <br> - Run **ANCOM‑II** on **relative abundances**. <br> - Run **DESeq2** on **raw counts**. <br> - Output TSV with required columns. | FR‑006, FR‑009 | SC‑002 |
| **7 – Cross‑Cohort Validation** | - Taxa significant (q < 0.05) in **both** cohorts **and** effect direction matches are flagged `replicated`. <br> - Compute replication rate (%). | FR‑007 | SC‑003 |
| **8 – Power & Sensitivity Analyses** | - **A priori power justification** (deferred): note that detectable β≈0.1 at α=0.05 with 80 % power would require [deferred] samples per cohort based on prior microbiome‐fiber literature. This is recorded in the plan for transparency. <br> - **Post‑hoc power calculation** for the smaller cohort using `statsmodels.stats.power.TTestIndPower`. Report achieved power and the minimum detectable effect size at [deferred] power. <br> - **Categorical fiber sensitivity analysis** (low/medium/high) to assess attenuation bias from self‑report error. | — (scientific robustness) | — |
| **9 – Summary & Reporting** | - Compute absolute median fiber intake per group per cohort. <br> - Summarize replication rate, power estimate, and flag `single_cohort` if applicable. <br> - Generate `final_report.md`. | FR‑008, FR‑009 | SC‑001, SC‑003 |
| **10 – Contract Validation** | - Run `pytest tests/contract/` against schemas in `contracts/`. | All FRs (output conformity) | All SCs (output correctness) |

## Edge‑Case Handling (explicit in spec)
- **Zero‑inflated taxa** → Bayesian replacement before CLR.  
- **Missing covariates** → Exclude >20 % missing; median/mode impute rest.  
- **Sample‑size disparity** → Report in summary; power analysis flags low‑power cohorts.  

## Compute Feasibility
All R packages (`MaAsLin2`, `ANCOMII`, `DESeq2`, `zCompositions`) run on CPU via `rpy2`. Streaming loaders (`datasets.load_dataset(..., streaming=True)`) keep RAM < 5 GB. Expected wall‑time ≤ 5 h on the GitHub Actions runner.
