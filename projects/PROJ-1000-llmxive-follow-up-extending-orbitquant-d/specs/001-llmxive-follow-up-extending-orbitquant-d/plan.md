# Implementation Plan: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

**Branch**: `001-llmxive-followup` | **Date**: 2026-10-18 | **Spec**: `specs/001-llmxive-followup/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-followup/spec.md`

## Summary
The project will (1) compute a **semantic‑entropy** score for each MS‑COCO caption using a lightweight language‑model proxy, (2) measure variance of intermediate DiT activations during a float32 forward pass, (3) test the **independent two‑sample t‑test** (or Mann‑Whitney U when normality fails) on variance differences between high‑entropy and low‑entropy groups **and** the **Spearman** correlation (controlling for covariates) between entropy and activation variance, (4) test the correlation between activation variance and **quantization MSE**, (5) cluster activation histograms into **K = 16** entropy bins and derive a rotation matrix per bin, (6) implement a router that selects the appropriate matrix at inference time with explicit edge‑case handling, and (7) evaluate the dynamic‑router pipeline against the static OrbitQuant baseline on FID, CLIP, MSE, and wall‑clock time, reporting statistical significance with **independent two‑sample t‑tests** (or Mann‑Whitney U) and a **Bonferroni** correction. All steps are reproducible, store artifacts under `data/` or `figures/`, and obey the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `diffusers==0.27.0`, `transformers==4.41.0`, `datasets==2.19.0`, `sentence-transformers==2.2.2`, `scikit-learn==1.5.0`, `numpy`, `pandas`, `fid-score==0.0.6` (CPU fork), `clip-score==0.0.5` (CPU fork), `accelerate`, `peft` (for 8‑bit loading).  
- **Target Platform**: GitHub Actions Linux runner (CPU‑first) with optional GPU‑escape hatch to Kaggle for image generation.  
- **Model Citations** (verified HuggingFace URLs):  
  - Entropy proxy: `google/t5-v1_1-small` – https://huggingface.co/google/t5-v1_1-small  
  - Readability/perplexity reference: `google/bert-base-uncased` – https://huggingface.co/google/bert-base-uncased  
  - Stable Diffusion 2.1 (CPU‑feasible DiT variant): `stabilityai/stable-diffusion-2-1` – https://huggingface.co/stabilityai/stable-diffusion-2-1  
  - FLUX‑dev (GPU‑escape option): `black-forest-labs/flux-dev` – https://huggingface.co/black-forest-labs/flux-dev  

## Constitution Check

| Principle | Status | How the plan satisfies it |
|-----------|--------|---------------------------|
| I. Reproducibility | PASS | Fixed seeds (`code/config.py`); data streamed via `datasets.load_dataset('coco2017', split='validation', streaming=True)`; outputs only to `data/` and `figures/`. |
| II. Verified Accuracy | PASS | All model and dataset URLs are verified; citations will be validated by the Reference‑Validator. |
| III. Data Hygiene | PASS | Raw COCO files stored under `data/raw/` with SHA‑256 checksums (`data/checksums.json`). Transformations write new files (`data/processed/`). |
| IV. Single Source of Truth | PASS | Every figure/table references a single row in `data/processed/results.csv` or a specific JSON record. |
| V. Versioning Discipline | PASS | After each pipeline run `data/artifact_hashes.json` is updated with SHA‑256 hashes; Advancement‑Evaluator uses these hashes. |
| VI. Dynamic Rotation Basis Validation | PASS | **Phase 0** now includes: <br>• Power Assurance (≥800 prompts → ≥80 % power for d ≥ 0.2). <br>• Independent two‑sample t‑test (or Mann‑Whitney U) on variance differences between high‑ and low‑entropy groups, with Bonferroni correction across layers. <br>• Paired‑t‑test requirement removed. <br>• Detailed clustering report (`data/processed/clustering_report.json`) documents layers, splits, and entropy boundaries. Router construction proceeds only after the power‑assured test yields *p* < 0.05 **or** the observed effect size exceeds the pre‑registered threshold (Cohen’s d ≥ 0.2). |
| VII. W2A4 Regime Overhead Accounting | PASS | Phase 3 records per‑image inference time for static and dynamic pipelines; any >2 % overhead is flagged for trade‑off documentation. |

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
│      │   └─ *.json           # one JSON per activation measurement
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
| **0 – Correlation & Sensitivity Study** | **FR‑001, FR‑002, FR‑009, FR‑010, SC‑001, VI** – <br>1. **Schema Validation**: `code/analysis/correlation.py` validates `prompts.csv` against `contracts/prompt_schema.schema.yaml` **and** `entropy_scores.csv` against `contracts/entropy_schema.schema.yaml` using `jsonschema`. Failures abort the pipeline. <br>2. **Semantic Entropy** (entropy_proxy) with 30 Monte‑Carlo samples per prompt, fixed seed, uniform token‑dropout. <br>3. **Covariate Collection** (`prompt_length`, `lexical_richness`, `image_entropy`, `syntactic_complexity`). <br>4. **Activation Variance & MSE**: run Stable Diffusion 2.1 (CPU‑feasible DiT) on **≥800** stratified prompts. Record per‑layer variance and quantization MSE. <br>5. **Power Assurance**: a priori G*Power analysis confirms ≥800 prompts give ≥80 % power to detect effect size d ≥ 0.2 at α = 0.05 (SC‑001). If power falls below 80 %, the pipeline automatically expands to **[deferred]** prompts before proceeding. <br>6. **Statistical Tests**: <br> - **Independent two‑sample t‑test** (or Mann‑Whitney U when Shapiro‑Wilk rejects normality) comparing variance of **high‑entropy** (top [deferred]) vs **low‑entropy** (bottom [deferred]) groups, matched on covariates via nearest‑neighbor on the covariate vector. <br> - **Bonferroni** correction across the *L* measured layers (α_adj = 0.05 / L). <br> - **Spearman ρ** between entropy and activation variance (partial correlation controlling for the four covariates). <br> - **Spearman ρ** between activation variance and MSE. <br> - **Collinearity Diagnostics**: VIF for multi‑layer variances; report any VIF > 5. <br>7. **Decision Rule**: Proceed to router construction if (a) the two‑sample test yields *p* < 0.05 **or** (b) the observed effect size (Cohen’s d or rank‑biserial) ≥ 0.2, satisfying the power‑assured threshold. <br>8. Log all results to `data/processed/logs/correlation_log.json`. | `data/processed/correlation_plot.png`, `data/processed/correlation_stats.json` |
| **1 – Rotation Matrix Generation** | **FR‑003** – Cluster activation histograms per entropy bin (K‑Means → 16 bins) on the **training split of 600 prompts** (subset of the 800). Derive orthogonal rotation matrix per bin, store as `.npy` + JSON metadata conforming to `rotation_matrix_schema`. Validate each metadata JSON against the schema. Document layers, splits, boundaries. | `data/processed/rotation_matrices/matrix_{i}.npy`, `data/processed/rotation_matrices/metadata_{i}.json`, `data/processed/clustering_report.json` |
| **2 – Router Implementation** | **FR‑004, FR‑005** – `router.py` reads `rotation_lookup.json`, clamps out‑of‑range entropy, selects matrix, applies it inside `w2a4_engine.py`. Edge‑case handling (out‑of‑range, activation outliers, proxy failure) writes to logs. | Runtime logs under `data/processed/logs/` |
| **3 – Evaluation** | **FR‑006‑FR‑009, SC‑002‑SC‑005** – Generate images with **static baseline** and **dynamic router** for a **held‑out test set of 200 prompts** (distinct from the 800‑prompt pool). Compute **FID** (`fid-score` CPU fork), **CLIP** (`clip-score` CPU fork), **MSE**, and **inference_time_ms** (wall‑clock). <br>   - **Statistical Tests**: for each metric, assess normality (Shapiro‑Wilk). If normal, paired t‑test; otherwise Wilcoxon signed‑rank. Apply Bonferroni across the four metrics. <br>   - **Sensitivity Sweep**: shift each entropy boundary by ±5 % of the total range, recompute FID across 5 random seeds, report σ of FID scores. | `data/processed/results.csv`, `figures/evaluation/*` |
| **4 – Reporting** | All SCs – Assemble tables/plots; each figure/table references a single row in `results.csv`. | `figures/` ready for downstream paper stage |

All tasks write only to `data/` or `figures/`. No `state/` writes.

## Compute Feasibility & Hardware Strategy
- **CPU‑first**: Entropy proxy, validation, clustering, correlation, and metric calculation run on the GitHub Actions runner. Data streamed via `datasets.load_dataset('coco2017', split='validation', streaming=True)` to keep RAM < 6 GB.  
- **GPU Escape Hatch**: Image generation (static & dynamic) uses `flux_wan_loader.py` with `device="cuda"` and `load_in_8bit=True` on Kaggle; the same code runs unchanged on the CI runner, which will automatically off‑load to Kaggle if CUDA is unavailable.

## Statistical Rigor
- **Independent two‑sample t‑test** (or Mann‑Whitney U) on variance differences between high‑ and low‑entropy groups, Bonferroni‑corrected across layers.  
- **Spearman** correlations (entropy ↔ variance, variance ↔ MSE) with partial control for four covariates; Bonferroni correction for multiple layers.  
- **Power note**: 800 prompts provide ≥ 80 % power to detect effect size *d* ≥ 0.2 at α = 0.05 (SC‑001). If the power analysis reports < 80 %, the pipeline expands to **[deferred]** prompts before proceeding.  
- **Normality diagnostics** (Shapiro‑Wilk) before paired tests; Wilcoxon fallback.  
- **Bonferroni** across the four evaluation metrics (FID, CLIP, MSE, time).  
- **Collinearity**: VIF computed for multi‑layer variance predictors; if VIF > 5, report and avoid claiming independent effects.  
- No causal claims; all statements are associational per Constitution VI.

## Edge‑Case Handling (explicitly coded)
| Situation | Policy |
|-----------|--------|
| Entropy < `min_0` or > `max_15` | Clamp to nearest bin (0 or 15). |
| Activation variance outlier (z‑score > 3) | Log to `figures/outlier_log.png`; router falls back to median matrix (index 8). |
| Entropy proxy failure (timeout, error) | Log to `data/processed/logs/proxy_failures.json`; router uses static baseline (median matrix). |

All logs are stored under `data/processed/logs/`.

---


