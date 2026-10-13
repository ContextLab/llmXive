# Research: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

## Objective
Identify gut microbial taxa whose longitudinal abundance trajectories are associated with the rate of change in Parkinson’s disease motor severity (MDS‑UPDRS total), while adjusting for age, sex, and levodopa equivalent dose.

## Dataset Strategy
| Role | Source | Access Method | Variables Provided | Notes |
|------|--------|---------------|--------------------|-------|
| Microbiome ASV | **Open, verified dataset** (to be selected by the research team) | Programmatic download via `datasets.load_dataset` or direct URL (must be a publicly reachable CSV/TSV) | `sample_id`, `patient_id`, `visit_date`, raw count columns for each taxon | The original PPMI ASV table is not publicly available; an open substitute must be identified and cited. |
| Clinical metadata | **Open, verified dataset** (paired with the ASV source) | Programmatic download via `datasets.load_dataset` or direct URL (Parquet or CSV) | `patient_id`, `visit_date`, `age`, `sex`, `levodopa_eq_dose`, **required** `MDS_UPDRS_total` | The original PPMI clinical file is gated; an open substitute must be identified and cited. |
| Additional reference data (optional) | **None** – all analysis uses the two files above. | — | — | — |

### Data Availability Gap
The specification originally required PPMI microbiome and clinical data, but no publicly verified version of these files exists. Researchers must supply an **open, verifiable dataset** that contains both microbiome ASV counts and longitudinal UPDRS scores. Until such a dataset is identified and its URL added to the repository, the pipeline will abort with an informative error, preserving reproducibility (Constitution I).

## Decision / Rationale
* **Method Choice** – All statistical steps (covariate‑adjusted Spearman, LME, BH, permutation) are fully CPU‑tractable; they run on the GitHub Actions free tier without GPU.  
* **Memory Management** – Automatic subsampling to the top 100 most abundant taxa prevents RAM overflow (FR‑010).  
* **Statistical Rigor** – Covariate‑adjusted Spearman correlation provides an exploratory association that respects the confounder control demanded by User Story 1; the LME model supplies covariate‑adjusted effect estimates; BH controls the false discovery rate; permutation on model residuals supplies an empirical null distribution. Together they satisfy the required inferential robustness.  
* **Reproducibility** – Fixed seeds, deterministic data loading, and checksum verification guarantee identical outputs on a fresh runner.  
* **Power Considerations** – A brief analytic power calculation (see Implementation Plan) indicates modest power for correlations of modest magnitude with a limited sample size after BH correction; this limitation is reported in the final PDF.  

## Expected Deliverables
| File | Description |
|------|-------------|
| `results/taxa_correlations.csv` | Taxon, covariate‑adjusted Spearman ρ, raw p‑value, BH‑adjusted p‑value (exploratory). |
| `results/mixed_effects_summary.csv` | Taxon, interaction coefficient, SE, raw p‑value, BH‑adjusted p‑value (covariate‑adjusted). |
| `results/permutation_pvalues.csv` | Taxon, empirical p‑value from several thousand permutations of model residuals. |
| `results/PD_microbiome_progression_report.pdf` | Ranked top taxa, bootstrap confidence intervals for LME coefficients, methods paragraph stating “associational” nature. |

---

