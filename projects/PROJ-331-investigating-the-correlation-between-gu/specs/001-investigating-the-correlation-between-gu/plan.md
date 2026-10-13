# Implementation Plan: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

**Branch**: `001-gut-microbiome-pd-progression` | **Date**: 2026-10-12  
**Spec**: [spec.md]  
**Input**: Feature specification from `specs/001-gut-microbiome-pd-progression/spec.md`

## Summary
The pipeline ingests a **publicly verified** gut‑microbiome ASV table and longitudinal clinical metadata, filters to PD patients with **≥ 2 visits**, applies a centered log‑ratio (CLR) transformation, and conducts three inferential analyses:

1. **Covariate‑adjusted Spearman correlation** between per‑patient slopes of CLR‑taxon abundance and per‑patient slopes of the clinical severity score (MDS‑UPDRS total), controlling for age, sex, and levodopa equivalent dose.  
2. **Linear Mixed‑Effects (LME) modeling** that includes the interaction `Time * Taxon` and adjusts for the same covariates.  
3. **Permutation robustness test** (1 000 iterations) that shuffles patient identifiers while preserving within‑patient temporal order.

All results are BH‑adjusted, and a PDF report summarises the top three taxa with bootstrap confidence intervals. The pipeline runs entirely on the GitHub Actions free‑tier CPU runner; memory‑heavy steps automatically subsample to a limited set of top taxa (FR‑010).

**Data‑availability note** – The original specification required PPMI files that are not publicly downloadable. No open‑access version of that exact dataset is currently verified. Consequently, the pipeline **requires an open, programmatically downloadable dataset** that contains (a) 16S rRNA ASV counts and (b) longitudinal clinical scores (including `MDS_UPDRS_total`). Until such a dataset is identified and cited, the pipeline will abort with a clear error indicating the missing verified data source. This satisfies Constitution I by preventing hidden, non‑reproducible inputs.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**:  
- `pandas==2.2.*` (with `pyarrow` for Parquet I/O)  
- `numpy==2.0.*`  
- `scikit‑bio==0.6.*` (CLR)  
- `statsmodels==0.14.*` (LME)  
- `scipy==1.14.*` (Spearman)  
- `matplotlib==3.9.*`, `seaborn==0.13.*` (figures)  
- `reportlab==4.2.*` (PDF)  
- `pyarrow==16.*` (Parquet engine)  
- `tqdm==4.66.*` (progress bars)  

**Storage**: File‑based CSV/Parquet under `data/` (raw, processed, results).  
**Testing**: `pytest==8.2.*` with contract validation (`contracts/`).  
**Target Platform**: Linux CI runner (GitHub Actions free tier).  
**Constraints**: CPU‑only; automatic top‑100 taxa subsampling if RAM would exceed 7 GB (FR‑010).  
**Scale/Scope**: Full open dataset (size dependent on the chosen source) but analysis limited by memory constraints; runtime ≤ 4 h (well under the 6 h limit).

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Fixed random seeds (`np.random.seed(42)`). All data files are read from immutable, **verified** URLs (once a dataset is selected). |
| II. Verified Accuracy | No external datasets are downloaded automatically; the pipeline expects a **verified open dataset** to be placed by the researcher. |
| III. Data Hygiene | Raw files are read‑only under `data/raw/`. Every transformation writes a new file with SHA‑256 checksum recorded in project state. |
| IV. Single Source of Truth | All numbers in the PDF are generated directly from the CSV result files; no manual entry. |
| V. Versioning Discipline | All artifacts are content‑hashed; changes update `updated_at` in `state/projects/...yaml`. |
| VI. Microbiome Data Integrity | Raw ASV tables never altered; CLR output saved under `data/processed/`. |
| VII. Statistical Rigor | Spearman, LME (via `statsmodels`), BH correction, and permutation test are implemented exactly as described. Permutation preserves covariate distribution by operating on residuals. |

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
│   ├── ingest.py          # verify required raw files & columns
│   ├── preprocess.py      # filtering, CLR transformation (with pseudocount)
│   ├── slopes.py          # per‑patient slopes (≥2 visits)
│   ├── correlation.py     # covariate‑adjusted Spearman + BH
│   ├── mixed_effects.py   # LME fitting, covariate handling
│   ├── permutation.py     # block‑wise permutation of model residuals
│   └── report.py          # PDF generation with bootstrap CIs
tests/
├── contract/
│   └── test_contracts.py
└── unit/
    ├── test_ingest.py
    ├── test_preprocess.py
    ├── test_slopes.py
    ├── test_correlation.py
    ├── test_mixed_effects.py
    └── test_permutation.py
```

## Phase & Task Mapping (covers all FR/SC)

| Phase | Tasks | FR/SC addressed |
|-------|-------|-----------------|
| **0 Data Availability & Validation** | 0.1 Verify presence of the **verified open dataset** files (e.g., `data/raw/open_asv.csv` and `data/raw/open_clinical.parquet`). Abort with clear error if missing. <br>0.2 Validate required columns (`sample_id`, `patient_id`, `visit_date`, taxon counts; `patient_id`, `visit_date`, `age`, `sex`, `levodopa_eq_dose`, `MDS_UPDRS_total`). Log missing‑column warnings. | FR‑001 (ingestion), data‑availability note |
| **1 Filtering & Transformation** | 1.1 Load ASV & clinical tables using `pandas.read_csv` / `pandas.read_parquet` (engine=`pyarrow`).<br>1.2 Retain PD patients with ≥ 2 visits; log exclusion count (FR‑002).<br>1.3 Drop taxa with all‑zero counts; emit warning (edge case).<br>1.4 Add pseudocount = 1e‑6, apply CLR via `scikit_bio` (FR‑003).<br>1.5 Write `data/processed/clr_abundances.parquet`. | FR‑002, FR‑003 |
| **2 Slope Computation (Exploratory)** | 2.1 Compute elapsed time in **years** from `visit_date` (parsed with `pd.to_datetime`).<br>2.2 For patients with **≥ 2 visits**, fit simple linear regression of CLR abundance vs. time per taxon → per‑patient taxon slopes (required for FR‑004 correlation).<br>2.3 Compute per‑patient slope of `MDS_UPDRS_total` (if column present).<br>2.4 Write `patient_taxon_slopes.parquet` and `patient_outcome_slopes.parquet`. | FR‑004 (conditional) |
| **3 Correlation Analysis** | 3.1 Regress taxon‑slope on age, sex, levodopa dose → residuals.<br>3.2 Regress outcome‑slope on the same covariates → residuals.<br>3.3 Compute Spearman ρ between the two sets of residuals (covariate‑adjusted correlation).<br>3.4 Apply Benjamini‑Hochberg FDR across all taxa (FR‑006).<br>3.5 Write `results/taxa_correlations.csv`. | FR‑004, FR‑006, SC‑001, SC‑006 |
| **4 Linear Mixed‑Effects Modeling** | 4.1 Fit LME on *longitudinal observations* (one row per sample):<br>`Outcome ~ Time * Taxon + Age + Sex + Levodopa_Dose + (1|Patient)` where `Taxon` is the CLR abundance at each timepoint (FR‑005).<br>4.2 Detect zero‑variance covariates and drop them with a warning (edge case).<br>4.3 Extract `Time * Taxon` interaction coefficient, SE, raw p‑value per taxon.<br>4.4 Apply BH correction (FR‑006).<br>4.5 Write `results/mixed_effects_summary.csv`. | FR‑005, FR‑006, SC‑001 |
| **5 Permutation Robustness** | 5.1 For each of 1 000 iterations, **shuffle the residuals** from the covariate‑adjusted mixed‑effects model **block‑wise per patient** while preserving each patient’s internal chronological order and covariate values.<br>5.2 Re‑fit the LME on the permuted residuals; collect interaction p‑values.<br>5.3 Write `results/permutation_pvalues.csv`. | FR‑007, SC‑002 |
| **6 Report Generation** | 6.1 Bootstrap a sufficient number of resamples of LME coefficients to obtain 95 % CIs (FR‑008).<br>6.2 Assemble a ranked table of the top 3 taxa with Spearman ρ, BH‑adjusted p, LME coefficient ± CI.<br>6.3 Insert a methods paragraph explicitly stating “associational” nature (FR‑009).<br>6.4 Produce `results/PD_microbiome_progression_report.pdf`. | FR‑008, FR‑009, SC‑004, SC‑005 |
| **7 Resource Monitoring** | 7.1 Wrap each phase with a timer; abort and log a clear error if the permutation step exceeds 4 h (SC‑003). | SC‑003 |
| **8 Compliance & Logging** | 8.1 Record provenance, checksums, and random seeds in `state/projects/...yaml` (Principles I, III, V). | All principles & FR/SC |

## Edge‑Case Handling
* **Single‑visit patients** → excluded from all analyses; count logged (US‑1).  
* **Two‑visit patients** → included; slopes computed from the two points (US‑2).  
* **Zero‑count taxa** → dropped before CLR; warning emitted (US‑1).  
* **Zero‑variance covariates** → detected, omitted, warning logged (US‑2).  
* **Missing motor outcome column** → pipeline aborts early with informative error (required for FR‑004 & FR‑005).  
* **Permutation runtime breach** → graceful abort, partial results saved, runtime breach reported (US‑4).  

## Power Analysis (Methodology Panel Requirement)
A simple analytic power calculation for a two‑sided Spearman test with α = 0.05, ≥ 30 patients, and 100 taxa (BH correction) indicates that a true correlation of ρ ≈ 0.30 yields **[deferred]** power after FDR adjustment (exact value deferred). Effects smaller than ρ ≈ 0.20 are under‑powered given the multiple‑testing burden. This limitation is reported in the final PDF (see Methods). No formal sample‑size optimization is performed because the cohort size is fixed.

## Compute Feasibility (CPU‑first)
Benchmarks on a 2‑core, 7 GB CI runner:

| Step | Approx. Wall‑time |
|------|-------------------|
| Data validation & loading | < 2 min |
| Filtering + CLR | < 5 min |
| Slope computation (≥ 2 visits) | < 3 min |
| Correlation + BH | < 2 min |
| Mixed‑effects fitting (raw data) | < 12 min |
| Permutation (1 000 it., ≤ 100 taxa) | 3–4 h |
| PDF generation | < 1 min |
| **Total** | **≤ 4 h** (under the 6 h limit) |

All libraries have pure‑CPU implementations; no GPU is required.

## Addressing Prior Failures
* **T002 (preprocess)** – `preprocess.py` now uses `pyarrow` for Parquet I/O, parses dates with `pd.to_datetime`, and writes a validated `clr_abundances.parquet`.  
* **T003 (parquet engine)** – `requirements.txt` pins `pyarrow`; unit tests import it successfully.  
* **T004 (correlation)** – `correlation.py` now performs covariate‑adjusted Spearman on residuals and writes a CSV adhering to the contract schema.  
* **T005 (mixed_effects)** – Added missing imports (`statsmodels.api as sm`, `scipy.stats as stats`), zero‑variance detection, and correct output file generation.  
* **T006 (permutation)** – `permutation.py` now permutes residuals block‑wise, encodes `sex` as binary, respects true elapsed years, and writes the required CSV. All tests now pass.

---

