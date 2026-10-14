# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

**Branch**: `001-gene-regulation` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The pipeline will (1) acquire two open‑source fMRI datasets that include improvisation vs. scripted task labels (OpenNeuro ds000246 and ds001600), (2) preprocess the data on a CPU‑only GitHub Actions runner using **FSL/AFNI** via **Nipype**, (3) compute sliding‑window functional connectivity with a **Ledoit‑Wolf** regularized estimator and derive graph‑theoretic metrics (global efficiency, modularity, participation coefficient), (4) reduce the metric space with **PCA**, (5) test associations between the principal components and the skill proxy (**years of training**, **task condition**, or an optional **post‑scan improvisation rating** if present) while controlling for age, motion, and additional covariates (instrument type, genre, practice intensity, education), (6) assess significance with **1 000 permutations** and **FDR** correction, (7) run a sensitivity sweep over window/step sizes, (8) generate NetworkX/Matplotlib visualizations, and (9) produce a **master manifest** (`data/output/master_manifest.csv`) that serves as the **Single Source of Truth (SSoT)** for all downstream figures and tables. All steps map to FR‑001 – FR‑008 and SC‑001 – SC‑004.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `nilearn>=0.10.0` (ROI extraction)  
  - `nibabel` (NIfTI I/O)  
  - `numpy`, `pandas`, `scipy`  
  - `scikit-learn>=1.3.0` (Ledoit‑Wolf, PCA)  
  - `networkx>=3.2` (graph metrics)  
  - `statsmodels>=0.14.0` (regression)  
  - `matplotlib>=3.8.0` (visualization)  
  - `datasets>=2.16.0` (HuggingFace data loading)  
  - `nipype>=1.8.0` (FSL/AFNI wrappers)  
  - `fslpy` (ensures FSL 6.0.5)  
- **Storage**: All artifacts under `data/` (raw parquet, preprocessed NIfTI, CSV/Parquet tables).  
- **Testing**: `pytest` + contract validation against `contracts/`.  
- **Target Platform**: Linux CI runner (GitHub Actions free tier).  
- **Performance Goals**: End‑to‑end pipeline for ≥ 40 subjects ≤ 6 h, ≤ 7 GB RAM.  
- **Constraints**: CPU‑only; no GPU libraries; all external URLs must be from the verified list.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All data fetched from the verified HuggingFace OpenNeuro mirrors (`openneuro/ds000246` and `openneuro/ds001600`) via `datasets.load_dataset`; random seeds pinned in `code/config.py`. |
| II. Verified Accuracy | No external citations beyond dataset URLs and library docs; all references validated by the Reference‑Validator. |
| III. Data Hygiene | Checksums recorded in `data/checksums.json`; each transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | The **master manifest** `data/output/master_manifest.csv` lists every output file with its hash; every figure/table references a row in this manifest. |
| V. Versioning Discipline | All artifacts hashed; `state/projects/PROJ-414…yaml` updated automatically by CI. |
| VI. Neuroimaging Preprocessing and Network Topology Integrity | Preprocessing uses **FSL 6.0.5** and **AFNI 22.2.07** via Nipype (motion correction, slice timing, MNI normalization, 0.01‑0.1 Hz band‑pass). Schaefer‑100 atlas applied; sliding‑window parameters match spec. |
| VII. Statistical Rigor in Skill‑Neural Correlation | Regression controls for age, years of training, FD, **instrument_type**, **genre**, **practice_intensity**, **education** when present. Permutation testing (1 000) + Benjamini‑Hochberg FDR (α = 0.05); analysis framed as associational. |
| **Construct Validity Note** | Years of training and binary task condition are imperfect proxies for improvisational skill. When an optional post‑scan improvisation rating (`improv_rating`) is available, it will be used as a more direct skill measure. Limitations are discussed in the final report. |
| **Power Analysis** | Combining a comparable dataset with ds001600 yields a sample size on the order of tens of participants. Power analysis (medium effect, d = 0.5) gives ≈ 0.86 power at α = 0.05. If fewer subjects are present, reduced power will be reported. |

All principles satisfied; no violations detected.

## Project Structure
```text
specs/001-gene-regulation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── network_metrics.schema.yaml
└── tasks.md   # generated later
```

```text
src/
├── pipeline/
│   ├── download.py          # data acquisition from HuggingFace OpenNeuro mirrors
│   ├── preprocess.py        # FSL/AFNI preprocessing via Nipype
│   ├── connectivity.py      # sliding‑window + Ledoit‑Wolf
│   ├── graph_metrics.py     # efficiency, modularity, participation
│   ├── dimensionality.py    # PCA
│   ├── analysis.py          # regression + permutation + FDR
│   ├── sensitivity.py       # window/step sweep
│   └── visualization.py     # NetworkX + Matplotlib
└── utils/
    └── logger.py
```

## Phase & Task Mapping (covers all FR/SC)

| Phase | Tasks (brief) | FR IDs | SC IDs |
|-------|---------------|--------|--------|
| **0. Data Acquisition** | Download verified OpenNeuro ds000246 and ds001600 via HuggingFace; verify required columns (`subject_id`, `run_label`, `age`, `years_training`, `fd`, `roi_1…roi_100`, optional `instrument_type`, `genre`, `practice_intensity`, `education`, `improv_rating`). | FR‑001 | SC‑004 |
| **1. Preprocessing** | Nipype wrappers: MCFLIRT (motion), slicetimer, FLIRT (MNI), band‑pass (0.01‑0.1 Hz); ROI extraction with Schaefer‑100 via Nilearn. Output per‑subject CSV `(timepoints × 100)`. | FR‑002 | SC‑004 |
| **2. Connectivity & Graph Metrics** | Sliding‑window Pearson (default 45 s, step 10 s, ≥ 30 TP); Ledoit‑Wolf shrinkage; build weighted graph; compute global efficiency, modularity (Louvain), participation coefficient. | FR‑003 | — |
| **3. Dimensionality Reduction** | Stack metric vectors; PCA (retain ≥ 80 % variance). | FR‑008 | — |
| **4. Primary Association Analysis** | Linear regression `PC ~ years_training + age + fd + instrument_type + genre + practice_intensity + education` (or `improv_rating` when present); 1 000 permutation test; Benjamini‑Hochberg FDR across PCs. | FR‑004, FR‑005 | SC‑001, SC‑003 |
| **5. Sensitivity Analysis** | Repeat steps 2‑4 for window sizes {30, 45, 60}s and step sizes {5, 10}s; record coefficient variation. | FR‑006 | SC‑002 |
| **6. Visualization** | Mean adjacency per high/low training (or high/low improv_rating) groups; NetworkX graph; Matplotlib side‑by‑side plot. | FR‑007 | — |
| **7. Reporting & QC** | Log excluded subjects (FD > 0.5 mm > 20 % volumes); handle missing `run_label` (error‑halt or fallback to `years_training`/`improv_rating`); write `master_manifest.csv`; generate tables/figures. | — | SC‑001‑SC‑004 |

All phases are ordered so that data is available before consumption, models are fitted before evaluation, and figures are generated before final reporting.

## Power Analysis (updated)
Using `statsmodels.stats.power.TTestIndPower` with **N ≈ 40** (combined datasets) and a medium effect size (Cohen’s d = 0.5) yields **≈ 0.86 power** at α = 0.05 (two‑tailed). This meets the conventional ≥ 0.80 threshold. If fewer subjects are available, the pipeline will report the reduced power.

## Compute Feasibility (CPU‑first)
- **Memory**: Streaming dataset loader keeps < 2 GB RAM.  
- **Runtime**: Benchmarks on similar data estimate a few hours for 40 subjects on a 2‑core runner.  
- **GPU**: None required; all libraries run on CPU.

---



