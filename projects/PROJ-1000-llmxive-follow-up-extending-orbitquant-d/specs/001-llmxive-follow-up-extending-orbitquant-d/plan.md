# Implementation Plan: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

**Branch**: `001-llmxive-followup` | **Date**: 2026-10-23 | **Spec**: `specs/001-llmxive-followup/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-followup/spec.md`

## Summary
The project will (1) compute semantic‑entropy scores for MS‑COCO captions using a lightweight language‑model proxy, (2) measure variance of intermediate DiT activations during a float32 forward pass (offloaded to GPU), (3) test the correlation between entropy, activation variance, and quantization MSE using paired t-tests via nearest-neighbor matching, (4) cluster activation histograms into K = 16 bins and derive a rotation matrix per bin, (5) implement a router that selects the appropriate matrix at inference time using the clustering report as a lookup table, and (6) evaluate the dynamic‑router pipeline against the static OrbitQuant baseline on FID, CLIP, MSE, and wall‑clock time. All steps are reproducible, store artifacts under `data/` or `figures/`, and obey the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `diffusers==0.27.0`, `transformers==4.41.0`, `datasets==2.19.0`, `sentence-transformers==2.2.2`, `scikit-learn==1.5.0`, `numpy`, `pandas`, `fid-score==0.0.6` (CPU fork), `clip-score==0.0.5` (CPU fork), `accelerate`, `peft` (for 8‑bit loading).  
- **Target Platform**: GitHub Actions Linux runner (CPU‑first) with GPU‑escape hatch to Kaggle for all DiT forward passes.  
- **Model Citations (verified URLs)**:  
  - Entropy proxy: `google/t-v1_1-small` – https://huggingface.co/google/t5-v1_1-small  
  - Readability/perplexity reference: `google/bert-base-uncased` – https://huggingface.co/google/bert-base-uncased  
  - Stable Diffusion (CPU‑feasible DiT variant): `stabilityai/stable-diffusion` – https://huggingface.co/stabilityai/stable-diffusion  
  - FLUX‑dev (GPU‑escape option): `black-forest-labs/flux-dev` – https://huggingface.co/black-forest-labs/flux-dev  

## Constitution Check

| Principle | Status | How the plan satisfies it |
|-----------|--------|---------------------------|
| I. Reproducibility | PASS | Fixed seeds; streaming data download; deterministic file naming; all outputs written under `data/` and `figures/`. |
| II. Verified Accuracy | PASS | All model and dataset URLs are verified; citations will be validated by the Reference‑Validator. |
| III. Data Hygiene | PASS | Raw COCO files stored under `data/raw/` with SHA‑256 checksums; transformations write new files under `data/processed/`. |
| IV. Single Source of Truth | PASS | Every figure/table references a single row in `data/processed/results.csv` or a specific JSON record. |
| V. Versioning Discipline | PASS | After each pipeline run `data/artifact_hashes.json` records SHA‑256 hashes; Advancement‑Evaluator uses these hashes. |
| VI. Dynamic Rotation Basis Validation | PASS | Phase 0 includes power‑assured correlation tests (paired t-test, Spearman, Bonferroni). Router construction proceeds only if significance or effect‑size thresholds are met. |
| VII. W2A4 Regime Overhead Accounting | PASS | Phase 3 records per‑image inference time for static and dynamic pipelines; any > 2 % overhead is flagged for trade‑off documentation. |

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
    ├─ prompt_schema.schema.yaml
    ├─ entropy_schema.schema.yaml
    └─ clustering_report_schema.schema.yaml

projects/PROJ-1000-llmxive-followup-extending-orbitquant-d/
├─ code/
│  ├─ __init__.py
│  ├─ config.py               # seeds, paths, hyper‑params
│  ├─ models/
│  │   ├─ dit_wrapper.py      # hooks for variance measurement (Stable Diffusion 2.1)
│  │   └─ flux_wan_loader.py  # GPU‑escape loader (8‑bit optional)
│  ├─ analysis/
│  │   ├─ entropy_proxy.py    # lightweight LM → entropy (T5‑small)
│  │   ├─ entropy_validation.py # readability & perplexity cross‑check
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
│      │   └─ *.json
│      ├─ rotation_matrices/
│      │   ├─ matrix_0.npy
│      │   ├─ metadata_0.json
│      │   └─ … matrix_15.npy / metadata_15.json
│      ├─ clustering_report.json
│      ├─ correlation_plot.png
│      ├─ correlation_stats.json
│      ├─ results.csv          # includes `rotation_index` column for dynamic rows
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
| **0 – Correlation & Sensitivity Study** | **FR‑001, FR‑002, FR‑009, FR‑010, SC‑001, VI** – <br>1. Schema validation of `prompts.csv` and `entropy_scores.csv`. <br>2. Compute semantic entropy (using multiple Monte‑Carlo samples, fixed seed, uniform token‑dropout). <br>3. Record covariates (`prompt_length`, `lexical_richness`, `image_entropy`, `syntactic_complexity`). <br>4. Run Stable Diffusion 2.1 on **≥800** stratified prompts (**offloaded to GPU escape hatch**); capture per‑layer activation variance and W2A4 MSE. <br>5. Power assurance (≥800 prompts → ≥80 % power for d ≥ 0.2). <br>6. Statistical tests: paired t‑test (via nearest‑neighbor matching on covariates) on high‑ vs low‑entropy variance, Bonferroni‑corrected across layers; Spearman ρ between entropy & variance (partial on covariates); Spearman ρ between variance & MSE; VIF collinearity diagnostics. <br>7. Decision rule: proceed to router if *p* < 0.05 **or** effect size ≥ 0.2. <br>8. Log results to `data/processed/logs/correlation_log.json`. | `data/processed/correlation_plot.png`, `data/processed/correlation_stats.json` |
| **1 – Rotation Matrix Generation** | **FR‑003** – Cluster activation histograms per entropy bin (K‑Means → 16 bins) on a **training split of 600 prompts**. Derive orthogonal rotation matrix per bin, store as `.npy` + JSON metadata conforming to `rotation_matrix_schema`. Validate each metadata JSON. Document layers, splits, boundaries. | `data/processed/rotation_matrices/matrix_{i}.npy`, `data/processed/rotation_matrices/metadata_{i}.json`, `data/processed/clustering_report.json` |
| **2 – Router Implementation** | **FR‑004, FR‑005** – `router.py` reads `clustering_report.json` to map entropy to matrix index, clamps out‑of‑range entropy, selects matrix, applies it inside `w2a4_engine.py`. Edge‑case handling (out‑of‑range, activation outliers, proxy failure) writes to logs. | Runtime logs under `data/processed/logs/` |
| **3 – Evaluation** | **FR‑006‑FR‑009, SC‑002‑SC‑005** – Generate images with **static baseline** and **dynamic router** for a **held‑out test set of 200 prompts** (**offloaded to GPU escape hatch**). Compute **FID**, **CLIP**, **MSE**, and **inference_time_ms**. <br>   - Statistical tests: normality (Shapiro‑Wilk); paired t‑test or Wilcoxon signed‑rank; Bonferroni across four metrics. <br>   - Sensitivity sweep: shift each entropy boundary by ±5 % of total range, recompute FID across 5 seeds, report σ of FID scores. | `data/processed/results.csv`, `figures/evaluation/*` |
| **4 – Reporting** | Assemble tables/plots; each figure/table references a single row in `results.csv`. | `figures/` ready for downstream paper stage |

All tasks write only to `data/` or `figures/`. No `state/` writes.

## Compute Feasibility & Hardware Strategy
- **CPU‑first**: Entropy proxy, validation, clustering, correlation, and metric calculation run on the GitHub Actions runner. Data streamed via `datasets.load_dataset('coco2017', split='validation', streaming=True)` to keep RAM < 6 GB.  
- **GPU Escape Hatch**: All DiT forward passes, including activation variance measurement (Phase 0) and image generation (Phase 3), use `flux_wan_loader.py` with `device="cuda"` and `load_in_8bit=True` on Kaggle; the same code runs unchanged on the CI runner, which will automatically off‑load to Kaggle if CUDA is unavailable.

## Statistical Rigor
- Paired t‑test (via nearest-neighbor matching on covariates) on variance differences, Bonferroni‑corrected across layers.  
- Spearman correlations (entropy ↔ variance, variance ↔ MSE) with partial control for covariates; Bonferroni across layers.  
- Power analysis guarantees ≥ 80 % power for effect size d ≥ 0.2 with ≥ 800 prompts.  
- Normality diagnostics (Shapiro‑Wilk) before paired tests; Wilcoxon fallback.  
- Bonferroni across the four evaluation metrics (FID, CLIP, MSE, time).  
- VIF collinearity check; any VIF > 5 reported.  
- All statements remain associational per Constitution VI.

## Edge‑Case Handling (explicitly coded)
| Situation | Policy |
|-----------|--------|
| Entropy < `min_0` or > `max_15` | Clamp to nearest bin (0 or 15). |
| Activation variance outlier (z‑score > 3) | Log to `figures/outlier_log.png`; router defaults to median matrix (index 8). |
| Entropy proxy failure (timeout, error) | Log to `data/processed/logs/proxy_failures.json`; router falls back to static baseline (median matrix). |

All logs are stored under `data/processed/logs/`.