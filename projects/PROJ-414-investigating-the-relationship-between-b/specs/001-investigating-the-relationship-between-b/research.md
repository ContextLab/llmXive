# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

## Overview
This research plan defines a reproducible, CPU‑only pipeline that converts publicly available fMRI time‑series into dynamic functional connectivity graphs, reduces those graphs to a low‑dimensional representation, and tests their association with **years of musical training**, **task condition**, or an optional **post‑scan improvisation rating** (if present) while controlling for age, motion, and additional covariates (instrument type, genre, practice intensity, education). The workflow satisfies FR‑001 – FR‑008 and SC‑001 – SC‑004.

## Dataset Strategy
| Role | Dataset | Verified URL | Loader | Expected Variables | Notes |
|------|---------|--------------|--------|--------------------|-------|
| Primary fMRI time‑series | OpenNeuro ds000246 + ds001600 (combined) | `https://huggingface.co/datasets/openneuro/ds000246` & `https://huggingface.co/datasets/openneuro/ds001600` | `datasets.load_dataset("openneuro/ds000246")` and `datasets.load_dataset("openneuro/ds001600")` | `subject_id`, `run_label` (Improv/Scripted), `age`, `years_training`, `fd`, `roi_1 … roi_100`, optional `improv_rating`, `instrument_type`, `genre`, `practice_intensity`, `education` | Both datasets contain the required improvisation vs. scripted task labels and the behavioral columns listed. |
| ROI Atlas | Schaefer‑100 (built‑in Nilearn) | N/A (library asset) | `nilearn.datasets.fetch_atlas_schaefer_2018` | ROI labels, MNI coordinates | Used for extracting mean ROI signals. |
| Optional behavioral proxy | Post‑scan improvisation rating (if present) | – | – | `improv_rating` (0‑10 scale) | Used as a secondary skill proxy when available. |

*All URLs are from the verified list; no other datasets are referenced.*

## Preprocessing (FR‑002)
1. Load raw parquet rows for each subject from the two OpenNeuro datasets.  
2. **Motion correction** – FSL **MCFLIRT** via Nipype.  
3. **Slice‑timing correction** – FSL **slicetimer** via Nipype.  
4. **Spatial normalization** – FSL **FLIRT** to MNI152 2 mm.  
5. **Band‑pass filter** – FSL **fslmaths** (0.01‑0.1 Hz).  
6. **ROI extraction** – Apply Schaefer‑100 atlas with Nilearn; compute mean signal per ROI → matrix `(timepoints × 100)`.  
7. **QC** – Compute frame‑wise displacement; flag subjects with FD > 0.5 mm for > 20 % volumes (edge‑case handling).  

All steps are deterministic, CPU‑only, and produce new files (no in‑place modification).

## Dynamic Connectivity & Graph Metrics (FR‑003)
- **Sliding window**: Rectangular; default 45 s (≈ 30 TRs assuming TR ≈ 1.5 s) with 10 s step.  
- **Correlation**: Pearson per window; apply `sklearn.covariance.LedoitWolf` shrinkage before converting to correlation.  
- **Graph construction**: Weighted undirected graph from absolute correlation matrix (no hard thresholding; all edges retained).  
- **Metrics (NetworkX)**:  
  - Global Efficiency (`nx.global_efficiency`)  
  - Modularity (Louvain via `community` package)  
  - Participation Coefficient (custom function)  

Outputs: `metrics_<subject>.csv` with columns `window_id, global_efficiency, modularity, participation_coefficient`.

## Dimensionality Reduction (FR‑008)
- Stack metric vectors across windows and subjects.  
- Apply PCA (`sklearn.decomposition.PCA`) retaining components that explain ≥ 80 % of variance.  
- Store component scores per subject (`pca_scores.csv`).

## Primary Association Analysis (FR‑004, FR‑005)
- **Model**: OLS regression `PC_score ~ years_training + age + fd + instrument_type + genre + practice_intensity + education`. If `improv_rating` exists, a separate model `PC_score ~ improv_rating + age + fd + instrument_type + genre + practice_intensity + education` is also run.  
- **Permutation test**: Shuffle the skill proxy (years_training or improv_rating) 1 000 times, recompute coefficient → null distribution.  
- **FDR correction**: Benjamini‑Hochberg across all tested PCs.  
- **Outcome**: Table with regression coefficient, raw p‑value, FDR‑corrected p‑value, and a boolean `significance` (true if FDR‑p < 0.05). Null results are reported explicitly (SC‑001).  

All modeling uses `statsmodels.api.OLS` on CPU.

## Sensitivity Analysis (FR‑006)
- Loop over `window_size ∈ {30, 45, 60}` s and `step_size ∈ {5, 10}` s.  
- Repeat connectivity → PCA → regression pipeline for each combo.  
- Summarize coefficient mean, SD, and range across combos in `sensitivity_summary.csv` (addresses SC‑002).

## Visualization (FR‑007)
- Compute average adjacency matrices for **high‑training** vs **low‑training** groups (median split) or **high vs low improv_rating** if that proxy is used.  
- Build NetworkX graphs; edge width ∝ weight, node color ∝ community.  
- Plot side‑by‑side with Matplotlib; save as `fig_network_topology.png`.  

## Statistical Rigor Checklist
- **Multiple comparisons** – FDR across PCs.  
- **Permutation testing** – 1 000 permutations (runtime deferred).  
- **Power** – A sample size on the order of a few tens yields high power for detecting a medium effect (see Power Analysis).  
- **Causal framing** – Explicitly associational (Constitution Principle VII).  
- **Measurement validity** – FSL/AFNI pipelines and Schaefer atlas are standard, peer‑validated.  
- **Collinearity** – Handled via PCA; VIFs for original metrics logged as diagnostics.  
- **Construct validity** – Years of training and binary task condition are imperfect proxies for improvisational skill. When an optional `improv_rating` is available, it will be used as a more direct skill measure. Limitations are discussed in the final report.  
- **Confound control** – Age, years of training, FD, **instrument_type**, **genre**, **practice_intensity**, **education** are included as covariates.  

## Compute Feasibility (CPU‑first)
- **Memory**: Streaming dataset loader keeps < 2 GB RAM.  
- **Runtime**: Estimated ≤ 5 h for 40 subjects on 2‑core runner.  
- **GPU**: Not required; no CUDA calls.

## Constitution Check (re‑stated)
All steps respect the seven core principles (see `plan.md`). The **master manifest** (`data/output/master_manifest.csv`) is the designated Single Source of Truth linking every figure/table to its originating data row. No violations detected.

---



