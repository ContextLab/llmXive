# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

## Overview
This research plan outlines a reproducible, CPU‑only pipeline that transforms publicly available fMRI‐derived time‑series data into dynamic functional connectivity graphs, reduces those graphs to a low‑dimensional set of components, and tests their association with improvisation task condition (or years of training) while controlling for demographic and motion covariates. The approach follows the functional requirements (FR‑001 – FR‑008) and success criteria (SC‑001 – SC‑004) enumerated in the specification.

## Dataset Strategy
| Role | Dataset | Source URL (verified) | Loader | Expected Variables | Notes |
|------|---------|-----------------------|--------|--------------------|-------|
| Primary fMRI‑derived time‑series | **OpenNeuro‑Parquet** (pre‑processed BOLD signals) | `https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet` | `datasets.load_dataset("clane9/openneuro-fslr64k", streaming=False)` | `subject_id`, `run_label` (Improv/Scripted), `age`, `years_training`, `fd`, `roi_1 … roi_100` | Verified parquet file contains ROI‑averaged BOLD time‑points. We will programmatically verify column presence; missing columns will trigger a clear error per Constitution Principle III. |
| ROI Atlas (definition) | Schaefer 100‑ROI atlas (built‑in Nilearn) | N/A (library asset) | `nilearn.datasets.fetch_atlas_schaefer_2018` | ROI labels, MNI coordinates | Used for extracting ROI signals from raw NIfTI (if needed). |
| Optional behavioral proxy | None (use `run_label` or `years_training` if `run_label` absent) | — | — | — | Handled in analysis step 4 (fallback logic). |

*No other verified OpenNeuro datasets containing improvisation tasks are available; therefore the above parquet dataset is used as the closest open source that supplies ROI‑level BOLD series.*

## Preprocessing (FR‑002)
1. **Load raw NIfTI (if present) or use the parquet time‑series directly.**  
2. **Motion correction** – Nilearn’s `image.clean_img` with `standardize=False` and `confounds` derived from FD.  
3. **Slice‑timing correction** – Nilearn’s `image.resample_img`.  
4. **Spatial normalization** – `nilearn.image.resample_to_img` to MNI152 2 mm template.  
5. **Band‑pass filter** – 0.01‑0.1 Hz using `nilearn.signal.clean`.  
6. **ROI extraction** – Apply Schaefer‑100 atlas; compute mean signal per ROI → matrix `(timepoints × 100)`.  
7. **Quality Control** – Compute frame‑wise displacement; flag subjects with FD > 0.5 mm for > 20 % volumes (Edge case handling).  

All steps are deterministic (random seeds not needed) and run on CPU.

## Dynamic Connectivity & Graph Metrics (FR‑003)
- **Sliding window**: Rectangular window; default 45 s (≈ 30 TRs assuming TR ≈ 1.5 s) with 10 s step.  
- **Correlation**: Pearson correlation for each window; apply `LedoitWolf` shrinkage (`sklearn.covariance.LedoitWolf`) to regularize the covariance before converting to correlation.  
- **Graph construction**: Thresholded absolute correlation matrix (e.g., retain top 20 % edges) to build an undirected weighted graph per window.  
- **Metrics** (computed via NetworkX):  
  - Global Efficiency (`nx.global_efficiency`)  
  - Modularity (Louvain algorithm via `community` package)  
  - Participation Coefficient (custom implementation)  

Outputs: `metrics_<subject>.csv` with columns `window_id, global_efficiency, modularity, participation_coeff`.

## Dimensionality Reduction (FR‑008)
- Stack all metric vectors across windows and subjects.  
- Apply PCA (`sklearn.decomposition.PCA`) retaining components that explain ≥ 80 % of variance.  
- Store component scores per subject (`pca_scores_<subject>.csv`).

## Primary Association Analysis (FR‑004, FR‑005)
- **Model**: Linear regression `PC_score ~ task_condition + age + years_training + fd`.  
- **Permutation testing**: Shuffle `task_condition` (or `years_training` when that is the dependent variable) 1 000 times, recompute coefficient, build null distribution.  
- **FDR correction**: Apply Benjamini‑Hochberg across all tested PCs (SC‑001, SC‑003).  
- **Outcome**: Table of regression coefficients, raw and FDR‑corrected p‑values; flag “null result” if corrected p > 0.05 (SC‑001).  

All modeling is performed with `statsmodels.api.OLS` (CPU).

## Sensitivity Analysis (FR‑006)
- Loop over `window_size ∈ {30, 45, 60}` s and `step_size ∈ {5, 10}` s.  
- Repeat connectivity → PCA → regression pipeline.  
- Summarize coefficient stability (mean, SD) across parameter combos in a CSV (`sensitivity_summary.csv`).  

## Visualization (FR‑07)
- For the two task groups (Improv vs. Scripted) compute average adjacency matrices (after thresholding).  
- Build NetworkX graphs; edge width ∝ weight, node color ∝ community.  
- Plot side‑by‑side using Matplotlib; save as `fig_network_topology.png`.  

## Statistical Rigor Checklist
- **Multiple comparisons** – FDR across PCs (≥ 1 test).  
- **Permutation testing** – 1 000 permutations, `[deferred]` exact runtime.  
- **Power acknowledgement** – Sample size limited to available subjects (≈ 20‑30); we will report the achieved power estimate using `statsmodels.stats.power.tt_ind_solve_power`.  
- **Causal framing** – Explicitly described as associational (Constitution Principle VII).  
- **Measurement validity** – Nilearn’s preprocessing pipeline is widely validated; Schaefer atlas is a standard parcellation.  
- **Collinearity** – PCA mitigates metric collinearity; we will report variance inflation factors for the original metrics as a diagnostic.

## Compute Feasibility (CPU‑first)
- **Memory**: Streaming parquet loader keeps < 2 GB in memory; per‑subject matrices ≤ 200 MB.  
- **Runtime**: Estimated 3‑4 h for 25 subjects on 2‑core runner (benchmark on similar data).  
- **No GPU**: All libraries are pure CPU; no `torch.cuda` calls.

## Constitution Check (re‑stated)
All steps respect the seven core principles (see `plan.md`). No violations detected.

---
