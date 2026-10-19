# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

**Branch**: `001-gene-regulation` | **Date**: 2026-10-19 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
A reproducible, CPU‑only pipeline that:

1. **Downloads two verified OpenNeuro datasets**  
   - **ds000246** (parquet shard `clane9/openneuro-fslr64k`) – used for descriptive ROI‑time‑series analysis.  
   - **ds001600** (parquet shard `clane9/openneuro-ds001600`) – contains expert blind‑rating scores and task‑condition labels, enabling the core association analysis.  
   Both are streamed row‑wise to stay within the ~7 GB RAM limit.

2. **Preprocesses fMRI data** using **fMRIPrep (≥ 20.2.0)** executed in a Docker container on the CPU runner (no GPU needed). fMRIPrep performs motion correction, slice‑timing correction, MNI normalization, and band‑pass filtering (0.01–0.1 Hz). The pipeline records the fMRIPrep version and checksum for reproducibility (fulfilling Constitution Principle VI).

3. **Extracts Schaefer 100‑ROI time‑series** (via `nilearn.datasets.fetch_atlas_schaefer_2018`) and applies the same band‑pass filter. Generates per‑subject CSVs (`roi_timeseries_<subject>.csv`) adhering to `roi_timeseries.schema.yaml`.

4. **Computes sliding‑window functional connectivity** (default window = 45 s, step = 10 s) using a **Ledoit‑Wolf regularized covariance estimator** (`sklearn.covariance.LedoitWolf`) and derives **global efficiency, modularity (Louvain), and participation coefficient** for each window (ROI‑based graph metrics). Outputs `metrics_<subject>.csv` per the `network_metrics.schema.yaml`.

5. **Reduces dimensionality** with **PCA** (≥ 80 % variance retained) and stores subject‑wise PC scores (`pca_scores.csv`) matching `pca_scores.schema.yaml`.

6. **Performs a priori power analysis** using **`statsmodels.stats.power.FTestPower`** with a medium effect size (f² = 0.15), α = 0.05, power = 0.80. The required N is compared to the available subject count from ds001600; results are saved in `results/power_analysis.json`. If under‑powered, only the association stage aborts (SC‑005).

7. **Conditional association analysis** (FR‑004, FR‑005, FR‑009, FR‑011):  
   - **Skill‑proxy selection priority**: `expert_rating` → `years_of_training` → `task_condition`.  
   - If any of these columns exist in ds001600, an OLS regression of each retained PC on the selected proxy + all available covariates (age, FD, instrument_type, musical_genre, practice_intensity, education_level) is run.  
   - **Freedman‑Lane residual permutation** (1000 permutations, seeded) generates raw p‑values, which are **Benjamini‑Hochberg FDR‑corrected** across PCs (SC‑001, SC‑003).  
   - Results are written to `results/regression_results.csv` per `regression_results.schema.yaml`.  
   - If **no skill‑proxy column** is present, the pipeline logs “no skill proxy – association skipped” and records `skill_proxy_used = "none"` in the manifest (still satisfying FR‑010 and SC‑006).

8. **Sensitivity analysis** (FR‑006, SC‑002): sweeps window ∈ {30, 45, 60} s and step ∈ {5, 10} s, recomputes metrics (and regression if applicable), and stores summary statistics in `results/sensitivity_summary.csv`.

9. **Visualization** (FR‑007):  
   - If `task_condition` is present, creates group‑average adjacency graphs (Improvisation vs. Scripted) with **NetworkX** and **Matplotlib**, saved as `results/fig_network_topology.png`.  
   - Otherwise, produces a single descriptive ROI‑based graph with the same tools, clearly labeled as “descriptive topology – no group comparison”.

10. **Master manifest** (FR‑012, SC‑006): aggregates per‑subject derived metrics, covariates, QC flags, power status, and (if computed) regression outcomes into `results/manifest.csv`, validated against `manifest.schema.yaml`.

**Critical limitation resolved**: By adding ds001600, the pipeline now has at least one open dataset containing the required skill‑proxy columns, enabling the primary hypothesis test while still providing a descriptive analysis on ds000246.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`): `numpy`, `pandas`, `scipy`, `scikit-learn>=1.3` (Ledoit‑Wolf, PCA), `networkx>=3.2` (graph metrics, Louvain), `statsmodels>=0.14` (power analysis, regression, permutation), `matplotlib>=3.8`, `nilearn>=0.10` (Schaefer atlas & auxiliary utilities), `pyarrow`, `huggingface_hub`, `docker`, `pytest`.  
- **Storage**: `data/` (raw parquet shards, checksums, column inventory) and `results/` (derived CSV/JSON/PNG).  
- **Testing**: `pytest` unit tests + contract validation against the `contracts/` schemas.  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU, ~7 GB RAM, ≤6 h).  
- **Compute Feasibility**: All steps run on CPU; streaming ensures peak RAM < 2 GB; total runtime ≤ 5 h. No GPU escape hatch required.

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | Data fetched from canonical URLs; SHA‑256 recorded; random seeds pinned in `code/config.py`. |
| II. Verified Accuracy | Only URLs listed in the “Verified datasets” block are cited. |
| III. Data Hygiene | Raw parquet never modified; each transformation writes a new file; checksums stored; no PII. |
| IV. Single Source of Truth | `results/manifest.csv` is the SSOT for all derived numbers. |
| V. Versioning Discipline | All artifacts are content‑hashed; state timestamps updated automatically. |
| VI. Neuroimaging Preprocessing & Topology Integrity | Preprocessing performed with **fMRIPrep (≥ 20.2.0)**, a fully CPU‑compatible, open‑source tool satisfying the exact steps required by Principle VI. ROI definition uses the verified Schaefer 100‑ROI atlas. |
| VII. Statistical Rigor in Skill‑Neural Correlation | Permutation testing (Freedman‑Lane, 1000 permutations), BH‑FDR correction, power analysis via `statsmodels`, PCA for collinearity, and strict associational framing. |

## Phase & Task Mapping (covers all FR/SC)

| Phase | Tasks (brief) | FR IDs | SC IDs |
|-------|---------------|--------|--------|
| **0. Data acquisition** | Download ds000246 and ds001600 parquet shards; verify SHA‑256; inventory columns → `data/raw/column_inventory.json`. | FR‑001 (adapted) | SC‑004 |
| **1. Preprocessing** | Run fMRIPrep (CPU‑only Docker) on each subject; generate preprocessed NIfTI; extract Schaefer ROI time‑series; band‑pass filter; QC flag high‑motion subjects. | FR‑002 (fMRIPrep adaptation) | SC‑004 |
| **2. Dynamic connectivity & metrics** | Sliding‑window (default 45 s, 10 s step) → Ledoit‑Wolf covariance → Pearson correlation → weighted graph → global efficiency, Louvain modularity, participation coefficient. | FR‑003 | — |
| **3. Dimensionality reduction** | Stack per‑window descriptors; PCA (≥80 % variance) → retained PCs per subject. | FR‑008 | — |
| **4. Power analysis (report‑only)** | Compute required N with `statsmodels.stats.power.FTestPower`; compare to available N; write `results/power_analysis.json`; abort association only if under‑powered. | FR‑010 | SC‑005 |
| **5. Conditional association** *(contingent)* | Select skill proxy (`expert_rating` → `years_of_training` → `task_condition`); OLS regression of PCs on proxy + present covariates; Freedman‑Lane 1000 permutations; BH‑FDR across PCs; output `results/regression_results.csv`. If no proxy → log and set `skill_proxy_used = "none"` in manifest. | FR‑004, FR‑005, FR‑009, FR‑011 | SC‑001, SC‑003 |
| **6. Sensitivity analysis** *(contingent)* | Re‑run Phases 2–3 (and 5 if it ran) for window ∈ {30, 45, 60} s × step ∈ {5, 10} s; summarize mean/SD of metrics and correlation coefficients → `results/sensitivity_summary.csv`. | FR‑006 | SC‑002 |
| **7. Visualization** *(contingent)* | If `task_condition` exists → group‑average graphs; else → descriptive graph; render with NetworkX/Matplotlib → `results/fig_network_topology.png`. | FR‑007 | — |
| **8. Reporting & manifest** | Assemble `results/manifest.csv` with all derived fields, covariates, QC flags, power status, and (if computed) regression outcomes; validate against `manifest.schema.yaml`. | FR‑012 | SC‑006 |

**Ordering** respects data flow: download → preprocessing → ROI extraction → connectivity → PCA → power → (conditional) regression → sensitivity → visualization → manifest.

---


## projects/PROJ-414-investigating-the-relationship-between-b/specs/001-investigating-the-relationship-between-b/research.md===
# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

## Overview
A fully reproducible, CPU‑only analysis pipeline that:

1. **Downloads two verified OpenNeuro fMRI parquet shards**  
   - `ds000246` (parquet shard `clane9/openneuro-fslr64k`) for descriptive analysis.  
   - `ds001600` (parquet shard `clane9/openneuro-ds001600`) which includes expert blind‑rating scores and task‑condition labels, enabling the core association analysis.

2. **Preprocesses fMRI data** with **fMRIPrep (≥ 20.2.0)** via Docker on the CPU runner (no GPU). This carries out motion correction, slice‑timing correction, MNI normalization, and band‑pass filtering (0.01–0.1 Hz). The version and checksum are recorded for reproducibility (Constitution Principle VI).

3. **Generates Schaefer 100‑ROI time‑series**, band‑pass filters them, and flags high‑motion subjects (FD > 0.5 mm for >20 % volumes).

4. **Computes sliding‑window Ledoit‑Wolf functional connectivity** and derives **global efficiency, modularity (Louvain), participation coefficient** for each window (ROI‑based graph metrics).

5. **Reduces the descriptor space** with PCA (≥ 80 % variance retained).

6. **Performs a priori power analysis** using **`statsmodels.stats.power.FTestPower`** (medium effect size f² = 0.15, α = 0.05, power = 0.8). If the required N exceeds the available subjects in ds001600, the association stage is aborted while all other stages continue.

7. **Conditional association**: selects the best available skill proxy in priority order (`expert_rating` → `years_of_training` → `task_condition`). If a proxy column exists, runs an OLS regression of each retained PC on the proxy + all present covariates, employing a Freedman‑Lane residual permutation test (1000 permutations, seeded) and Benjamini‑Hochberg FDR correction across PCs. If **no skill proxy** is present, logs a clear message and records `skill_proxy_used = "none"` in the manifest.

8. **Sensitivity analysis** sweeps window sizes {30, 45, 60} s and step sizes {5, 10} s, recomputes metrics (and regression if applicable), and stores a summary CSV of metric means/SDs and correlation coefficient variability.

9. **Visualization** using NetworkX and Matplotlib:  
   - If `task_condition` exists, creates group‑comparison graphs (Improvisation vs. Scripted).  
   - Otherwise, produces a single descriptive ROI‑based connectivity topology figure.

10. **Master manifest** (`results/manifest.csv`) records for every subject all derived metrics, covariates, QC flags, power status, and (if computed) regression outcomes, serving as the Single Source of Truth (Constitution Principle IV).

**Key advancement**: By incorporating ds001600, the pipeline now possesses the required behavioral columns to test the primary hypothesis, while still providing a robust descriptive analysis on ds000246.

## Dataset Strategy

| Role | Dataset | Verified URL | Loader | Expected Variables | Notes |
|------|---------|--------------|--------|--------------------|-------|
| Primary fMRI timeseries (association) | OpenNeuro ds001600 parquet shard | `https://huggingface.co/datasets/clane9/openneuro-ds001600/resolve/main/data/test-00000-of-00016.parquet` | Direct download via `huggingface_hub.hf_hub_download`; streamed with `pyarrow` | BOLD timeseries; `expert_rating` (1‑10); `task_condition` (Improvisation/Scripted); `years_of_training`; plus age, fd, instrument_type, musical_genre, practice_intensity, education_level. | Provides the essential skill‑proxy columns. |
| Secondary fMRI timeseries (descriptive) | OpenNeuro ds000246 parquet shard | `https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet` | Direct download via `huggingface_hub.hf_hub_download`; streamed with `pyarrow` | BOLD timeseries; basic demographics (age, fd). | Used for ROI‑based descriptive connectivity when skill proxies are absent. |
| ROI atlas | Schaefer 100‑ROI atlas (7‑networks) | Programmatic fetch via `nilearn.datasets.fetch_atlas_schaefer_2018` | `nilearn.datasets.fetch_atlas_schaefer_2018` | ROI definitions for 100 parcels | Verified, satisfies Principle VI after amendment. |

### Dataset‑Variable Fit
The pipeline performs a **column‑inventory step** (`data/raw/column_inventory.json`) that records which of the required behavioral/covariate columns are present in each dataset. All downstream steps consult this inventory, ensuring no assumption of missing columns.

## Preprocessing (FR‑002 – fMRIPrep)

1. **Streaming download** – `download_openneuro.py` streams each parquet file, computes SHA‑256, writes `data/checksums.json`.  
2. **fMRIPrep execution** – `preprocess_fmriprep.py` launches the Docker image `poldracklab/fmriprep:20.2.6` with `--use-syn-sdc` and `--output-spaces MNI152NLin2009cAsym`. Outputs preprocessed NIfTI files under `data/preprocessed/`.  
3. **ROI extraction** – `extract_rois.py` fetches Schaefer 100‑ROI atlas, extracts mean BOLD per ROI, applies Butterworth band‑pass (0.01–0.1 Hz), writes `roi_timeseries_<subject>.csv`.  
4. **QC & exclusion** – computes frame‑wise displacement; subjects with >20 % bad volumes are flagged, exclusion reason recorded in `qc_<subject>.json`.

## Dynamic Connectivity & ROI‑Based Metrics (FR‑003)

- **Sliding window**: rectangular window, default 45 s, step 10 s; windows with <30 TRs are dropped.  
- **Estimator**: `sklearn.covariance.LedoitWolf` → covariance → Pearson correlation.  
- **Graph construction**: absolute correlation matrix → weighted undirected graph (no threshold).  
- **Metrics** (computed with `networkx`): global efficiency, Louvain modularity, participation coefficient.  
- Output `metrics_<subject>.csv` conforms to `network_metrics.schema.yaml`.

## Dimensionality Reduction (FR‑008)

`dimensionality.py` stacks all window descriptors, runs `sklearn.decomposition.PCA` (seeded), retains the smallest number of components explaining ≥ 80 % variance, writes `pca_scores.csv` per `pca_scores.schema.yaml`.

## Power Analysis (FR‑010, SC‑005)

`analysis.py` uses **`statsmodels.stats.power.FTestPower`** with effect size f² = 0.15, α = 0.05, power = 0.8 to compute required N, compares to available N from ds001600, writes `results/power_analysis.json`. If under‑powered, only the association stage aborts (status `"underpowered_association_skipped"`).

## Conditional Association Analysis (FR‑004, FR‑005, FR‑009, FR‑011, SC‑001, SC‑003)

1. **Skill‑proxy selection** (priority order): `expert_rating` → `years_of_training` → `task_condition`.  
2. **Model**: OLS regression `PC_score ~ skill_proxy + age + fd + instrument_type + musical_genre + practice_intensity + education_level`. Only covariates present in the column inventory are included.  
3. **Freedman‑Lane permutation**: 1000 seeded residual permutations (implemented via `statsmodels.stats.weightstats.ttest_ind` with custom residual shuffling).  
4. **Multiple‑comparison correction**: Benjamini‑Hochberg FDR across all retained PCs.  
5. **Outputs**: `results/regression_results.csv` adhering to `regression_results.schema.yaml`. Null results (p > 0.05) are flagged but not treated as failures.

All statements remain strictly **associational** (Constitution VII).

## Sensitivity Analysis (FR‑006, SC‑002)

`sensitivity.py` repeats Phases 2–3 (and Phase 5 if it ran) for the six window/step combos, records mean/SD of the three metrics and, when applicable, the correlation coefficient between the skill proxy and each PC. Results saved in `results/sensitivity_summary.csv`. If no skill proxy exists, correlation fields are set to `not_computable_no_skill_proxy`.

## Visualization (FR‑007)

`visualization.py`:

- **If `task_condition` exists**: computes mean adjacency per condition, builds NetworkX graphs, renders with Matplotlib (edge width ∝ weight, node color ∝ Louvain community), saves `results/fig_network_topology.png` with caption indicating the comparison.  
- **If absent**: renders a single descriptive ROI‑based graph, labeled accordingly.

## Decision / Rationale (Compute Feasibility)

- **CPU‑first**: All libraries are CPU‑compatible; streaming ensures RAM stays < 2 GB.  
- **Dataset choice**: ds001600 provides the necessary skill‑proxy columns; ds000246 remains for descriptive work. Both are programmatically downloadable from verified Hugging Face URLs.  
- **Methodological soundness**: fMRIPrep replaces FSL/AFNI while satisfying Principle VI; Ledoit‑Wolf estimator ensures stable covariance with short windows; PCA handles collinearity; permutation + FDR ensures robust inference.

## Statistical Rigor Checklist

- **Multiple comparisons**: BH‑FDR across PCs.  
- **Permutation testing**: 1000 Freedman‑Lane residual permutations (seeded).  
- **Power analysis**: `statsmodels.stats.power.FTestPower` with effect size f² = 0.15; aborts only association if under‑powered.  
- **Causal framing**: strictly associational.  
- **Measurement validity**: Schaefer atlas is widely validated; ROI‑based descriptors are explicitly labeled.  
- **Collinearity**: PCA mitigates correlated metrics.  
- **Confound control**: all available covariates included; missing covariates omitted and noted.

## Constitution Check

All seven principles are addressed. The switch to fMRIPrep resolves the previous deviation from Principle VI. The inclusion of ds001600 resolves the data‑resource gaps. No silent violations remain.

---




## projects/PROJ-414-investigating-the-relationship-between-b/specs/001-investigating-the-relationship-between-b/quickstart.md===
# Quickstart: Brain Network Dynamics & Improvisation Skill Analysis

## Prerequisites
- Python 3.11 (available on the GitHub Actions runner).  
- Internet access (to download the verified parquet shards).  
- Docker (for fMRIPrep) – Docker is pre‑installed on the GitHub Actions runner.  
- No GPU, FSL, or AFNI installation required.

## 1. Set up the environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```
All versions are pinned in `code/requirements.txt`.

## 2. Download and verify the data (verified sources)
```bash
python code/download_openneuro.py
```
What this script does:
- Downloads **ds001600** (`test-00000-of-00016.parquet`) and **ds000246** (`test-00000-of-00016.parquet`) from the verified Hugging Face URLs.
- Verifies each file’s SHA‑256 checksum (recorded in `data/checksums.json`).
- Streams the parquet files with `pyarrow`, inventories column names, and writes `data/raw/column_inventory.json` indicating which behavioral/covariate columns are present.
- Exits with an error if any download fails; **never falls back to synthetic data**.

## 3. Run the full pipeline
```bash
python code/run_all.py \
    --seed 42 \
    --window 45 \
    --step 10 \
    --permutations 1000
```
The orchestrator executes the phases in the exact order required by the plan:

1. **Preprocessing** – launches fMRIPrep (Docker) on each subject’s raw NIfTI files (CPU‑only).  
2. **ROI extraction** – fetches the Schaefer 100‑ROI atlas via Nilearn and creates `roi_timeseries_<subject>.csv`.  
3. **Dynamic connectivity & metrics** – computes sliding‑window Ledoit‑Wolf correlations and graph metrics.  
4. **Dimensionality reduction** – runs PCA and writes `pca_scores.csv`.  
5. **Power analysis** – uses `statsmodels.stats.power.FTestPower` and writes `results/power_analysis.json`.  
6. **Conditional association** – runs regression only if a skill‑proxy column (`expert_rating`, `years_of_training`, or `task_condition`) is present; otherwise logs “no skill proxy – association skipped”.  
7. **Sensitivity analysis** – sweeps all six window/step combinations and writes `results/sensitivity_summary.csv`.  
8. **Visualization** – generates `results/fig_network_topology.png` (group comparison if `task_condition` exists, otherwise a descriptive graph).  
9. **Manifest creation** – aggregates everything into `results/manifest.csv`.

### Running a single phase (for debugging)
```bash
python code/run_all.py --stage download --stage preprocess --stage extract --stage metrics
```

## 4. Inspect the results
- `results/manifest.csv` – master manifest (Single Source of Truth).  
- `results/regression_results.csv` – association results (present only if a skill proxy existed).  
- `results/sensitivity_summary.csv` – robustness table across window/step settings.  
- `results/power_analysis.json` – required N vs. available N and status (`adequate` or `underpowered_association_skipped`).  
- `results/fig_network_topology.png` – visualization of ROI‑based connectivity (group comparison or descriptive).

## 5. Run the test suite
```bash
pytest -q tests
```
Tests include unit‑tests and contract validation against the schema files (`contracts/*.schema.yaml`).  

## 6. Run a different sensitivity setting
```bash
python code/run_all.py \
    --seed 123 \
    --window 30 \
    --step 5 \
    --output_dir results/window30_step5
```
All outputs will be written under the specified `--output_dir`.
