# Research: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

## Executive Summary
We test whether **semantic entropy** of MS‑COCO captions predicts **activation variance** in a Diffusion Transformer (DiT) during generation, and whether that variance predicts quantization error (MSE). A **paired t-test** (via nearest-neighbor matching on covariates) on variance differences between high‑entropy and low‑entropy groups (≥ 800 prompts) **or** a significant Spearman correlation validates the hypothesis and justifies a **dynamic rotation router** that selects one of several pre‑computed rotation matrices based on entropy. The study proceeds through four phases (correlation, matrix generation, router implementation, evaluation) and reports quantitative gains in FID, CLIP, and MSE while keeping inference overhead ≤ 2 %.

## Dataset Strategy

| Dataset | Source | Role |
|---------|--------|------|
| **MS‑COCO 2017 (images + captions)** | `coco2017` – https://huggingface.co/datasets/coco2017 | Provides image files for activation‑variance measurement, FID/CLIP evaluation, and captions as prompts. |

All datasets are publicly downloadable via `datasets.load_dataset`. No gated data are used.

## Methodological Rigor & Statistical Plan

### 1. Data Point Construction (≥ 800 prompts)
For each sampled caption (`prompt_id` = COCO `image_id`):
1. **Semantic Entropy** (FR‑001):  
   - Generate *S* = 5 paraphrases using `google/t5-v1_1-small` (temperature 0.7).  
   - Embed original + paraphrases with `sentence-transformers/all-MiniLM-L6-v2`.  
   - Cluster embeddings into *K* = 3 groups via K‑Means, compute Shannon entropy of the cluster distribution → `semantic_entropy`.  
   - **Validity Check**: also compute (a) Flesch‑Kincaid readability and (b) perplexity using `google/bert-base-uncased`. Require a statistically significant correlation (p < 0.05) with entropy to pass validation. |
2. **Covariates**: `prompt_length`, `lexical_richness`, `image_entropy` (pixel‑level Shannon entropy), `syntactic_complexity`. |
3. **Activation Variance & MSE** (FR‑002, FR‑009):  
   - Run **Stable Diffusion 2.1** (CPU‑feasible DiT variant) conditioned on the caption (**offloaded to GPU escape hatch**).  
   - Hook into selected intermediate layers (`self_attn`, `mlp`) and record variance of activation tensors across diffusion timesteps.  
   - Quantize the same activations with the W2A4 scheme and compute Mean Squared Error (MSE) against the float32 reference. |
The tuple `(semantic_entropy, activation_variance, mse, prompt_length, lexical_richness, image_entropy, syntactic_complexity)` is saved in `data/processed/pairs.csv`.

### 2. Power Assurance & Decision Rule (SC‑001)
A priori G*Power analysis shows that **≥800** prompts give **≥80 %** power to detect an effect size *d* ≥ 0.2 at α = 0.05. If computed power falls below 80 % the pipeline automatically expands to **[deferred]** prompts before proceeding.

**Decision Rule**: Proceed to router construction if (a) the paired t-test yields *p* < 0.05 **or** (b) the observed effect size (Cohen’s d or rank‑biserial) ≥ 0.2, satisfying the power‑assured threshold.

### 3. Correlation & Paired T-Test (FR‑010, SC‑001, VI)

- **Paired t-test**: Split the 800 prompts into **high‑entropy** (top X %) and **low‑entropy** (bottom X %) groups. Match each high‑entropy prompt to a low‑entropy prompt on `prompt_length` and `lexical_richness` (nearest‑neighbor on the covariate vector). Compute variance difference for each pair and run a two‑tailed paired t‑test (or Wilcoxon signed‑rank if Shapiro‑Wilk rejects normality). Apply Bonferroni correction across the *L* measured layers (α_adj = 0.05 / L).
- **Spearman Correlation**: Compute Spearman ρ between entropy and activation variance, controlling for the four covariates via partial correlation. Apply Bonferroni across layers.  
- **Variance‑MSE Correlation**: Compute Spearman ρ between activation variance and MSE to validate the variance‑sensitivity hypothesis.  
- **Collinearity Diagnostics**: Calculate VIF for the set of layer variances; report any VIF > 5.  
All results are logged to `data/processed/logs/correlation_log.json`.

### 4. Dynamic Router Construction (FR‑003‑FR‑005, VI)

- **Training split**: 600 prompts (subset of the 800).  
- **Clustering**: K‑Means on `semantic_entropy` → an appropriate set of entropy bins.; record boundaries in `data/processed/clustering_report.json`.  
- **Matrix Derivation**: For each bin, aggregate activation histograms, compute the principal‑component rotation that aligns the centroid → orthogonal matrix `M_i`. Save as `.npy` and accompanying JSON metadata (`rotation_matrix_schema`). Validate the JSON against the schema immediately after generation.  
- **Lookup Table**: The `clustering_report.json` serves as the lookup table, mapping entropy ranges to matrix indices.

### 5. Evaluation (FR‑006‑FR‑009, SC‑002‑SC‑005)

- **Test split**: 200 **unseen** prompts (distinct from the 800‑prompt pool).  
- Generate images with **static baseline** and **dynamic router** (**offloaded to GPU escape hatch**).  
- Compute **FID** (`fid-score` CPU fork), **CLIP** (`clip-score` CPU fork), **MSE**, and **inference_time_ms** (wall‑clock).  
- **Statistical Tests**: For each metric, assess normality (Shapiro‑Wilk). If normal, run a paired t‑test; otherwise, use Wilcoxon signed‑rank. Apply Bonferroni across the four metrics (α_adj = 0.05 / 4).  
- **Sensitivity Sweep**: Shift each entropy boundary by ±5 % of the total entropy range, recompute FID across multiple random seeds, report σ of FID scores.  

### 6. Reporting
All figures (scatter plots, entropy histograms, boxplots) are saved under `figures/`. Tables are derived from `data/processed/results.csv`. Each figure/table traces back to a single row in that CSV (Single Source of Truth).

## Compute Feasibility & Hardware Strategy
- **CPU‑first**: Entropy proxy, validation, clustering, correlation, and metric computation run on the GitHub Actions runner; data streamed to keep RAM < 6 GB.  
- **GPU Escape Hatch**: All DiT forward passes, including variance measurement (Phase 0) and image generation (Phase 3), use `flux_wan_loader.py` with `device="cuda"` and `load_in_8bit=True` on Kaggle; the same script runs unchanged on the CI runner, which will off‑load to Kaggle if CUDA is unavailable.

## Edge‑Case Handling (as implemented)
| Situation | Policy |
|-----------|--------|
| Entropy out‑of‑range | Clamp to nearest bin (0 or 15). |
| Activation variance outlier (z‑score > 3) | Log to `figures/outlier_log.png`; router defaults to median matrix (index 8). |
| Entropy proxy failure (timeout/error) | Log to `data/processed/logs/proxy_failures.json`; router falls back to static baseline (median matrix). |

All logs are stored under `data/processed/logs/`.