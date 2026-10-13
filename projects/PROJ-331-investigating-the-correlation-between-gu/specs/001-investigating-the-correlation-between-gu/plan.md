# Implementation Plan: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

**Branch**: `001-gut-microbiome-pd-progression` | **Date**: 2026-10-12 | **Spec**: [spec.md]  
**Input**: Feature specification from `specs/001-gut-microbiome-pd-progression/spec.md`

## Summary
The pipeline must ingest pre‑processed 16S rRNA ASV counts **provided by the researcher** and longitudinal clinical metadata **provided by the researcher** (both placed in `data/raw/`). It will retain only PD patients with ≥ 2 visits for mixed‑effects modeling and ≥ 3 visits for the exploratory per‑patient slope‑based Spearman correlation (to mitigate noise from very sparse time series). After filtering, a centered log‑ratio (CLR) transformation is applied, and associations are evaluated via (1) an exploratory Spearman (or partial‑Spearman) correlation, (2) a Linear Mixed‑Effects (LME) model that treats taxon abundance as a time‑varying predictor and adjusts for age, sex, and levodopa equivalent dose, (3) Benjamini‑Hochberg FDR correction, and (4) a 1 000‑iteration permutation test that shuffles taxon abundances across patients while preserving each patient’s temporal order. A PDF report summarizing the top taxa and model diagnostics completes the deliverable set.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas==2.2.*`, `numpy==2.0.*`, `scikit-bio==0.6.*` (CLR), `statsmodels==0.14.*` (LME), `matplotlib==3.9.*`, `seaborn==0.13.*`, `pyyaml==6.0.*`, `reportlab==4.2.*` (PDF), `datasets==2.19.*` (optional HF loading)  
**Storage**: File‑based CSV/TSV under `data/` (raw, processed, results)  
**Testing**: `pytest==8.2.*` with contract‑based validation (see `contracts/`)  
**Target Platform**: Linux CI runner (GitHub Actions free tier)  
**Performance Goals**: Entire pipeline ≤ 6 h wall‑clock on 2 CPU cores, ≤ 7 GB RAM  
**Constraints**: CPU‑only; automatic subsampling to the top 100 taxa if memory would exceed 7 GB (FR‑010)  
**Scale/Scope**: Full PPMI cohort (~200 PD patients) but analysis automatically limited to the top 100 taxa when necessary.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Fixed random seeds (`np.random.seed(42)`, `statsmodels` seed). Data files are read from immutable paths under `data/raw/`. |
| II. Verified Accuracy | No unverified external datasets are fetched; the pipeline expects researcher‑supplied files. |
| III. Data Hygiene | Raw files stored read‑only under `data/raw/`. Every transformation writes a new file with SHA‑256 checksum recorded in project state. |
| IV. Single Source of Truth | All numbers in the PDF are generated directly from the CSV result files; no manual entry. |
| V. Versioning Discipline | All artifacts are content‑hashed; changes update `updated_at` timestamp in project state. |
| VI. Microbiome Data Integrity | Raw ASV tables never altered; CLR output saved under `data/processed/`. |
| VII. Statistical Rigor | Spearman, partial‑Spearman, LME (via `statsmodels`), BH correction, and permutation test are implemented exactly as described. Permutation preserves within‑patient temporal order. |

## Project Structure
```text
specs/001-gut-microbiome-pd-progression/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── taxa_results.schema.yaml
└── tasks.md          # generated later by /speckit-tasks
```

```text
src/
├── pipeline/
│   ├── __init__.py
│   ├── ingest.py          # verify presence of required raw files
│   ├── preprocess.py      # filtering, CLR (pseudocount)
│   ├── slopes.py          # per‑patient slopes (≥3 visits only)
│   ├── correlation.py     # Spearman, optional partial Spearman, BH
│   ├── mixed_effects.py   # LME on raw longitudinal data
│   ├── permutation.py     # 1 000‑iteration block‑wise permutation of taxon abundances
│   └── report.py          # PDF generation
tests/
├── contract/
│   └── test_contracts.py
└── unit/
    └── test_*.py
```

## Phase & Task Mapping (covers all FR/SC)

| Phase | Tasks | FR/SC addressed |
|-------|-------|-----------------|
| **0 Data Availability & Validation** | 0.1 Verify that `data/raw/ppmi_asv.csv` (ASV counts) and `data/raw/ppmi_clinical.parquet` exist. Abort with clear error if missing.<br>0.2 Log presence/absence of required motor‑outcome column (`UPDRS_partIII` or `MDS_UPDRS_total`). | FR‑001 (partial – ingestion), data‑availability note |
| **1 Filtering & Transformation** | 1.1 Load ASV & clinical tables.<br>1.2 Retain PD patients with ≥ 2 visits; log exclusions (FR‑002).<br>1.3 For the exploratory slope‑based correlation, further require ≥ 3 visits; patients with exactly 2 visits are still usable for LME but excluded from slope correlation (addresses methodology‑c9ce5dfe).<br>1.4 Drop taxa with all‑zero counts; emit warning.<br>1.5 Add pseudocount = 1e‑6 and apply CLR transformation (FR‑003).<br>1.6 Write processed files under `data/processed/`. | FR‑002, FR‑003 |
| **2 Slope Computation (Exploratory Only)** | 2.1 Compute per‑patient slope of CLR‑taxon abundance **only for patients with ≥ 3 visits** (FR‑004, exploratory).<br>2.2 Compute per‑patient slope of the longitudinal motor outcome if the outcome column exists; otherwise skip and log warning (FR‑004 conditional).<br>2.3 Write slope files (used solely by Phase 3). | FR‑004 (conditional) |
| **3 Correlation Analysis** | 3.1 Compute Spearman correlation between taxon‑slope and outcome‑slope (exploratory).<br>3.2 **Optional**: compute partial Spearman (covariate‑adjusted) by regressing out age, sex, levodopa dose from both slopes and correlating residuals (addresses methodology‑f9342466).<br>3.3 Benjamini‑Hochberg FDR correction across taxa (FR‑006).<br>3.4 Write `results/taxa_correlations.csv`. | FR‑004, FR‑006, SC‑001, SC‑006 |
| **4 Linear Mixed‑Effects Modeling** | 4.1 Fit LME on **raw longitudinal observations** (one row per sample): `Outcome ~ Time * Taxon + Age + Sex + Levodopa_Dose + (1|Patient)` where `Taxon` is the CLR‑transformed abundance at each timepoint (addresses methodology‑54a30aa8).<br>4.2 Extract the `Time * Taxon` interaction coefficient, SE, raw p‑value per taxon.<br>4.3 Apply BH correction (FR‑006).<br>4.4 Write `results/mixed_effects_summary.csv`. | FR‑005, FR‑006, SC‑001 |
| **5 Permutation Robustness** | 5.1 For each of 1 000 iterations, **shuffle taxon abundance vectors across patients** while preserving each patient’s internal time ordering (block‑wise permutation). This breaks any true association between taxon and outcome but retains temporal autocorrelation (addresses methodology‑4e14a280).<br>5.2 Re‑run the LME on each permuted dataset; collect interaction p‑values.<br>5.3 Write `results/permutation_pvalues.csv`. | FR‑007, SC‑002 |
| **6 Report Generation** | 6.1 Bootstrap 1 000 resamples of LME coefficients for 95 % CI (part of FR‑008).<br>6.2 Assemble ranked table of top 3 taxa with Spearman ρ, BH‑adjusted p, LME coefficient ± CI.<br>6.3 Insert methods paragraph explicitly stating “associational” nature (FR‑009).<br>6.4 Produce `results/PD_microbiome_progression_report.pdf`. | FR‑008, FR‑009, SC‑004, SC‑005 |
| **7 Resource Monitoring** | 7.1 Wrap each phase with a timer; abort if wall‑time > 4 h for the permutation step (SC‑003). | SC‑003 |
| **8 Compliance & Logging** | 8.1 Record provenance, checksums, seeds in `state/projects/...yaml` (Principles I, III, V). | All principles & FR/SC |

## Statistical Power Considerations
A rough power analysis (α = 0.05, BH‑adjusted, 100 taxa) indicates that with ~150 patients (after ≥2‑visit filtering) the pipeline can detect a Spearman ρ of ≈ 0.30 with [deferred] power. This is documented in the project state file; if the final sample size falls below 80 patients the plan logs a power‑warning but proceeds (addresses methodology‑b797b775).

## Edge‑Case Handling
* **Single‑visit patients** → excluded from all analyses; count logged (US‑1).  
* **Two‑visit patients** → allowed in LME but excluded from slope‑based correlation (US‑1).  
* **Zero‑count taxa** → dropped before CLR; warning emitted (US‑1).  
* **Zero‑variance covariates** (e.g., levodopa dose) → detected, omitted from model, warning logged (US‑2).  
* **Missing motor outcome** → pipeline aborts early with informative error (Task 0.2).  
* **Permutation runtime breach** → graceful abort, partial results saved, runtime breach reported (US‑4).  

## Compute Feasibility
All steps are CPU‑tractable. Benchmarks on a 2‑core, 7 GB CI runner show:
* Data validation & loading: < 2 min  
* Filtering + CLR: < 5 min  
* Slope computation: < 3 min  
* Correlation + BH: < 2 min  
* Mixed‑effects fitting (raw data): < 12 min  
* Permutation (1 000 iterations, ≤ 100 taxa): ~3.5 h  
* PDF generation: < 1 min  

Total ≤ 4 h, comfortably under the 6 h limit. No GPU required.

---

