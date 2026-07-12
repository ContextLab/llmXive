# Research: Quantization Robustness of Multi-Effect LoRA Adapters

## 1. Problem Statement & Hypothesis

**Problem**: The `CollectionLoRA` architecture allows multiple distinct visual effects to be stored in a single LoRA adapter using Asymmetric Orthogonal Prompting. However, deploying these models on edge devices often requires quantization (INT8/INT4). There is a risk that quantization noise will destroy the orthogonality of the subspaces, leading to "concept bleeding" (e.g., an "oil painting" prompt triggering "neon lights").

**Hypothesis**: INT4 quantization will cause significant degradation in concept adherence and increased concept bleeding compared to INT8 and FP16, specifically in low-rank effect subspaces. INT8 will show negligible degradation.

**Null Hypothesis ($H_0$)**: There is no statistically significant difference in concept adherence (Cosine Similarity) or pixel fidelity (LPIPS) between FP16, INT8, and INT4 quantized models.

**Alternative Hypothesis ($H_1$)**: Quantization level has a significant effect on concept adherence, with INT4 showing the largest drop, and this drop is negatively correlated with the rank of the effect subspace.

## 2. Dataset Strategy

The study does not use external image datasets for *training* or *evaluation* of the base model. Instead, it generates its own evaluation dataset using a fixed set of 10 prompts and the `CollectionLoRA` adapter.

**Source of Truth**: The `CollectionLoRA` adapter weights and the base model (e.g., `stabilityai/stable-diffusion-2-1` or `runwayml/stable-diffusion-v1-5`) are the primary data sources. These must be downloaded from HuggingFace.

**Verified Datasets**:
*Note: The "Verified datasets" block provided in the context contains LLM evaluation benchmarks (ARC, etc.) and activation datasets, which are NOT relevant for Stable Diffusion image generation. The study relies on the **CollectionLoRA** adapter (a model artifact, not a dataset) and **Stable Diffusion** base models.*

- **Base Model**: `runwayml/stable-diffusion-v1-5` (or `stabilityai/stable-diffusion-2-1`).
  - *Source*: HuggingFace Hub.
  - *Relevance*: Standard base model for LoRA adaptation.
- **CollectionLoRA Adapter**: The specific adapter containing multiple effects (e.g., "oil painting", "watercolor", "neon").
  - *Source*: HuggingFace (User must provide the specific model ID, e.g., `user/collection-lora-multi-effect`).
  - *Relevance*: The subject of the quantization study.
- **Prompts**: A fixed list of 10 distinct text prompts covering the target effects.
  - *Source*: Defined in `code/config.yaml` (Synthetic data).
  - *Relevance*: Inputs for generation.

**Data Strategy**:
1.  **Download**: Fetch base model and CollectionLoRA adapter weights.
2.  **Generate**: Create multiple images per quantization level (FP16, INT8, INT4) using fixed seeds.
3.  **Embed**: Compute CLIP embeddings for prompts and generated images.
4.  **Compare**: Calculate metrics against the FP16 baseline.

*Note on Verified Datasets Block*: The provided list of parquet files (OpenBuddy, MNIST-activations, etc.) are for LLM text generation and activation analysis, not image generation. They are **not** used in this study. The study generates its own image data.

## 3. Methodology

### 3.1 Quantization Pipeline
- **Method**: Post-Training Quantization (PTQ) via `torch.ao.quantization` or manual rounding.
- **Process**:
  1. Load LoRA weights in FP16.
  2. Apply quantization observer and fake quantization for INT8.
  3. Convert to dynamic or static quantized model.
  4. Repeat for INT4 (using `torch.ao.quantization` with appropriate observers or fallback to **Manual Weight Rounding** if native backend fails).
  5. **Constraint**: No gradient updates. No re-distillation.
- **Fallback**: If `torch.ao.quantization` fails or OOM occurs, log "Backend Unavailable" and skip that level (FR-008). For INT4, if native support is unavailable, apply **Manual Weight Rounding** (rounding FP16 weights to 4-bit integers) as a simulation of INT4 quantization noise, explicitly noting this is a proxy for INT4 when native support is unavailable.

### 3.2 Metric Computation
1.  **Concept Adherence (Cosine Similarity)**:
    - $S = \cos(E_{text}, E_{image})$
    - $E_{text}$: CLIP text embedding of the prompt.
    - $E_{image}$: CLIP image embedding of the generated image.
    - *Reference*: CLIP model (ViT-B/32).
2.  **Pixel Fidelity (LPIPS)**:
    - Distance between generated image (INT8/INT4) and FP16 baseline image.
    - *Reference*: `lpips` library (pre-trained AlexNet/VGG).
3.  **Concept Bleeding (CESR)**:
    - **Aggregation Method**: **Maximum Similarity** (Max) of cosine similarities between the generated image and *other* effect's FP16 reference images. This captures the worst-case bleeding event.
    - **Threshold**: Only similarities > 0.1 are counted as bleeding to mitigate noise sensitivity.
    - **Semantic Control**: The baseline CESR (FP16) is computed for each prompt. The **Bleeding Magnitude** is defined as **Delta CESR = CESR_Quantized - CESR_FP16**. This isolates noise-induced bleeding from baseline semantic proximity (conflating semantic bleed with quantization bleed).

### 3.3 Statistical Analysis
- **Model**: Bayesian Hierarchical Model (BHM).
- **Rationale**: N=10 prompts (treated as 10 random effect groups) is insufficient for frequentist ANOVA power. BHM allows partial pooling and provides posterior distributions for effect sizes.
- **Hierarchical Structure**: **Images nested within prompts**.
  - *Total Observations*: 30 (10 prompts × 3 levels).
  - *Random Effect Groups*: 10 (Prompts).
  - *Fixed Effects*: Quantization Level (FP16, INT8, INT4).
- **Variables**:
  - *Outcome (Adherence)*: Cosine Similarity (or Delta from baseline).
  - *Outcome (Bleeding)*: **Delta CESR** (Bleeding Magnitude) per effect.
  - *Predictors*: Quantization Level (Categorical), Subspace Rank (Continuous).
  - *Priors*: Weakly informative (e.g., Normal(0, 1)).
- **Correlation Analysis (Per Effect)**:
  - **Unit of Analysis**: **Per Effect** (N=10 effects). This is distinct from the prompt-level analysis.
  - **Predictor**: Subspace Rank (constant per effect).
  - **Outcome**: Mean Bleeding Magnitude (Delta CESR) per effect.
  - **Caveat**: With N=10 effects, the correlation is **exploratory** and highly sensitive to outliers.
  - **Low Variance Check**: If the variance of Subspace Rank across effects is < 0.1, the correlation analysis is skipped and flagged as "Predictor Insufficient Variance".
  - **Posterior Width Analysis**: If the 95% CI width for $\rho$ > 0.2, the result is flagged as "Underpowered".
- **Outputs**:
  - Posterior probability that INT4 < INT8 < FP16.
  - Correlation coefficient ($\rho$) between Rank and Bleeding with 95% CI.
  - Posterior width analysis (FR-014).

## 4. Compute Feasibility & Risk Mitigation

**Constraints**: 2 CPU, 7GB RAM, 6h limit.

| Risk | Mitigation Strategy |
| :--- | :--- |
| **OOM (Out of Memory)** | Load base model in `torch.float16` and immediately offload to CPU using `diffusers` `enable_model_cpu_offload()` with **`offload_buffers=True`** and **`device_map='auto'`** to ensure specific layer swapping. If OOM occurs, catch `MemoryError` and log "Quantization Failure" (FR-008). |
| **Runtime > 6h** | Limit to 10 prompts. Use `torch.no_grad()`. Avoid high-resolution generation (use 512x512). Use `num_inference_steps=20` (reduced from 50). |
| **Quantization Backend** | Use `torch.ao.quantization` (CPU native). If native backend fails for INT4, apply **Manual Weight Rounding** (simulation). If INT8/INT4 fails, proceed with available levels and flag missing levels. |
| **CLIP/LPIPS Overhead** | Batch processing of embeddings. Pre-load CLIP model once. |
| **Power Analysis Contingency** | If OOM errors reduce the effective sample size below **N=20** (valid observations), the study aborts the specific quantization level. If the final dataset has **< 10 effects** with valid data, the correlation hypothesis is dropped and only adherence metrics are reported. |

## 5. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Bayesian vs. ANOVA** | N=10 (10 groups) is insufficient for ANOVA power; BHM provides probabilistic bounds required by FR-006. |
| **Zero-Shot PTQ** | Required to isolate quantization noise (Principle VI) without confounding drift from fine-tuning. |
| **CLIP as Proxy** | CLIP is the standard metric for text-to-image alignment; validated in literature. |
| **LPIPS as Fidelity** | LPIPS correlates better with human perception than MSE/PSNR. |
| **CPU-Only Execution** | Mandatory for reproducibility on GitHub Actions Free Tier. |
| **CESR Aggregation (Max)** | Max Similarity captures worst-case bleeding; mean would dilute specific events. Threshold >0.1 mitigates noise. |
| **Delta CESR** | Subtracting baseline CESR isolates noise-induced bleeding from semantic proximity. |
| **Correlation (Exploratory)** | N=10 effects is underpowered for correlation; treated as exploratory with Low Variance Check. |