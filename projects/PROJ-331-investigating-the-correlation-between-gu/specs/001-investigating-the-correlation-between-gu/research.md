# Research: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

## Objective
Identify gut microbial taxa whose longitudinal abundance trajectories are associated with the rate of change in Parkinson’s disease motor severity (MDS‑UPDRS total), while adjusting for age, sex, and levodopa equivalent dose.

## Dataset Strategy
| Role | Source | Access Method | Variables Provided | Notes |
|------|--------|---------------|--------------------|-------|
| Microbiome ASV | **None currently verified** that contains both 16S counts *and* longitudinal clinical scores. | – | – | The original PPMI ASV files are gated; an open substitute must be supplied by the researcher. |
| Clinical metadata | **None currently verified** for MDS‑UPDRS total. | – | – | The UPDRS column is absent from all verified datasets; the researcher must provide a CSV/Parquet file with the required columns. |
| Optional auxiliary data | – | – | – | No auxiliary datasets are needed for the core analysis. |

### Data Availability Gap
The specification requests PPMI microbiome and clinical data, but no open, programmatically downloadable version of these files exists in the verified list. Consequently, the pipeline **requires the researcher to place** the following files in `data/raw/` before execution:

1. `data/raw/open_asv.csv` – a CSV with columns `sample_id`, `patient_id`, `visit_date`, and one column per taxon containing raw integer counts.  
2. `data/raw/open_clinical.parquet` – a Parquet file with columns `patient_id`, `visit_date`, `age`, `sex`, `levodopa_eq_dose`, **MDS_UPDRS_total**.

If either file or any required column is missing, the pipeline aborts with an informative error; no synthetic data are generated. This design satisfies Constitution I (reproducibility) by refusing to fabricate or silently substitute data.

**Resolution of Panel Concern (data_resources‑388aa01b)**  
The requirement for the gated PPMI dataset cannot be satisfied with an openly downloadable source. This is a limitation of the source specification rather than the plan itself. The plan now explicitly documents this limitation and flags the specification for revision: either an open dataset that includes both microbiome ASV counts and longitudinal clinical scores must be identified, or FR‑001 must be adjusted to accept user‑provided files. Until such a revision, the pipeline will abort with an informative error if the required inputs are missing.

## Decision / Rationale
* **Method Choice** – All statistical steps (plain Spearman, LME, BH correction, permutation) are fully CPU‑tractable and fit comfortably within the GitHub Actions free‑tier limits. No GPU is required.  
* **Memory Management** – Automatic subsampling to a limited set of the most abundant taxa prevents RAM overflow (FR‑010).  
* **Statistical Rigor** – The primary Spearman analysis follows FR‑004 exactly (no covariate adjustment). Covariate‑adjusted Spearman is offered only as an optional supplemental file. The LME model provides robust effect estimates, BH controls the false discovery rate, and permutation supplies an empirical null distribution, collectively meeting the robustness requirement (Story 3).  
* **Reproducibility** – Fixed random seeds, deterministic file paths, and checksum verification guarantee identical outputs on a fresh runner.  
* **Power Considerations** – A brief analytic power calculation (see Implementation Plan) is reported in the final PDF; the limitation of modest sample size after BH correction is acknowledged.  

## Expected Deliverables
| File | Description |
|------|-------------|
| `results/taxa_correlations.csv` | Taxon, Spearman ρ, raw p‑value, BH‑adjusted p‑value (plain correlation, FR‑004). |
| `results/mixed_effects_summary.csv` | Taxon, interaction coefficient, SE, raw p‑value, BH‑adjusted p‑value (covariate‑adjusted). |
| `results/permutation_pvalues.csv` | Taxon, empirical p‑value derived from patient‑ID shuffling permutations (no BH adjustment). |
| `results/PD_microbiome_progression_report.pdf` | Ranked the highest‑ranking taxa with bootstrap 95 % CIs for LME coefficients, plus a methods paragraph stating that all findings are “associational”. |

---



