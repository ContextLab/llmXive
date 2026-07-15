# Research: Quantization Robustness of Multi-Effect LoRA Adapters

## Research Question

Does post‑training quantization (INT8, INT4) of a multi‑effect LoRA adapter (CollectionLoRA) induce significant **concept bleeding**—measured by Cross‑Effect Similarity Ratio (CESR)—and is this degradation correlated with the **effective rank** of each effect’s subspace?

## Methodology

### 1. Experimental Design

| Variable | Levels |
|----------|--------|
| **Quantization** | FP16 (baseline), INT8, INT4 |
| **Effect** | 5 distinct effects (e.g., *oil painting*, *cyberpunk*, *watercolor*, *sketch*, *pixel art*) |
| **Prompt** | A set of deterministic prompts, each uniquely paired with one effect. (one‑to‑one mapping) – see `data/prompts.txt`. |

*The one‑to‑one mapping eliminates the need to model prompts as random effects, stabilising the Pooled Bayesian Linear Model (P-BLM) with only 5 data points per quantization level.*

### 2. Dataset Strategy

| Component | Source |
|-----------|--------|
| **Base Model** | `stabilityai/stable-diffusion-1-5` (HuggingFace) |
| **CollectionLoRA Adapter** | `user/collectionlora-multi-teacher-onp` (HuggingFace model ID). *Note: This adapter ID is a placeholder and must be verified against the 'Verified datasets' block before execution. If no verified ID exists, the pipeline halts.* |
| **Prompts** | Fixed list in `data/prompts.txt`. |
| **Reference Images (for CESR)** | **LoRA-FreeReferenceImages**: Generated **without** the LoRA adapter for all effects. These serve as the ground truth for measuring 'bleeding' (convergence to other LoRA effects). This breaks the circularity of comparing quantized outputs to LoRA-generated references. |

All assets are fetched programmatically on each CI run, guaranteeing reproducibility (Constitution Principle I).

### 3. Metric Suite

| Metric | Description | Implementation |
|--------|-------------|----------------|
| **Cosine Similarity (CLIP)** | Prompt‑text embedding vs. generated‑image embedding (semantic adherence). | `metrics.py` uses `transformers` CLIP model. |
| **Style‑Classifier Score** | Probability that the image belongs to the intended style (trained on WikiArt). | Lightweight CNN (`torchvision` ResNet‑18) fine‑tuned on style labels; runs on CPU. **Validated on a hold-out set before use.** |
| **LPIPS** | Perceptual distance between quantized image and its FP16 counterpart (pixel‑space fidelity). | `lpips` library (CPU mode). |
| **CESR (Max)** | For a quantized image, compute the **maximum** cosine similarity to the `LoRA-FreeReferenceImages` of the **other four** effects (excluding the target). This measures the worst-case bleeding (convergence to the nearest competing effect). | Implemented in `metrics.py`. |
| **Delta Metrics** | Differences (quantized − FP16) for each of the above scores. | Simple arithmetic after metric extraction. |

### 4. Statistical Analysis Plan

1. **Pooled Bayesian Linear Model (P-BLM)**  
   *Outcome*: cosine similarity (and LPIPS) per image.  
   *Fixed effects*: quantization level (FP16, INT8, INT4), effect ID.  
   *Pooled Variance*: The model assumes a **shared residual variance (sigma)** across all effects and quantization levels. This pooling allows estimation of quantization effects despite N=1 per cell (A series of observations will be conducted.).  
   Priors are weakly informative (Normal (0, 0.5) for quantization offsets; Half‑Cauchy for shared residual variance). Posterior samples are drawn with NUTS.  

2. **Posterior Width Check (FR‑014)** – Compute the [deferred] HDI width for each quantization effect; flag “Underpowered” if width > 0.2.

3. **Correlation Analysis** – Bayesian linear regression of **CESR delta** (quantized − FP16) against **subspace rank** (from `data/subspace_ranks.json`). Report posterior mean, [deferred] HDI, and a significance flag (HDI does not cross zero).

4. **Multiple‑Comparison Handling** – Joint posterior inference inherently adjusts for multiple parameters; we also report the Bayesian False Discovery Rate where applicable.

All statistical code resides in `analysis/` and adheres to the reproducibility requirements (Constitution Principle I).

### 5. Compute Feasibility & Constraints

- **Images**: 5 effects × 3 quantization levels = 15 generations.
- **Runtime**: ~ mins per image on CPU (SD 1.5, A reduced number of steps for quantized models, 50 for FP16) → **≈ 3.5 h total**.
- **Memory**: Model loading uses `torch.load(..., mmap=True)`; peak RAM ≤ 6 GB.
- **Hardware**: GitHub Actions free tier (2 CPU, ~7 GB RAM). No GPU or CUDA.

If a `MemoryError` (exit 137) occurs during quantized generation, the pipeline logs a “Quantization Failure” flag and continues with remaining levels.

### 6. Edge‑Case Handling

| Situation | Handling |
|-----------|----------|
| `torch.ao.quantization` unavailable | Log “Quantization Backend Unavailable – skipping INT8/INT4” and **skip** those levels (no fallback). |
| OOM (`MemoryError`) during generation | Catch, log “Quantization Failure – level X skipped”, and proceed. |
| Zero delta (identical embeddings) | Record delta = 0.0; variance calculations use a small epsilon to avoid division-by-zero. |
| Missing adapter URL in verified block | Load via `from_pretrained`; flag in the report that the adapter source is not verified. |
| Runtime > 3.5h | Reduce inference steps for quantized levels to 10 (graceful degradation). |

## Expected Results

- **SC‑001**: Baseline cosine similarity scores (FP16) for each effect‑prompt pair.  
- **SC‑002**: LPIPS and style‑classifier deltas for INT8/INT4 vs. FP16.  
- **SC‑003**: Posterior probability that INT8/INT4 quantization reduces cosine similarity (target > 0.95).  
- **SC‑004**: Posterior correlation coefficient between subspace rank and CESR delta; credible interval not crossing zero indicates a significant relationship.  
- **SC‑005**: Total pipeline runtime ≤ 6 h (expected ≈ 3.5 h).  
- **SC‑006**: CESR values for each quantized image compared to LoRA-FreeReferenceImages.

All results will be stored in `data/analysis_results.json` and validated against the provided schemas.