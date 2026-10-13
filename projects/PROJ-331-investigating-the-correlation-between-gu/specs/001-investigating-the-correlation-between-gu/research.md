# Research: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

## Objective
Identify gut microbial taxa whose longitudinal abundance trajectories are associated with the rate of change in Parkinson’s disease motor severity (UPDRS III or an alternative motor score), while adjusting for age, sex, and levodopa equivalent dose.

## Dataset Strategy
| Role | Source | Access Method | Variables Provided | Notes |
|------|--------|---------------|--------------------|-------|
| Microbiome ASV | **[A verified open microbiome ASV dataset is required]** | *To be supplied by the researcher* (e.g., a HuggingFace dataset with a CSV/TSV count matrix) | Taxon counts per sample | No verified open source currently listed; the specification must be updated with a suitable dataset. |
| Clinical metadata (age, sex, levodopa dose, visit dates) | PPMI (parquet) | `datasets.load_dataset("mcbuehler/pp_mixed_v0", data_dir="data/raw")` | `patient_id`, `visit_date`, `age`, `sex`, `levodopa_eq_dose` | Verified URL: https://huggingface.co/datasets/mcbuehler/pp_mixed_v0/resolve/main/data/chunk-000/file-000.parquet |
| Motor outcome (UPDRS Part III **or** a verified alternative such as `MDS_UPDRS_total`) | **Not available in any verified open dataset** | — | `UPDRS_partIII` (or alternative) | No verified source; the pipeline will abort with a clear error if neither column is present. The researcher must provide an open dataset that includes a longitudinal motor outcome for the analysis to run. |

### Data Availability Gap
The specification requires longitudinal UPDRS III motor scores, which are absent from the two verified PPMI resources. Consequently, the primary outcome variable cannot be computed directly. Options:

1. **Provide an open substitute** (e.g., a publicly released PD motor rating dataset that includes longitudinal scores).  
2. **Revise the analysis** to use an alternative outcome that is available in the verified data (e.g., `MDS_UPDRS_total` if present).

The current plan proceeds under the assumption that a suitable motor‑score column will be supplied; all pipeline steps that depend on it raise an informative error if the column is missing.

## Decision / Rationale
* **Method Choice** – All statistical analyses (Spearman, LME, BH, permutation) are CPU‑tractable and will run on the GitHub Actions runner. No GPU is required.  
* **Memory Management** – Automatic subsampling to the top [limited] taxa prevents RAM overflow.  
* **Statistical Rigor** – Spearman correlation respects the non‑parametric nature of slope estimates. LME accounts for repeated measures and covariates. BH controls the false discovery rate. Permutation preserves the longitudinal structure, providing an empirical null.  
* **Reproducibility** – Fixed seeds, deterministic data loading, and checksum verification guarantee that re‑runs on a fresh runner reproduce identical outputs.

## Expected Deliverables
| File | Description |
|------|-------------|
| `results/taxa_correlations.csv` | Taxon, Spearman ρ, raw p, BH‑adjusted p |
| `results/mixed_effects_summary.csv` | Taxon, interaction coefficient, SE, raw p, BH‑adjusted p |
| `results/permutation_pvalues.csv` | Taxon, empirical p‑value from a large set of permutations |
| `results/PD_microbiome_progression_report.pdf` | Ranked top taxa, confidence intervals, methods paragraph, explicit associational framing |

---

