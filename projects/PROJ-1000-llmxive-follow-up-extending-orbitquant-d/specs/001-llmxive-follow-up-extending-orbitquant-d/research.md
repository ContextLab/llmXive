# Research: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

## Executive Summary
We test whether **semantic entropy** of MS‑COCO captions predicts **activation variance** in a Diffusion Transformer (DiT) during generation, and whether that variance predicts quantization error (MSE). A significant correlation justifies a **dynamic rotation router** that selects one of several pre‑computed rotation matrices based on entropy. The study proceeds through four phases (correlation, matrix generation, router implementation, evaluation) and reports quantitative gains in FID, CLIP, and MSE while keeping inference overhead ≤ 2 %.

## Dataset Strategy

| Dataset | Source | Role |
|---------|--------|------|
| **MS‑COCO 2017 (images + captions)** | `coco2017` (HuggingFace, https://huggingface.co/datasets/coco2017) | Provides both image files for activation‑variance measurement, FID/CLIP evaluation, and the caption texts used as prompts. |

All datasets are publicly downloadable via `datasets.load_dataset`. No gated data are used.

## Methodological Rigor & Statistical Plan

### 1. Data Point Construction
For each sampled caption (`prompt_id` = MS‑COCO `image_id`):
1. **Semantic Entropy**:  
   - Generate *S* = 5 paraphrases using `google/t5-v1_1-small` (temperature 0.7).  
   - Embed original + paraphrases with `sentence-transformers/all-MiniLM-L6-v2`.  
   - Cluster embeddings into *K* = 3 groups via K‑Means, compute Shannon entropy of the cluster distribution → `semantic_entropy`.  
   - **Construct‑Validity Check**: also compute (a) Flesch‑Kincaid readability scores and (b) perplexity using `google/bert-base-uncased`. Correlate each with our entropy; require |ρ| > 0.5 with at least one external measure before proceeding. |
2. **Covariates**:  
   - Token count (`prompt_length`) and type‑token ratio (`lexical_richness`) are recorded for each prompt. |
3. **Activation Variance & MSE**:  
   - Run **Stable Diffusion 2.1** (CPU‑feasible DiT variant) conditioned on the caption.  
   - Hook into selected intermediate layers (e.g., `self_attn`, `mlp`) and record variance of the activation tensor across diffusion timesteps.  
   - After the float32 pass, quantize the same activations with the W2A4 scheme and compute Mean Squared Error (MSE) against the float32 reference. |
The tuple `(semantic_entropy, activation_variance, mse, prompt_length, lexical_richness)` is saved in `data/processed/pairs.csv`.

### 2. Correlation Analysis (FR‑001, FR‑002, FR‑009, SC‑001)
- Compute **Spearman** ρ and two‑tailed *p* across the 200 stratified pairs for (a) entropy ↔ activation variance and (b) activation variance ↔ MSE.  
- Perform **partial correlation** controlling for `prompt_length` (and optionally `lexical_richness`).  
- If variance is extracted for *L* > 1 layers, apply **Bonferroni correction**: α_adj = 0.05 / L.  
- Also compute Spearman correlation between **activation variance** and **MSE** to validate the variance‑sensitivity hypothesis.  
- Report VIF for multi‑layer variance to assess collinearity.  
- **Power note**: with 200 prompts, power to detect |ρ| ≥ 0.2 is modest; results are exploratory.

### 3. Dynamic Router Construction (FR‑003‑FR‑005, VI‑VI)
- **Training split**: 160 prompts.  
- **Clustering**: K‑Means on `semantic_entropy` → 16 bins → entropy boundaries `[min_i, max_i]`.  
- **Matrix Derivation**: For each bin, aggregate activation histograms of its prompts, compute the principal‑component rotation that best aligns the histogram centroid → orthogonal matrix `M_i`.  
- Save matrices as `data/processed/rotation_matrices/matrix_{i}.npy` **and** accompanying JSON metadata `metadata_{i}.json` conforming to `rotation_matrix_schema`.  
- **Lookup Table**: `data/processed/rotation_lookup.json` maps entropy ranges to matrix indices.  

### 4. Evaluation (FR‑006‑FR‑009, SC‑002‑SC‑005)
- **Test split**: 40 unseen prompts.  
- Generate images with **static baseline** (single OrbitQuant matrix) and **dynamic router** (selected `M_i`).  
- Compute **FID** (`fid-score` CPU fork), **CLIP** (`clip-score` CPU fork), **MSE** of quantized activations, and **inference_time_ms** (wall‑clock).  
- Perform **paired t‑tests** for each metric; first assess normality of the paired differences with Shapiro‑Wilk. If normality fails, fall back to **Wilcoxon signed‑rank** tests. Apply Bonferroni across the four tests.  
- **Sensitivity Sweep**: shift each entropy boundary by ±5 % of the total entropy range, recompute FID distribution, report variance.  

### 5. Reporting
All figures (scatter plot, entropy histogram, boxplots of metrics) are saved under `figures/`. Tables are derived from `data/processed/results.csv`. Every figure references a single row in that CSV (Single Source of Truth).

## Compute Feasibility & Hardware Strategy
- **CPU‑first**: Entropy proxy, validation, clustering, correlation, metric calculation run on the GitHub Actions runner. Data streamed to keep RAM < 6 GB.  
- **GPU Escape Hatch**: Image generation (static & dynamic) uses `flux_wan_loader.py` with `device="cuda"` and `load_in_8bit=True` on Kaggle; the same code runs unchanged on the CI runner, which will automatically off‑load to Kaggle if CUDA is unavailable.  

## Edge‑Case Handling (as implemented)
| Situation | Policy |
|-----------|--------|
| Entropy < `min_0` or > `max_15` | Clamp to nearest bin (0 or 15). |
| Activation variance outlier (z‑score > 3) | Log to `figures/outlier_log.png`; router falls back to the median matrix (index 8). |
| Entropy proxy failure (timeout, error) | Log to `data/processed/logs/proxy_failures.json`; router uses static baseline (median matrix). |

All logs are stored under `data/processed/logs/` to stay within project‑owned paths.

---



