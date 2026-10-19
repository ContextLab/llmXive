# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

## Overview
A fully reproducible, CPU‑only analysis pipeline that:

1. Downloads the **only verified OpenNeuro fMRI parquet shard** (e.g., `clane*/openneuro-fslr64k`).  
2. Generates **Schaefer 100‑ROI** time‑series, band‑pass filters (0.01–0.1 Hz), and flags high‑motion subjects.  
3. Computes sliding‑window Ledoit‑Wolf functional connectivity and derives **ROI‑based graph metrics** (global efficiency, modularity, participation coefficient).  
4. Reduces the descriptor space with PCA.  
5. Performs a **statsmodels‑based** a‑priori power analysis for a medium effect size (f² = 0.15).  
6. **Conditionally** runs a Freedman‑Lane permutation regression of the PCs on the best available skill proxy (expert rating > years of training) while controlling for all present covariates. If no proxy exists, the regression stage is skipped and a clear log entry is recorded.  
7. Sweeps window/step parameters for robustness.  
8. Visualizes network topology with NetworkX/Matplotlib (group comparison only if real task labels exist).  
9. Writes a master manifest (`results/manifest.csv`) that is the Single Source of Truth.

**Critical limitation**: The verified OpenNeuro parquet shard **lacks any skill‑proxy columns** (expert_rating, task_condition, years_of_training, instrument_type, musical_genre, practice_intensity, education_level). Therefore the primary association analysis (Phase [later stage]) will be **skipped** for this dataset, and the study will provide a **descriptive analysis of dynamic ROI‑based connectivity** plus a transparent limitation statement. Future work should acquire an open dataset with expert improvisation ratings to test the core hypothesis.

## Dataset Strategy

| Role | Dataset | Verified URL | Loader | Expected Variables | Notes |
|------|---------|--------------|--------|--------------------|-------|
| Primary fMRI timeseries | OpenNeuro fsLR‑high‑resolution parquet mirror (test split shard 1 of 16) | `https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet` | Direct download via `huggingface_hub.hf_hub_download`; streamed with `pyarrow` | BOLD timeseries on fsLR 64k surface; subject/run IDs; motion columns | **Only verified source**. No expert rating, task condition, years of training, instrument, genre, practice intensity, or education columns – pipeline records this limitation. |
| ROI atlas | Schaefer high‑resolution ROI atlas (7‑networks) | `https://github.com/ThomasYeoLab/CBIG/tree/master/stable_projects/brain_parcellation/Schaefer2018_100Parcels_7Networks` (downloaded via `nilearn.datasets.fetch_atlas_schaefer_2018`) | `nilearn.datasets.fetch_atlas_schaefer_2018` | ROI definitions for 100 parcels | Verified, programmatically downloadable; satisfies Principle VI after amendment. |
| FSL / AFNI tools | — | — | — | — | Not used; preprocessing performed with Nilearn (CPU‑only) pending constitution amendment. |

### Dataset‑Variable Fit
The spec’s ideal variables (expert blind‑rating scores, years of training, instrument type, genre, practice intensity, education level, task condition) are **absent** from the verified dataset. The pipeline therefore:

- Performs a **data‑inventory step** (`data/raw/column_inventory.json`) that records which of these columns are actually present.
- Executes the association analysis **only if** a real skill‑proxy column is found; otherwise it logs a clear “no skill proxy” message and records `skill_proxy_used = "none"` in the manifest.
- **Never fabricates** behavioral scores or substitutes other datasets.

## Preprocessing (FR‑002 – Python adaptation)

1. **Streaming download** – `download_openneuro.py` streams the parquet file row‑group by row‑group; computes SHA‑256 and stores in `data/checksums.json`.  
2. **Schaefer ROI extraction** – `extract_rois.py` fetches the Schaefer 100‑ROI atlas via Nilearn, maps each vertex to an ROI, and computes the mean BOLD per ROI for each subject/run; writes `data/derived/roi_timeseries_<subject>.csv` adhering to `roi_timeseries.schema.yaml`.  
3. **Band‑pass & detrending** – Butterworth filter (0.01–0.1 Hz) via `scipy.signal`; detrending with linear fit.  
4. **QC & exclusion** – compute a simple amplitude‑based outlier metric; if >20 % of volumes exceed the outlier threshold, flag the subject as excluded and record the reason in `data/derived/qc_<subject>.json`. This satisfies the edge‑case requirement.

*No FSL/AFNI commands are run; the preprocessing is performed with CPU‑only Nilearn utilities, an amendment‑pending but reproducible alternative.*

## Dynamic Connectivity & ROI‑Based Metrics (FR‑003)

- **Sliding window**: rectangular window, default 45 s (converted to TRs via dataset’s TR), step 10 s; windows with <30 timepoints are discarded.  
- **Estimator**: `sklearn.covariance.LedoitWolf` (shrinkage) applied to the ROI time‑series in each window, then converted to Pearson correlation.  
- **Graph construction**: absolute correlation matrix → weighted undirected graph (no thresholding).  
- **Metrics** (computed with `networkx`):  
  - Global efficiency (`nx.global_efficiency`).  
  - Modularity via Louvain (`nx.community.louvain_communities`, fixed seed).  
  - Participation coefficient (standard formula over Louvain communities).  
- Output files `data/derived/metrics_<subject>.csv` conform to `network_metrics.schema.yaml`.

All metric names are explicitly labeled **“ROI‑based connectivity descriptor”** to avoid misinterpretation as whole‑brain network properties.

## Dimensionality Reduction (FR‑008)

`dimensionality.py` stacks all per‑window descriptors, runs `sklearn.decomposition.PCA` (seeded), retains the smallest number of components that explain ≥ 80 % of variance, and writes `results/pca_scores.csv` matching `pca_scores.schema.yaml`.

## Power Analysis (FR‑010, SC‑005)

`analysis.py` performs an a‑priori power calculation **using `statsmodels.stats.power.FTestPower`** with a medium effect size f² = 0.15 (Cohen’s medium for regression). Parameters: `df_num=1`, `alpha=0.05`, `power=0.8`, `df_denom=available_N - n_covariates - 2`. Required N is compared to the available subject count from the inventory. The JSON result (`results/power_analysis.json`) contains:

```json
{
  "required_n": <int>,
  "available_n": <int>,
  "status": "adequate" | "underpowered_association_skipped"
}
```

If under‑powered, **only Phase 5 (association) aborts**; all other phases still run.

## Conditional Association Analysis (FR‑004, FR‑005, FR‑009, FR‑011, SC‑001, SC‑003)

1. **Skill‑proxy selection** (priority order):  
   - `expert_rating` column (if present)  
   - `years_of_training` column (if present)  
   - If none exist → log “no skill proxy” and write `skill_proxy_used = "none"` in the manifest.  
2. **Model**: OLS regression `PC_score ~ skill_proxy + age + fd + instrument_type + musical_genre + practice_intensity + education_level`. Covariates are **included only when present** (as recorded in the column inventory).  
3. **Freedman‑Lane permutation**: 1000 seeded residual permutations (valid under covariate adjustment).  
4. **Multiple‑comparison correction**: Benjamini‑Hochberg FDR across all retained PCs.  
5. **Outputs**: `results/regression_results.csv` adhering to `regression_results.schema.yaml`. Null results (p > 0.05) are flagged but not treated as failures.

All statistical statements are **associational**; no causal claims are made (Constitution VII).

## Sensitivity Analysis (FR‑006, SC‑002)

`sensitivity.py` repeats Phases 2–3 (and Phase 5 if it ran) for the six combinations:

| Window (s) | Step (s) |
|------------|----------|
| 30 | 5 |
| 30 | 10 |
| 45 | 5 |
| 45 | 10 |
| 60 | 5 |
| 60 | 10 |

For each combination it records mean/SD of the three metrics and, when Phase 5 ran, the correlation coefficient between the skill proxy and each PC. Results are saved in `results/sensitivity_summary.csv`. If no skill proxy exists, the correlation fields are set to `not_computable_no_skill_proxy`.

## Visualization (FR‑007)

`visualization.py`:

- **If task labels exist**: compute mean adjacency per condition, construct NetworkX graphs, render with Matplotlib (edge width ∝ weight, node color ∝ Louvain community). Save `results/fig_network_topology.png` with a caption indicating the comparison.  
- **If no task labels** (expected): render a **single‑group descriptive topology** of the mean ROI‑based graph, clearly labeled as “descriptive ROI‑based connectivity topology – no group comparison”.  

All figures are saved as PNG and referenced in the final report.

## Decision / Rationale (Compute Feasibility)

- **CPU‑first**: All steps use CPU‑compatible libraries; streaming ensures RAM stays < 2 GB.  
- **Why direct parquet download**: `datasets.load_dataset("openneuro/ds000246")` does not exist; the verified parquet URL is the only programmatically accessible source.  
- **Why Schaefer atlas**: Provides a standard, neuroanatomically meaningful parcellation with a verified download mechanism, satisfying Principle VI after amendment.  
- **Why re‑scoping**: The essential dependent variable (expert improvisation rating) is unavailable; the honest primary deliverable is a descriptive analysis of ROI‑based dynamics, with the full association machinery implemented but expected to halt. This respects the “no fabrication” rule.

## Statistical Rigor Checklist

- **Multiple comparisons**: BH‑FDR across PCs (FR‑005, SC‑003).  
- **Permutation testing**: 1000 Freedman‑Lane residual permutations (seeded).  
- **Power analysis**: `statsmodels.stats.power.FTestPower` with effect size f² = 0.15, aborts only the association stage if under‑powered (SC‑005).  
- **Causal framing**: strictly associational.  
- **Measurement validity**: Schaefer atlas is a widely validated parcellation; ROI‑based descriptors are clearly labeled as such.  
- **Collinearity**: PCA handles correlated descriptors; components are not interpreted as independent effects.  
- **Confound control**: All available covariates are included; missing covariates are omitted and noted.  

## Constitution Check

All seven principles are addressed in this document. The deviations (absence of FSL/AFNI, use of Schaefer atlas) are routed through the amendment process. No silent violations remain.

---


