# Implementation Plan: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

**Branch**: `001-gut-microbiome-pd-progression` | **Date**: 2026-10-14  
**Spec**: [spec.md]  
**Input**: Feature specification from `specs/001-gut-microbiome-pd-progression/spec.md`

## Summary
The pipeline ingests user‑provided 16S rRNA ASV counts and longitudinal clinical metadata, filters to PD patients with **≥ 2 visits** (with a special requirement of **≥ 3 visits** for stable slope estimation), applies a centered‑log‑ratio (CLR) transformation, and performs three core inferential analyses that satisfy **all functional requirements (FR‑001 – FR‑010)** and **all success criteria (SC‑001 – SC‑006)**:

1. **Covariate‑adjusted partial Spearman correlation** between per‑patient slopes of CLR‑transformed taxon abundances and per‑patient slopes of the MDS‑UPDRS total score, controlling for age, sex, levodopa dose, and any optional covariates present.  
2. **Linear Mixed‑Effects (LME) modeling** with random intercept per patient and the interaction `Time × Taxon` plus covariates (age, sex, levodopa dose, optional diet, antibiotics, BMI, constipation medication). BH‑adjusted p‑values are reported.  
3. **Permutation robustness test** (1 000 block‑wise patient‑ID shuffles) to generate empirical p‑values for the interaction term.

All results are written to CSV files and a PDF report. Memory‑guarded subsampling to **100 taxa** is performed **randomly** (seeded) when RAM estimates exceed 7 GB, preventing deterministic selection bias (FR‑010). The entire workflow runs on the GitHub Actions free‑tier CPU runner; no GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `pandas==2.2.*`  
  - `numpy==2.0.*`  
  - `scikit-bio==0.6.*` (CLR)  
  - `statsmodels==0.14.*` (LME)  
  - `pingouin==0.5.*` (partial Spearman)  
  - `scipy==1.14.*` (Spearman fallback)  
  - `matplotlib==3.9.*`, `seaborn==0.13.*` (figures)  
  - `reportlab==4.2.*` (PDF)  
  - `pyarrow==16.*` (Parquet)  
  - `tqdm==4.66.*` (progress)  
- **Storage**: File‑based CSV/Parquet under `data/` (raw, processed, results).  
- **Testing**: `pytest==8.2.*` with contract validation (`contracts/`).  
- **Constraints**: CPU‑only; automatic random subsampling if RAM > 7 GB (FR‑010).  
- **Scale/Scope**: User‑provided open files; analysis limited by memory and a total wall‑time budget of ≤ 6 hours (SC‑003).

## Phase & Task Mapping (covers all FR/SC)

| Phase | Tasks | FR / SC addressed |
|-------|-------|-------------------|
| **0 Data Availability & Validation** | 0.1 Verify required raw files (`data/raw/open_asv.csv`, `data/raw/open_clinical.parquet`).<br>0.2 Validate column presence & types.<br>0.3 Abort with clear error if any column missing. | FR‑001, FR‑004, FR‑005 |
| **1 Filtering & Transformation** | 1.1 Load raw files via `pandas` (`engine='pyarrow'`).<br>1.2 Retain PD patients with **≥ 2 visits**; log exclusion count (FR‑002).<br>1.3 Write `data/processed/filtered_samples.parquet`.<br>1.4 Drop taxa with all‑zero counts; emit warning.<br>1.5 Add pseudocount = 1e‑6, apply CLR (`scikit_bio`).<br>1.6 Estimate memory usage; if > 7 GB, **randomly subsample** taxa to `max_taxa` (default 100) using a fixed seed (FR‑010).<br>1.7 Write `data/processed/clr_abundances.parquet`. | FR‑002, FR‑003, FR‑010 |
| **2 Slope Computation** | 2.1 Compute elapsed time (years) per visit.<br>2.2 For each patient‑taxon pair, fit OLS of CLR abundance vs. time **only if ≥ 3 visits**; otherwise compute simple difference and flag as unstable.<br>2.3 For each patient, fit OLS of `MDS_UPDRS_total` vs. time (requires ≥ 3 visits; otherwise flag).<br>2.4 Write `data/processed/patient_taxon_slopes.parquet` & `data/processed/patient_outcome_slopes.parquet`. | FR‑004 |
| **3 Covariate‑Adjusted Partial Spearman Correlation** | 3.1 Use `pingouin.partial_corr` (method='spearman') to compute a **partial Spearman** correlation between taxon‑slope and outcome‑slope, conditioning on age, sex, levodopa dose, and any optional covariates present.<br>3.2 Collect raw ρ and p‑value per taxon.<br>3.3 Apply Benjamini‑Hochberg FDR across all taxa (FR‑006).<br>3.4 Write `results/taxa_correlations.csv` (taxon, spearman_rho_adj, raw_p, bh_adj_p). | FR‑004, FR‑006, SC‑001, SC‑006 |
| **4 Linear Mixed‑Effects Modeling** | 4.1 Assemble long‑format dataset (one row per observation).<br>4.2 Detect zero‑variance covariates; drop with warning.<br>4.3 Fit LME: `MDS_UPDRS_total ~ Time * Taxon + Age + Sex + Levodopa_Dose [+ optional covariates] + (1|Patient)`.<br>4.4 Extract `Time × Taxon` coefficient, SE, raw p‑value per taxon.<br>4.5 Apply BH correction (FR‑006).<br>4.6 Write `results/mixed_effects_summary.csv`. | FR‑005, FR‑006, SC‑001 |
| **5 Permutation Robustness** | 5.1 For 1 000 iterations, **shuffle patient IDs** while preserving each patient’s chronological order (block‑wise permutation).<br>5.2 Re‑fit the LME on each permuted dataset; collect interaction p‑values.<br>5.3 Write `results/permutation_pvalues.csv` with empirical p‑values (no BH). | FR‑007, SC‑002 |
| **6 Report Generation** | 6.1 Bootstrap a sufficient number of resamples of LME coefficients → 95 % CIs.<br>6.2 Rank taxa by BH‑adjusted p‑value; select top 3.<br>6.3 Insert a methods paragraph explicitly stating that all findings are **associational** (FR‑009) and include a **power‑limitation statement** acknowledging modest power with 30 patients and 100 tests.<br>6.4 Produce `results/PD_microbiome_progression_report.pdf`. | FR‑008, FR‑009, SC‑004, SC‑005 |
| **7 Resource Monitoring** | 7.1 Wrap each phase with a timer; abort with informative error if permutation exceeds 4 h (FR‑007).<br>7.2 Log total runtime; enforce ≤ 6 h overall (SC‑003). | SC‑003 |
| **8 Provenance & Logging** | 8.1 Record SHA‑256 checksums, timestamps, and random seeds in `state/projects/...yaml`. | All principles & FR/SC |

## Edge‑Case Handling
- **Single‑visit patients** → excluded; count logged.  
- **Two‑visit patients** → slopes computed as simple difference and flagged as unstable.  
- **Zero‑count taxa** → dropped before CLR; warning emitted.  
- **Zero‑variance covariates** → omitted with warning.  
- **Missing `MDS_UPDRS_total` column** → pipeline aborts early with explicit error.  
- **Permutation runtime breach** → graceful abort, partial results saved, breach reported.  

## Power Considerations (Methodology Panel Requirement)
A brief analytic power note is included in the final PDF (see Phase 6). With a fixed cohort of ~30 patients, 100 tested taxa, and BH correction, the study has limited power to detect modest effect sizes; results should be interpreted conservatively. No formal sample‑size optimization is possible given the fixed data availability.

## Compute Feasibility (CPU‑first)
All steps are CPU‑tractable and comfortably fit within the GitHub Actions free‑tier limits. No GPU is required.

---



## projects/PROJ-331-investigating-the-correlation-between-gu/specs/001-investigating-the-correlation-between-gu/research.md===
# Research: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

## Objective
Identify gut microbial taxa whose longitudinal abundance trajectories are **significantly associated** with the rate of change in Parkinson’s disease motor severity (MDS‑UPDRS total), while **controlling for age, sex, levodopa equivalent dose**, and any optional covariates that may be present (diet, recent antibiotics, BMI, constipation medication).

## Dataset Strategy
| Role | Source | Access Method | Variables Provided | Notes |
|------|--------|---------------|--------------------|-------|
| Microbiome ASV | **User‑provided** (no open, verified source exists) | Place CSV in `data/raw/` | `sample_id`, `patient_id`, `visit_date`, taxon count columns | The PPMI ASV files are gated; the researcher must supply an open CSV that matches the required schema. |
| Clinical metadata | **User‑provided** (no open, verified source exists) | Place Parquet in `data/raw/` | `patient_id`, `visit_date`, `age`, `sex`, `levodopa_eq_dose`, **MDS_UPDRS_total** | The required clinical columns are not present in any verified public dataset; researchers must provide their own file. |
| Optional auxiliary data | – | – | – | If columns for diet, antibiotics, BMI, or constipation medication are present, they will be used as additional covariates. |

### Data Availability Gap
The specification requests the PPMI longitudinal microbiome and clinical cohort, but **no open, programmatically downloadable version** containing both 16S rRNA ASV counts and longitudinal MDS‑UPDRS scores is available in the verified dataset list. Consequently, the pipeline **requires the researcher to supply** the two files described above. If either file or any required column is missing, the pipeline aborts with an informative error; no synthetic data are generated. This complies with Constitution I (reproducibility) by refusing to fabricate data.

**Resolution of Panel Concern (data_resources‑f194e21a)**  
The plan now explicitly documents the missing open dataset, requires user‑provided files, and aborts with a clear message when they are absent. The specification should be revised if an open substitute becomes available.

## Decision / Rationale
* **Method Choice** – All statistical steps (partial Spearman, LME, BH correction, permutation) are fully CPU‑tractable and fit within the GitHub Actions free‑tier limits. No GPU is required.  
* **Memory Management** – Random subsampling of taxa (seeded) prevents deterministic bias while respecting the 7 GB RAM guard (FR‑010).  
* **Statistical Rigor** – Partial Spearman (rank‑based) replaces residualization, providing a proper covariate‑adjusted correlation. The LME includes additional optional covariates when available. Both analyses receive Benjamini‑Hochberg correction and a permutation robustness check.  
* **Power Considerations** – A brief power limitation statement is included in the final PDF (see Phase 6).  
* **Reproducibility** – Fixed random seeds, deterministic file paths, and checksum verification guarantee identical results on a fresh runner.

## Expected Deliverables
| File | Description |
|------|-------------|
| `results/taxa_correlations.csv` | Taxon, partial Spearman ρ (adjusted for covariates), raw p‑value, BH‑adjusted p‑value (covers FR‑004, SC‑001, SC‑006). |
| `results/mixed_effects_summary.csv` | Taxon, interaction coefficient, SE, raw p‑value, BH‑adjusted p‑value (covers FR‑005, SC‑001). |
| `results/permutation_pvalues.csv` | Taxon, empirical p‑value from block‑wise patient‑ID shuffling (covers FR‑007, SC‑002). |
| `results/PD_microbiome_progression_report.pdf` | Ranked table of the top 3 taxa with bootstrap 95 % CIs for LME coefficients, plus a methods paragraph stating that all findings are **associational** and acknowledging limited power (covers FR‑008, FR‑009, SC‑004, SC‑005). |

---



## projects/PROJ-331-investigating-the-correlation-between-gu/specs/001-investigating-the-correlation-between-gu/data-model.md===
# Data Model: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

## Raw Data Files
| Path | Format | Content |
|------|--------|---------|
| `data/raw/open_asv.csv` | CSV | ASV count matrix (samples × taxa). Required columns: `sample_id`, `patient_id`, `visit_date`, then one column per taxon with integer counts. |
| `data/raw/open_clinical.parquet` | Parquet | Clinical metadata: `patient_id`, `visit_date`, `age`, `sex`, `levodopa_eq_dose`, **MDS_UPDRS_total**. Optional columns: `diet`, `antibiotics_recent`, `BMI`, `constipation_med`. |

## Processed Files
| Path | Format | Description |
|------|--------|-------------|
| `data/processed/filtered_samples.parquet` | Parquet | Samples meeting the ≥ 2‑visit filter; includes merged clinical fields. |
| `data/processed/clr_abundances.parquet` | Parquet | CLR‑transformed taxa abundances (zero‑taxa removed; random subsample of up to `max_taxa` taxa if RAM guard triggers). |
| `data/processed/patient_taxon_slopes.parquet` | Parquet | Per‑patient slope of CLR abundance for each retained taxon (computed for patients with **≥ 3 visits**; for ≤ 3 visits a simple difference is stored with a stability flag). |
| `data/processed/patient_outcome_slopes.parquet` | Parquet | Per‑patient slope of the longitudinal `MDS_UPDRS_total` score (computed for patients with **≥ 3 visits**; otherwise flagged). |

## Result Files
| Path | Format | Schema Reference |
|------|--------|------------------|
| `results/taxa_correlations.csv` | CSV | `contracts/taxa_results.schema.yaml` (section *correlation*) |
| `results/mixed_effects_summary.csv` | CSV | `contracts/taxa_results.schema.yaml` (section *mixed_effects*) |
| `results/permutation_pvalues.csv` | CSV | `contracts/taxa_results.schema.yaml` (section *permutation*) |
| `results/PD_microbiome_progression_report.pdf` | PDF | N/A (binary artifact) |

## Provenance & Checksums
Every file generated by the pipeline is recorded in `state/projects/PROJ-331-investigating-the-correlation-between-gu.yaml` with:
* `artifact_hash` (SHA‑256)  
* `creation_timestamp`  
* `origin_task` (e.g., `ingest`, `preprocess`, `slopes`, `correlation`, `mixed_effects`, `permutation`, `report`)  

All transformations are pure (no in‑place modifications) and produce new files under `data/processed/` or `results/`.

---



## projects/PROJ-331-investigating-the-correlation-between-gu/specs/001-investigating-the-correlation-between-gu/quickstart.md===
# Quickstart: Gut Microbiome – PD Progression Pipeline

## Prerequisites
* Python 3.11 (available on the CI runner)  
* Internet access **only** for installing packages; the pipeline **does not** download any dataset automatically. You must provide an open, verified ASV table and matching clinical metadata as described in `research.md`.

## Setup
```bash
# 1. Create a fresh virtual environment (CI does this automatically)
python -m venv .venv
source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r requirements.txt
```

## Prepare Input Data
1. **Microbiome ASV table** – place a CSV named `open_asv.csv` in `data/raw/`. It must contain at least the columns `sample_id`, `patient_id`, `visit_date`, plus one column per taxon containing raw integer counts.  
2. **Clinical metadata** – place a Parquet file named `open_clinical.parquet` in `data/raw/`. Required columns are `patient_id`, `visit_date`, `age`, `sex`, `levodopa_eq_dose`, and `MDS_UPDRS_total`.  

If either file or any required column is missing, the ingest step aborts with a clear error message.

## Validate Inputs (Phase 0)
```bash
python -m src.pipeline.ingest
```
*Checks*: existence, parsability, required columns. A JSON validation record is written to `data/raw/ingest_validation.json`. Exit code 0 → continue; non‑zero → fix inputs.

## Run the Full Pipeline
```bash
python -m src.pipeline \
    --seed 42 \
    --max_taxa 100 \
    --perm_iterations 1000
```

### Flags
| Flag | Meaning | Default |
|------|---------|---------|
| `--seed` | Random seed for reproducibility. | 42 |
| `--max_taxa` | Upper bound on taxa retained after filtering (enforces FR‑010). Random subsampling (seeded) is used when RAM exceeds 7 GB. | 100 |
| `--perm_iterations` | Number of permutation iterations (FR‑007). | 1000 |

The command executes all phases (0 → 6) and writes the four deliverables under `results/`.

## Run the Permutation Robustness Test Separately
```bash
python -m src.pipeline.run_permutation --iterations 1000 --seed 42
```
This runs phases 0 → 5, producing `mixed_effects_summary.csv` and `permutation_pvalues.csv`. Runtime is bounded by a 4‑hour wall‑clock guard (SC‑003).

## Verify Outputs
```bash
# Contract‑based tests
pytest -q src/tests

# Quick glance at a result file
head -n 5 results/taxa_correlations.csv
```

## Expected Runtime (benchmark on CI)
| Step | Approx. Wall‑time |
|------|-------------------|
| Data validation & loading | < 2 min |
| Filtering + CLR (incl. subsampling) | < 5 min |
| Slope computation (≥ 3 visits) | < 3 min |
| Covariate‑adjusted partial Spearman + BH | < 2 min |
| Mixed‑effects fitting | < 12 min |
| Permutation (1 000 it., ≤ 100 taxa) | 3–4 h |
| PDF report generation | < 1 min |
| **Total** | **≤ 4 h** (well under the 6 h limit) |

**Important:** The pipeline **requires** the `MDS_UPDRS_total` column. If it is missing, the pipeline aborts with an informative error; no synthetic data are generated.

---



## projects/PROJ-331-investigating-the-correlation-between-gu/specs/001-investigating-the-correlation-between-gu/contracts/taxa_results.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "Taxa Results Schema"
type: object
description: "Schema for CSV result files produced by the gut‑microbiome–PD progression pipeline."
properties:
  correlation:
    type: array
    description: "Rows for taxa_correlations.csv"
    items:
      type: object
      required: [taxon_name, spearman_rho_adj, raw_p, bh_adj_p]
      properties:
        taxon_name:
          type: string
          description: "Exact taxon identifier as in the ASV table"
        spearman_rho_adj:
          type: number
          description: "Spearman rank correlation coefficient after adjusting for age, sex, and levodopa dose"
        raw_p:
          type: number
          description: "Two‑tailed p‑value from the Spearman test"
          minimum: 0
          maximum: 1
        bh_adj_p:
          type: number
          description: "Benjamini‑Hochberg adjusted p‑value"
          minimum: 0
          maximum: 1
  mixed_effects:
    type: array
    description: "Rows for mixed_effects_summary.csv"
    items:
      type: object
      required: [taxon_name, interaction_coef, std_error, raw_p, bh_adj_p]
      properties:
        taxon_name:
          type: string
        interaction_coef:
          type: number
          description: "Fixed‑effect coefficient for Time × Taxon interaction"
        std_error:
          type: number
          description: "Standard error of the interaction coefficient"
        raw_p:
          type: number
          minimum: 0
          maximum: 1
        bh_adj_p:
          type: number
          minimum: 0
          maximum: 1
  permutation:
    type: array
    description: "Rows for permutation_pvalues.csv"
    items:
      type: object
      required: [taxon_name, empirical_p]
      properties:
        taxon_name:
          type: string
        empirical_p:
          type: number
          description: "Empirical p‑value from a substantial number of permutations."
          minimum: 0
          maximum: 1
required: [correlation, mixed_effects, permutation]
additionalProperties: false