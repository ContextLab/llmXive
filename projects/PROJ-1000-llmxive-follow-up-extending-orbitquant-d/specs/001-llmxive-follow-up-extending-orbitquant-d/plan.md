# Implementation Plan: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

**Branch**: `001-llmxive-followup` | **Date**: 2026-10-12 | **Spec**: `specs/001-llmxive-followup/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-followup/spec.md`

## Summary
The project will (1) compute a **semantic‑entropy** score for each MS‑COCO caption using a lightweight generative proxy **and validate this metric against established readability and language‑model perplexity measures** (construct‑validity step), (2) measure variance of intermediate DiT activations during **text‑to‑image generation** conditioned on that caption **using a single, CPU‑feasible DiT variant (Stable Diffusion 2.1)** for all correlation work, (3) test the Pearson correlation between entropy and activation variance **while controlling for prompt length and lexical richness**, (4) cluster prompts into multiple entropy bins, derive a rotation matrix per bin from activation histograms **and generate JSON metadata for each matrix** (FR‑003, VI‑VI), (5) implement a router that selects the appropriate matrix at inference **with explicit edge‑case handling** (FR‑004, FR‑005), (6) evaluate dynamic‑router quality versus the static OrbitQuant baseline using FID, CLIP, MSE, and wall‑clock time **including the required `rotation_index` column** (FR‑006‑FR‑009, SC‑002‑SC‑005). All steps are reproducible, write only to project‑owned directories (`data/`, `figures/`, `code/`), and respect the constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `diffusers==0.27.0`, `transformers==4.41.0`, `datasets==2.19.0`, `sentence-transformers==2.2.2`, `scikit-learn==1.5.0`, `numpy`, `pandas`, `fid-score==0.0.6` (CPU fork), `clip-score==0.0.5` (CPU fork), `accelerate`, `peft` (for 8‑bit loading).  
- **Target Platform**: GitHub Actions Linux runner (2 CPU cores, ~7 GB RAM, ~14 GB disk). GPU‑escape hatch to Kaggle free T4/P100 when a DiT model cannot run on CPU.  
- **Constraints**: No synthetic data; all artifacts stored under `data/` or `figures/`. No writes to platform‑owned `state/`.

## Constitution Check
| Principle | Status | How the plan satisfies it |
|-----------|--------|---------------------------|
| I. Reproducibility | PASS | Fixed random seeds in `code/config.py`; all data fetched via `datasets.load_dataset` with explicit revision; outputs written to `data/` and `figures/`. |
| II. Verified Accuracy | PASS | All citations will be validated by the Reference‑Validator before review. |
| III. Data Hygiene | PASS | Raw MS‑COCO parquet files stored under `data/raw/` with SHA‑256 checksums recorded in `data/checksums.json`. Transformations produce new files in `data/processed/`. |
| IV. Single Source of Truth | PASS | Every figure/table originates from CSV/JSON files under `data/processed/`. |
| V. Versioning Discipline | PASS | After each pipeline run a `data/artifact_hashes.json` (project‑owned) is updated with SHA‑256 hashes of all new artifacts; the Advancement‑Evaluator uses this for change detection. |
| VI. Dynamic Rotation Basis Validation | PASS | The clustering report (`data/processed/clustering_report.json`) documents layers, splits, and entropy boundaries; correlation test (including covariate control) must achieve *p* < 0.05 before proceeding to router implementation. |
| VII. W2A4 Regime Overhead Accounting | PASS | Phase 3 records per‑image inference time (`inference_time_ms`) for static and dynamic pipelines; any >2 % increase triggers a documented trade‑off. |

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
    └─ rotation_matrix_schema.schema.yaml

projects/PROJ-1000-llmxive-followup-extending-orbitquant-d/
├─ code/
│  ├─ __init__.py
│  ├─ config.py               # seeds, paths, hyper‑params
│  ├─ data/
│  │   ├─ download_coco.py
│  │   └─ preprocess.py
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
│  ├─ raw/                     # MS‑COCO parquet (read‑only)
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
| **0 – Correlation Study** | FR‑001, FR‑002, SC‑001 – Compute entropy (entropy_proxy), **validate** entropy (entropy_validation), run DiT (Stable Diffusion) on a set of stratified prompts, extract per‑layer variance, record prompt length & type‑token ratio, compute Pearson *r* and *p* (partial correlation controlling for length). Apply Bonferroni if >1 layer. Log to `data/processed/logs/correlation_log.json`. | `data/processed/correlation_plot.png`, `data/processed/correlation_stats.json` |
| **1 – Rotation Matrix Generation** | FR‑003 – Cluster activation histograms per entropy bin (clustering), derive orthogonal rotation matrices; generate **JSON metadata** (`metadata_i.json`) per matrix (rotation_matrix_schema). Document layers, splits, boundaries. | `data/processed/rotation_matrices/matrix_{i}.npy`, `data/processed/rotation_matrices/metadata_{i}.json`, `data/processed/clustering_report.json` |
| **2 – Router Implementation** | FR‑004, FR‑005 – `router.py` reads lookup table, clamps out‑of‑range entropy, selects matrix, applies it inside `w2a4_engine.py`. Edge‑case handling (out‑of‑range, activation outliers, proxy failure) writes to `data/processed/logs/` files. | Runtime logs under `data/processed/logs/` |
| **3 – Evaluation** | FR‑006‑FR‑009, SC‑002‑SC‑005 – Generate images with static baseline and dynamic router for the 40‑prompt test split, compute FID, CLIP, MSE, inference time; perform **paired t‑tests** (Bonferroni across four metrics); sweep entropy cut‑offs ±5 % and report FID variance. Include `rotation_index` column for dynamic rows. | `data/processed/results.csv`, `figures/evaluation/*` |
| **4 – Reporting** | All SCs – Assemble tables/plots; each figure references a single row in `results.csv`. | `figures/` ready for downstream paper stage |

All tasks write only to `data/` or `figures/`. No `state/` writes.

## Compute Feasibility
- **CPU‑first**: Entropy proxy, validation, clustering, correlation, metric calculation run on the CI CPU runner. Data streamed from MS‑COCO parquet (`datasets.load_dataset(..., streaming=True)`) to keep RAM < 6 GB.  
- **GPU Escape Hatch**: Image generation (static & dynamic) uses `flux_wan_loader.py` with `device="cuda"` and `load_in_8bit=True` on Kaggle; the same code runs unchanged on the CI runner, which will automatically off‑load to Kaggle if CUDA is unavailable.

## Statistical Rigor
- Pearson correlation (two‑tailed) with partial control for prompt length; Bonferroni correction for multiple layers.  
- Power note: 200 stratified prompts give >80 % power to detect |r| ≥ 0.2 at α = 0.05 (cited in research.md).  
- Paired t‑tests for each metric (FID, CLIP, MSE, time) with Bonferroni across four tests; significance threshold *p* < 0.05.  
- No causal claims; all statements are associational per the constitution.  
- Collinearity diagnostics (VIF) reported for multi‑layer variance predictors.  

## Edge‑Case Handling (explicitly coded)
| Situation | Policy |
|-----------|--------|
| Entropy < `min_0` or > `max_15` | Clamp to nearest bin (0 or 15). |
| Activation variance outlier (z‑score > 3) | Log to `figures/outlier_log.png`; router falls back to median matrix (index 8). |
| Entropy proxy failure (timeout, error) | Log to `data/processed/logs/proxy_failures.json`; router uses static baseline (median matrix). |

All logs are stored under `data/processed/logs/` to stay within project‑owned paths.

---

