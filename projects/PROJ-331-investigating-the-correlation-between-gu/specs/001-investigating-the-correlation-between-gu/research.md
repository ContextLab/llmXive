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
* **Memory Management** – Random subsampling of taxa (seeded) prevents deterministic bias while respecting the RAM guard (FR‑010).  
* **Statistical Rigor** – Partial Spearman (rank‑based) replaces residualization, providing a proper covariate‑adjusted correlation. The LME includes additional optional covariates when available. Both analyses receive Benjamini‑Hochberg correction and a permutation robustness check.  
* **Power Considerations** – A brief power limitation statement is included in the final PDF (see Phase 6).  
* **Reproducibility** – Fixed random seeds, deterministic file paths, and checksum verification guarantee identical results on a fresh runner.

## Expected Deliverables
| File | Description |
|------|-------------|
| `results/taxa_correlations.csv` | Taxon, partial Spearman ρ (adjusted for covariates), raw p‑value, BH‑adjusted p‑value (covers FR‑004, SC‑001, SC‑006). |
| `results/mixed_effects_summary.csv` | Taxon, interaction coefficient, SE, raw p‑value, BH‑adjusted p‑value (covers FR‑005, SC‑001). |
| `results/permutation_pvalues.csv` | Taxon, empirical p‑value from block‑wise patient‑ID shuffling (covers FR‑007, SC‑002). |
| `results/PD_microbiome_progression_report.pdf` | Ranked table of the top taxa with bootstrap 95 % CIs for LME coefficients, plus a methods paragraph stating that all findings are **associational** and acknowledging limited power (covers FR‑008, FR‑009, SC‑004, SC‑005). |

---

