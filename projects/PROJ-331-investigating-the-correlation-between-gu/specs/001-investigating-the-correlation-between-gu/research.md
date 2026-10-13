# Research: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

## Objective
Identify gut microbial taxa whose longitudinal abundance trajectories are associated with the rate of change in Parkinson’s disease motor severity (UPDRS III or an alternative motor score), while adjusting for age, sex, and levodopa equivalent dose.

## Dataset Strategy
| Role | Source | Access Method | Variables Provided | Notes |
|------|--------|---------------|--------------------|-------|
| Microbiome ASV | **Researcher‑provided** (CSV/TSV) | Place file at `data/raw/ppmi_asv.csv` | Taxon counts per sample (pre‑processed) | No open‑access PPMI ASV dataset is verified; the pipeline will abort with a clear error if this file is missing. |
| Clinical metadata (age, sex, levodopa dose, visit dates, motor outcome) | **Researcher‑provided** (Parquet) | Place file at `data/raw/ppmi_clinical.parquet` | `patient_id`, `visit_date`, `age`, `sex`, `levodopa_eq_dose`, **required** motor score column (`UPDRS_partIII` **or** `MDS_UPDRS_total`) | No verified open PPMI clinical dataset is available; the pipeline will abort if neither motor‑score column is present. |
| Motor outcome (UPDRS Part III **or** alternative `MDS_UPDRS_total`) | **Embedded in the clinical parquet** (see above) | — | `UPDRS_partIII` or `MDS_UPDRS_total` | Required for slope computation and LME; absence triggers an informative abort. |

### Data Availability Gap
The specification calls for PPMI microbiome and clinical data, but no open‑access source for the gut‑microbiome ASV table or the longitudinal motor scores is currently verified. Researchers must supply these files in the locations described above before running the pipeline.

## Decision / Rationale
* **Method Choice** – All statistical steps (Spearman, partial‑Spearman, LME, BH, permutation) are fully CPU‑tractable; they will run on the GitHub Actions free tier without GPU.  
* **Memory Management** – Automatic subsampling to the top 100 most abundant taxa prevents RAM overflow (FR‑010).  
* **Statistical Rigor** – Spearman correlation (exploratory), LME (covariate‑adjusted), BH (FDR control), and permutation (empirical null) together provide a robust inferential framework.  
* **Reproducibility** – Fixed seeds, deterministic data loading, and checksum verification guarantee identical outputs on a fresh runner.

## Expected Deliverables
| File | Description |
|------|-------------|
| `results/taxa_correlations.csv` | Taxon, Spearman ρ, raw p, BH‑adjusted p (exploratory) |
| `results/mixed_effects_summary.csv` | Taxon, interaction coefficient, SE, raw p, BH‑adjusted p |
| `results/permutation_pvalues.csv` | Taxon, empirical p‑value from 1 000 permutations |
| `results/PD_microbiome_progression_report.pdf` | Ranked top taxa, confidence intervals, methods paragraph, explicit associational framing |

---

