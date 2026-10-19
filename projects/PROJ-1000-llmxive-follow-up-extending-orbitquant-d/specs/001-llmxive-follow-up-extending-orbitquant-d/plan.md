# Implementation Plan: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

**Branch**: `001-llmxive-followup` | **Date**: 2026-10-18 | **Spec**: `specs/001-llmxive-followup/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-followup/spec.md`

## Summary
The project will (1) compute a **semantic‑entropy** score for each MS‑COCO caption using a lightweight language‑model proxy, (2) measure variance of intermediate DiT activations during a float32 forward pass, (3) test the **Spearman** correlation (controlling for prompt length) between entropy and activation variance **and** the correlation between activation variance and **quantization MSE** (FR‑009), (4) cluster activation histograms into **K = 16** entropy bins and derive a rotation matrix per bin, (5) implement a router that selects the appropriate matrix at inference time with explicit edge‑case handling, and (6) evaluate the dynamic‑router pipeline against the static OrbitQuant baseline on FID, CLIP, MSE, and wall‑clock time, reporting statistical significance with **paired t‑tests** (primary) and a **Wilcoxon signed‑rank fallback** if normality is violated, and a sensitivity sweep. All steps are reproducible, store artifacts under `data/` or `figures/`, and obey the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `diffusers==0.27.0`, `transformers==4.41.0`, `datasets==2.19.0`, `sentence-transformers==2.2.2`, `scikit-learn==1.5.0`, `numpy`, `pandas`, `fid-score==0.0.6` (CPU fork), `clip-score==0.0.5` (CPU fork), `accelerate`, `peft` (for 8‑bit loading).  
- **Target Platform**: GitHub Actions Linux runner (several CPU cores, ~7 GB RAM, ~14 GB disk). GPU‑escape hatch to Kaggle free T4/P100 when a DiT model cannot run on CPU.  
- **Constraints**: No synthetic data; all artifacts stored under `data/` or `figures/`. No `state/` writes.

## Constitution Check

| Principle | Status | How the plan satisfies it |
|-----------|--------|---------------------------|
| I. Reproducibility | PASS | Fixed random seeds (`code/config.py`); data fetched via `datasets.load_dataset('coco2017', split='validation', streaming=True)`; outputs written only to `data/` and `figures/`. |
| II. Verified Accuracy | PASS | All citations will be validated by the Reference‑Validator before review. |
| III. Data Hygiene | PASS | Raw MS‑COCO files stored under `data/raw/` with SHA‑256 checksums recorded in `data/checksums.json`. Transformations produce new files in `data/processed/`. |
| IV. Single Source of Truth | PASS | Every figure/table originates from a row in `data/processed/results.csv` (or a specific JSON). |
| V. Versioning Discipline | PASS | After each pipeline run a `data/artifact_hashes.json` (project‑owned) is updated with SHA‑256 hashes of all new artifacts; the Advancement‑Evaluator uses this for change detection. |
| VI. Dynamic Rotation Basis Validation | PASS | The clustering report (`data/processed/clustering_report.json`) documents the layers, splits, and entropy boundaries; correlation tests (including the variance‑MSE link) must achieve *p* < 0.05 before proceeding to router implementation. |
| VII. W2A4 Regime Overhead Accounting | PASS | Phase 3 records per‑image inference time for static and dynamic pipelines; any >2 % increase triggers a documented trade‑off. |

## Project Structure
```
specs/001-llmxive-followup/
├─ plan.md
├─ research.md
├─ data-model.md
├─ quickstart.md
└─ contracts/
    ├─ activation_schema.schema.yaml
    ├─ results_schema.schema.yaml
    ├─ rotation_matrix_schema.schema.yaml
    ├─ entropy_schema.schema.yaml
    └─ prompt_schema.schema.yaml

projects/PROJ-1000-llmxive-followup-extending-orbitquant-d/
├─ code/
│  ├─ __init__.py
│  ├─ config.py               # seeds, paths, hyper‑params
│  ├─ models/
│  │   ├─ dit_wrapper.py      # hooks for variance measurement (Stable Diffusion 2.1)
│  │   └─ flux_wan_loader.py  # GPU‑escape loader (8‑bit optional)
│  ├─ analysis/
│  │   ├─ entropy_proxy.py    # lightweight LM → entropy
│  │   ├─ entropy_validation.py # readability & perplexity comparison
│  │   ├─ correlation.py
│  │   ├─ clustering.py
│  │   └─ router.py
│  ├─ quantization/
│  │   ├─ w2a4_engine.py
│  │   └─ static_baseline.py
│  ├─ evaluation/
│  │   ├─ metrics.py
│  │   └─ timing.py
│  └─ main.py                 # orchestrates phases
├─ data/
│  ├─ raw/                     # MS‑COCO images + captions (via huggingface `coco2017`)
│  └─ processed/
│      ├─ prompts.csv
│      ├─ entropy_scores.csv
│      ├─ activation_stats/
│      │   └─ *.json           # one JSON per activation measurement
│      ├─ rotation_matrices/
│      │   ├─ matrix_0.npy
│      │   ├─ metadata_0.json
│      │   └─ … matrix_15.npy / metadata_15.json
│      ├─ clustering_report.json
│      ├─ correlation_plot.png
│      ├─ correlation_stats.json
│      ├─ results.csv          # includes rotation_index column for dynamic rows
│      └─ logs/
│          ├─ correlation_log.json
│          ├─ model_load_log.json
│          └─ proxy_failures.json
├─ figures/                    # all plots for the paper
└─ requirements.txt
```

## Phase & Task Mapping (covers every FR/SC)

| Phase | Tasks (mapped FR/SC) | Output (project‑owned) |
|-------|----------------------|------------------------|
| **0 – Correlation & Sensitivity Study** | FR‑001, FR‑002, FR‑009, SC‑001 – Compute entropy (entropy_proxy), **validate** entropy (entropy_validation), run DiT (Stable Diffusion 2.1) on a stratified set of prompts, extract per‑layer variance, compute **Spearman** *ρ* and two‑tailed *p* (partial correlation controlling for `prompt_length`). Also compute **Spearman** correlation between **activation variance** and **MSE** of quantized activations (validates variance‑sensitivity hypothesis). Apply Bonferroni correction if >1 layer. Log to `data/processed/logs/correlation_log.json`. **Note:** With 200 prompts the study is exploratory; power to detect |ρ| ≥ 0.2 is modest. | `data/processed/correlation_plot.png`, `data/processed/correlation_stats.json` |
| **1 – Rotation Matrix Generation** | FR‑003 – Cluster activation histograms per entropy bin (K‑Means → 16 bins), derive orthogonal rotation that best aligns the histogram centroid → matrix `M_i`. Store as `.npy` plus JSON metadata conforming to `rotation_matrix_schema`. Document layers, splits, boundaries. | `data/processed/rotation_matrices/matrix_{i}.npy`, `data/processed/rotation_matrices/metadata_{i}.json`, `data/processed/clustering_report.json` |
| **2 – Router Implementation** | FR‑004, FR‑005 – `router.py` reads lookup table, clamps out‑of‑range entropy, selects matrix, applies it inside `w2a4_engine.py`. Edge‑case handling (out‑of‑range, activation outliers, proxy failure) writes to `data/processed/logs/`. | Runtime logs under `data/processed/logs/` |
| **3 – Evaluation** | FR‑006‑FR‑009, SC‑002‑SC‑005 – Generate images with static baseline and dynamic router for the test split of multiple prompts., compute FID, CLIP, MSE, and **wall‑clock time**; perform **paired t‑tests** for each metric. Prior to testing, assess normality (Shapiro‑Wilk); if normality fails, fall back to **Wilcoxon signed‑rank** tests. Apply Bonferroni across the four tests. **Sensitivity Sweep**: shift each entropy boundary by ±5 % of the total entropy range, recompute FID distribution, report variance. | `data/processed/results.csv`, `figures/evaluation/*` |
| **4 – Reporting** | All SCs – Assemble tables/plots; each figure references a single row in `results.csv`. | `figures/` ready for downstream paper stage |

All tasks write only to `data/` or `figures/`. No `state/` writes.

## Compute Feasibility
- **CPU‑first**: Entropy proxy, validation, clustering, correlation, metric calculation run on the GitHub Actions runner. Data streamed from MS‑COCO via `datasets.load_dataset('coco2017', split='validation', streaming=True)` to keep RAM < 6 GB.  
- **GPU Escape Hatch**: Image generation (static & dynamic) uses `flux_wan_loader.py` with `device="cuda"` and `load_in_8bit=True` on Kaggle; the same code runs unchanged on the CI runner, which will automatically off‑load to Kaggle if CUDA is unavailable.

## Statistical Rigor
- **Spearman correlation** (rank‑based) between semantic entropy and activation variance, with partial control for `prompt_length`. Bonferroni correction for multiple layers.  
- **Correlation between activation variance and MSE** also tested with Spearman.  
- **Power note**: With 200 prompts, power to detect |ρ| ≥ 0.2 is modest ([deferred]); we treat results as exploratory.  
- **Paired t‑tests** for each evaluation metric (FID, CLIP, MSE, time) with **normality diagnostics**; if normality is violated, use **Wilcoxon signed‑rank** as a robust alternative. Bonferroni across the four tests; significance threshold *p* < 0.05.  
- No causal claims; all statements are associational per the constitution.  
- Collinearity diagnostics (VIF) reported for multi‑layer variance predictors.  

## Edge‑Case Handling (explicitly coded)
| Situation | Policy |
|-----------|--------|
| Entropy < `min_0` or > `max_15` | Clamp to nearest bin (0 or 15). |
| Activation variance outlier (z‑score > 3) | Log to `figures/outlier_log.png`; router falls back to the median matrix (index 8). |
| Entropy proxy failure (timeout, error) | Log to `data/processed/logs/proxy_failures.json`; router uses static baseline (median matrix). |

All logs are stored under `data/processed/logs/` to stay within project‑owned paths.

---



