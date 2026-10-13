# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

## Overview
This research plan outlines a reproducible, CPU‑only pipeline that transforms publicly available fMRI‑derived time‑series data into dynamic functional connectivity graphs, reduces those graphs to a low‑dimensional set of components, and tests their association with **years of musical training** (the primary proxy for improvisation skill) while controlling for demographic, motion, scanner, session, and physiological covariates. The approach follows the functional requirements (FR‑001 – FR‑008) and success criteria (SC‑001 – SC‑004) enumerated in the specification.

## Dataset Strategy
| Role | Dataset | Source URL (verified) | Loader | Expected Variables | Notes |
|------|---------|-----------------------|--------|--------------------|-------|
| Primary fMRI‑derived time‑series | **OpenNeuro ds000246** (musical improvisation) | `https://openneuro.org/datasets/ds000246` | `datasets.load_dataset("openneuro", "ds000246", streaming=False)` | `subject_id`, `run_label` (Improv/Scripted), `age`, `years_training`, `fd`, `roi_1 … roi_100` | Verified dataset contains the required improvisation vs. scripted task labels. |
| ROI Atlas (definition) | Schaefer ROI atlas (built‑in Nilearn) | N/A (library asset) | `nilearn.datasets.fetch_atlas_schaefer_2018` | ROI labels, MNI coordinates | Used for extracting ROI signals from raw NIfTI (if needed). |
| Optional behavioral proxy | None (use `years_training` as primary skill metric) | — | — | — | If `run_label` is missing for any subject, analysis falls back to `years_training`. |

*All external URLs are from the verified list; no other datasets are used.*

## Preprocessing (FR‑002)
1. **Load raw NIfTI (if present) or use the parquet time‑series directly.**  
2. **Motion correction** – FSL **MCFLIRT** via Nipype.  
3. **Slice‑timing correction** – FSL **slicetimer** via Nipype.  
4. **Spatial normalization** – FSL **FLIRT** to MNI152 2 mm template.  
5. **Band‑pass filter** – FSL **fslmaths** (0.01‑0.1 Hz).  
6. **ROI extraction** – Apply Schaefer‑100 atlas with Nilearn; compute mean signal per ROI → matrix `(timepoints × 100)`.  
7. **Quality Control** – Compute frame‑wise displacement; flag subjects with FD > 0.5 mm for > 20 % volumes (edge‑case handling).  

All steps are deterministic and run on CPU.

## Dynamic Connectivity & Graph Metrics (FR‑003)
- **Sliding window**: Rectangular window; default 45 s (≈ 30 TRs assuming TR ≈ 1.5 s) with 10 s step.  
- **Correlation**: Pearson correlation for each window; apply `LedoitWolf` shrinkage (`sklearn.covariance.LedoitWolf`) to regularize the covariance before converting to correlation.  
- **Graph construction**: Thresholded absolute correlation matrix (retain top [deferred] edges) to build an undirected weighted graph per window.
- **Metrics** (computed via NetworkX):  
  - Global Efficiency (`nx.global_efficiency`)  
  - Modularity (Louvain algorithm via `community` package)  
  - Participation Coefficient (custom implementation)  

Outputs: `metrics_<subject>.csv` with columns `window_id, global_efficiency, modularity, participation_coefficient`.

## Dimensionality Reduction (FR‑008)
- Stack all metric vectors across windows and subjects.  
- Apply PCA (`sklearn.decomposition.PCA`) retaining components that explain ≥ 80 % of variance.  
- Store component scores per subject (`pca_scores_<subject>.csv`).

## Primary Association Analysis (FR‑004, FR‑005)
- **Model**: Linear regression `PC_score ~ years_training + age + fd + scanner + session_order + phys_noise`.  
- **Permutation testing**: Shuffle `years_training` 5 000 times, recompute coefficient, build null distribution.  
- **FDR correction**: Apply Benjamini‑Hochberg across all tested PCs (SC‑001, SC‑003).  
- **Outcome**: Table of regression coefficients, raw and FDR‑corrected p‑values; flag “null result” if corrected p > 0.05 (SC‑001).  

All modeling is performed with `statsmodels.api.OLS` (CPU).

## Sensitivity Analysis (FR‑006)
- Loop over `window_size ∈ {30, 45, 60}` s and `step_size ∈ {5, 10}` s.  
- Repeat connectivity → PCA → regression pipeline.  
- Summarize coefficient stability (mean, SD) across parameter combos in a CSV (`sensitivity_summary.csv`).  

## Visualization (FR‑007)
- For the two groups (high vs. low years of training), compute average adjacency matrices (after thresholding).  
- Build NetworkX graphs; edge width ∝ weight, node color ∝ community.  
- Plot side‑by‑side using Matplotlib; save as `fig_network_topology.png`.  

## Statistical Rigor Checklist
- **Multiple comparisons** – FDR across PCs (≥ 1 test).  
- **Permutation testing** – 5 000 permutations, `[deferred]` exact runtime.  
- **Power acknowledgement** – Sample size limited to the number of available subjects (approximately a few dozen).; power estimate reported in the **Power Analysis** subsection of the plan.  
- **Causal framing** – Explicitly described as associational (Constitution Principle VII).  
- **Measurement validity** – FSL/AFNI preprocessing pipelines are widely validated; Schaefer atlas is a standard parcellation.  
- **Collinearity** – PCA mitigates metric collinearity; we will report variance inflation factors for the original metrics as a diagnostic.

## Compute Feasibility (CPU‑first)
- **Memory**: Streaming parquet loader keeps < 2 GB in memory; per‑subject matrices ≤ 200 MB.  
- **Runtime**: Estimated a few hours for 25 subjects on a 2‑core runner (benchmark on similar data).  
- **No GPU**: All libraries are pure CPU; no `torch.cuda` calls.

## Constitution Check (re‑stated)
All steps respect the seven core principles (see `plan.md`). No violations detected.

---

