# Implementation Plan: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

**Branch**: `001-gut-microbiome-pd-progression` | **Date**: 2026-10-12 | **Spec**: [spec.md]  
**Input**: Feature specification from `specs/001-gut-microbiome-pd-progression/spec.md`

## Summary
The project must ingest a pre‑processed 16S rRNA ASV table and longitudinal clinical metadata from the Parkinson’s Progression Markers Initiative (PPMI), filter to PD patients with ≥ 2 visits, apply a centered log‑ratio (CLR) transformation (with a pseudocount), compute per‑patient slopes for taxa abundances and **a longitudinal motor outcome** (UPDRS III *or* an alternative verified motor score such as `MDS_UPDRS_total`). If **neither** motor‑score column is present, the pipeline aborts with a clear error message, and the researcher must supply an open dataset that includes a suitable longitudinal motor outcome. All associations are evaluated via (1) Spearman correlation, (2) Linear Mixed‑Effects (LME) modeling with covariate adjustment, (3) Benjamini‑Hochberg (BH) FDR correction, and (4) a 1 000‑iteration permutation test that respects within‑patient temporal structure. A PDF report summarizing the top taxa and model diagnostics completes the deliverable set.

> **Data‑availability note** – The currently verified PPMI resources contain microbiome ASV counts and clinical covariates but **do not contain longitudinal UPDRS III scores**. They may, however, contain an alternative motor rating column such as `MDS_UPDRS_total`. The pipeline therefore:
> * Checks for the presence of either `UPDRS_partIII` **or** a verified alternative motor‑score column at runtime (Task 0.3).  
> * Proceeds only if one of these columns is found; otherwise it aborts with an informative error, prompting the researcher to provide an open dataset with a longitudinal motor outcome.

## Data Availability
The two verified PPMI datasets provide microbiome ASV counts and clinical covariates, **but they do not contain longitudinal UPDRS III scores**. An alternative motor‑score column (`MDS_UPDRS_total`) may be present. Consequently, the primary outcome variable required for FR‑004 and FR‑005 is unavailable unless one of these columns exists. The pipeline therefore:

* Checks for the presence of a motor‑score column at runtime (Task 0.3).  
* Proceeds only if the column is found; otherwise it aborts and reports the missing variable.  
* Allows the researcher to supply an alternative open dataset that includes a longitudinal motor outcome, provided the dataset is referenced by a verified URL and conforms to the required schema.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas==2.2.*`, `numpy==2.0.*`, `scikit‑bio==0.6.*` (for CLR), `statsmodels==0.14.*` (LME), `matplotlib==3.9.*`, `seaborn==0.13.*`, `pyyaml==6.0.*`, `reportlab==4.2.*` (PDF), `datasets==2.19.*` (HuggingFace dataset loading)  
**Storage**: File‑based CSV/TSV under `data/` (raw, processed, results)  
**Testing**: `pytest==8.2.*` with contract‑based validation (see `contracts/`)  
**Target Platform**: Linux CI runner (GitHub Actions free tier)  
**Performance Goals**: Entire pipeline ≤ 6 h wall‑clock on 2 CPU cores, ≤ 7 GB RAM  
**Constraints**: No GPU required; all steps must run on CPU.  
**Scale/Scope**: Full PPMI cohort (≈ 200 PD patients) but analysis will automatically subsample to the top 100 taxa if memory exceeds 7 GB.

## Power Considerations
After filtering for ≥ 2 visits, the cohort is expected to contain ≈ 30–60 patients (minimum requirement from the spec). Testing several hundred taxa with BH correction yields limited power to detect modest effect sizes. The study is thus framed as **hypothesis‑generating**; any significant findings will be interpreted cautiously and flagged for validation in larger cohorts.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are fixed (`np.random.seed(42)`, `statsmodels` seed). Data downloads use fixed HF revision tags. |
| II. Verified Accuracy | Only the two verified PPMI URLs are used for data ingestion. No unverified citations appear. |
| III. Data Hygiene | Raw files are stored read‑only under `data/raw/`. Every transformation writes a new file with a SHA‑256 checksum recorded in `state/projects/...yaml`. |
| IV. Single Source of Truth | Every number in the PDF report is generated directly from the CSV result files; no manual entry. |
| V. Versioning Discipline | All artifacts are version‑hashed; changes trigger `updated_at` timestamp updates. |
| VI. Microbiome Data Integrity | Raw ASV files are never altered; CLR output is saved under `data/processed/`. |
| VII. Statistical Rigor | Spearman, LME (via `statsmodels`), BH correction, and permutation test are implemented exactly as described. The permutation preserves within‑patient time ordering (see Phase 5). |

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
│   ├── ingest.py          # download & verify raw files
│   ├── preprocess.py      # filtering, CLR (with pseudocount)
│   ├── slopes.py          # per‑patient slopes
│   ├── correlation.py     # Spearman + BH
│   ├── mixed_effects.py   # LME fitting + BH
│   ├── permutation.py     # 1 000‑iteration block‑wise permutation
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
| **0 Data Acquisition** | 0.1 Download PPMI ASV zip & clinical parquet via verified HF URLs; verify checksums.<br>0.2 Log missing variables (e.g., `UPDRS_partIII` not present).<br>**0.3 Outcome Availability Check** – Verify that a longitudinal motor‑score column (`UPDRS_partIII` **or** a verified alternative such as `MDS_UPDRS_total`) exists; if neither is present, abort with an informative error. | FR‑001 (partial – ASV), **Data Availability** note |
| **1 Filtering & Transformation** | 1.1 Load ASV & clinical tables.<br>1.2 Retain PD patients with ≥ 2 visits; log exclusions (FR‑002).<br>1.3 Filter taxa with all‑zero counts; emit warning.<br>1.4 Add pseudocount = 1e‑6 to all counts and apply CLR transformation (FR‑003).<br>1.5 Write `data/processed/filtered_samples.parquet` and `data/processed/clr_abundances.parquet`. | FR‑002, FR‑003 |
| **2 Slope Computation** | 2.1 Compute linear slope of CLR‑taxon abundance per patient.<br>2.2 **If** a motor‑score column is present, compute per‑patient slope of that outcome; otherwise this step is skipped and downstream phases are not executed (FR‑004).<br>2.3 Write `data/processed/patient_taxon_slopes.parquet` and, when generated, `data/processed/patient_updrs_slopes.parquet`. | FR‑004 (conditional) |
| **3 Correlation Analysis** | 3.1 Spearman rank correlation between taxon‑slope and motor‑outcome slope (FR‑004, only if outcome present).<br>3.2 BH FDR correction across taxa (FR‑006).<br>3.3 Write `results/taxa_correlations.csv`. | FR‑004, FR‑006, SC‑001 |
| **4 Linear Mixed‑Effects Modeling** | 4.1 Fit LME: `Outcome ~ Time * Taxon + Age + Sex + Levodopa_Dose + (1|Patient)` (FR‑005, only if outcome present).<br>4.2 Extract interaction coefficient, SE, p‑value per taxon.<br>4.3 Apply BH correction (FR‑006).<br>4.4 Write `results/mixed_effects_summary.csv`. | FR‑005, FR‑006, SC‑001 |
| **5 Permutation Robustness** | 5.1 For each of 1 000 iterations, **block‑wise** permute residuals within each patient (preserving temporal autocorrelation) (FR‑007).<br>5.2 Re‑run LME on each permuted dataset, collect interaction p‑values.<br>5.3 Write `results/permutation_pvalues.csv`. (Skipped if outcome missing.) | FR‑007, SC‑002 |
| **6 Report Generation** | 6.1 Bootstrap 1 000 resamples of LME coefficients for CI (part of FR‑008).<br>6.2 Assemble ranked table of top 3 taxa with Spearman ρ, BH‑adjusted p, LME coefficient ± CI.<br>6.3 Insert methods paragraph explicitly stating “associational” nature (FR‑009).<br>6.4 Produce `results/PD_microbiome_progression_report.pdf`. (Generated only if outcome present.) | FR‑008, FR‑009, SC‑004, SC‑005 |
| **7 Resource Monitoring** | 7.1 Wrap each phase with a timer; abort if wall‑time > 4 h for permutation (SC‑003, Edge case). | SC‑003 |
| **8 Compliance & Logging** | 8.1 Record all provenance, checksums, seeds in `state/projects/...yaml` (Principles I, III, V). | All principles |

## Edge‑Case Handling
* Patients with a single visit → excluded, count logged (US‑1).  
* Taxa with all zeros → dropped before CLR, warning emitted (US‑1).  
* Zero‑variance covariates (e.g., levodopa dose) → detected, omitted from model, warning logged (US‑2).  
* **Missing motor outcome** → pipeline aborts early with clear error (Task 0.3).  
* Permutation runtime breach → graceful abort, partial results saved, runtime breach reported (US‑4).  

## Compute Feasibility
All steps are pure CPU; the most demanding step is the permutation test. Preliminary benchmarks on a multi‑core, 7 GB runner indicate a few hours for a substantial number of permutations on a moderate number of taxa (vectorized `statsmodels` calls). If the full taxon set exceeds memory, the pipeline automatically limits to the 100 most abundant taxa (FR‑010).

---

