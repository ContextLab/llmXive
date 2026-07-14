# Research: llmXive follow-up: extending "ViQ: Text-Aligned Visual Quantized Representations at Any Resolution"

## 1. Problem Statement & Hypothesis

**Hypothesis**: A visual quantization codebook trained exclusively on low-resolution (64x64) images can successfully encode high-resolution (1024x1024) inputs without architectural modification, preserving semantic alignment (text-image similarity) while suffering predictable degradation in pixel-wise fidelity (PSNR/SSIM) correlated with texture complexity.

**Core Question**: Does the "resolution-invariant" property of ViQ hold when the training manifold (64x64) is disjoint from the evaluation manifold (1024x1024) in terms of frequency content?

## 2. Dataset Strategy

We utilize the verified datasets provided in the project specification.

| Dataset Role | Source Name | Verified URL | Usage |
|:--- |:--- |:--- |:--- |
| **Training (Low-Res)** | COCO (Image-Caption Pairs) | ` | 64x64 resizing; Training VQ codebook and projection head. |
| **Evaluation (High-Res)** | ImageNet-1K | ` | 1024x1024 inference; Fidelity & Texture metrics. |
| **Evaluation (High-Res)** | COCO (Subset) | ` | 1024x1024 inference; Fidelity & Semantic metrics (requires captions). |

**Dataset Fit Verification**:
- **COCO**: Contains image-text pairs. *Fit*: Perfect for training and semantic validation.
- **ImageNet**: Contains high-res images. *Fit*: Perfect for evaluating resolution shift. *Constraint*: We will use a subset (N=100) to fit within 7GB RAM.
- **ChestX-ray14**: *Removed*. No verified source exists in the block. The dataset is not natively available in `torchvision` and requires external download scripts not guaranteed to work in CI. The "medical texture" hypothesis is deferred.
- **Metric Reference**: Removed non-existent "predict-SIREN-PSNR" dataset. Validation will use internal held-out COCO subsets with known ground truth.

**Metric Validation**:
- Internal validation using a held-out subset of the COCO training set (known ground truth) to verify PSNR/SSIM calculation logic. No external "benchmark" dataset is used.

## 3. Methodology

### Phase 1: Low-Resolution Training (64x64)
1. **Data Loading**: Load COCO pairs. Resize images to 64x64 using bilinear interpolation.
2. **Model Initialization**:
 - **Encoder**: Pre-trained ViQ encoder (frozen weights).
 - **Codebook**: Randomly initialized VQ codebook (e.g., 256 tokens, dim 256).
 - **Projection Head**: Linear layer mapping encoder output to CLIP text embedding dim.
3. **Loss Function**:
 - $L_{vq} = ||z_e - e||^2 + ||sg[z_e] - e||^2$ (VQ-VAE commitment loss).
 - $L_{align} = 1 - \cos(\text{Proj}(z_e), \text{CLIP}_{text}(text))$.
 - $L_{total} = L_{vq} + \lambda L_{align}$.
4. **Optimization**: AdamW on CPU. Batch size tuned to fit available system memory (likely 4-8).
5. **Stopping**: Early stop if validation loss plateaus or max epochs reached.

### Phase 2: High-Resolution Inference (1024x1024)
1. **Data Loading**: Load ImageNet and a subset of COCO images at native 1024x1024.
2. **Forward Pass**:
 - Pass 1024x1024 image through frozen ViQ encoder.
 - Quantize using the *trained* 64x64 codebook.
 - Decode to generate 1024x1024 reconstruction.
 - *Termination Condition*: If the decoder architecture is not resolution-invariant and fails to output 1024x1024 (e.g., shape mismatch), the experiment terminates, and the result is reported as "Architecture Limitation".
3. **Metrics**:
 - **Fidelity**: PSNR, SSIM between **native** 1024x1024 image and reconstruction. (Note: This corrects the spec's FR-004 which suggested upsampled ground truth).
 - **Semantic**: Cosine similarity between projected visual embedding and CLIP text embedding (only for COCO subset where captions exist). **ImageNet is excluded from semantic metrics** due to lack of ground-truth captions; generic prompts are rejected as invalid for Construct Validity.
 - **Texture Complexity**: Calculate Laplacian variance of the original 1024x1024 image.

### Phase 3: Statistical Analysis
1. **Control Condition**: To isolate resolution shift from information density, we compute a "Low-Res Baseline" for semantic similarity by **resizing the same high-res images to 64x64**, running them through the pipeline, and comparing the resulting scores. This ensures the comparison is between resolutions of the *same* content.
2. **Correlation**: Spearman rank correlation between Texture Complexity and Reconstruction Error (PSNR) on **N=200** images (100 ImageNet + 100 COCO). *Power Note*: N=200 provides moderate power for strong correlations; effect sizes and confidence intervals will be reported alongside p-values.
3. **Significance**: **Paired t-test** (or Wilcoxon signed-rank test) comparing High-Res similarity scores against the Low-Res baseline scores for the same images. (Note: This corrects the spec's SC-005 which suggested a one-sample test).
4. **Threshold Check**: Flag if semantic similarity drop > 5%.

## 4. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (multi-core CPU, adequate RAM).
- **GPU**: None. No CUDA.
- **Memory Management**:
 - Training: Batch size restricted to ensure < 6GB peak RAM.
 - Inference: Process images **one-by-one** (batch size 1) with explicit `gc.collect()` calls.
 - **Fallback Strategy**: If memory usage exceeds 6GB during inference, the script will automatically reduce the sample size by [deferred] and log a warning. Target N=200 is the goal, but N=100 is the safe fallback.
- **Time Limit**: 6 hours.
 - Training on 64x64 is computationally light.
 - Inference on 1024x1024 is the bottleneck. We will limit the dataset to a representative subset of images from ImageNet and COCO to ensure completion.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **ViQ Encoder not Resolution Invariant** | Fatal: Shape mismatch on 1024x1024 input. | Check architecture (global pooling). If fixed-size, experiment terminates; report as "Architecture limitation". |
| **Memory Overflow** | Crash on 1024x1024 batch. | Strict batch size = 1; explicit garbage collection; automatic sample size reduction. |
| **CLIP Text Encoder Mismatch** | Semantic metric failure. | Verify embedding dimension (standard vs. extended) and match Projection Head. |
| **Low Statistical Power** | Inconclusive correlation. | Increase N to 200; report effect sizes and confidence intervals; use qualitative inspection if p > 0.05. |

## 6. Decision Log

- **Decision**: Use `datasets` library for COCO/ImageNet loading.
 - *Rationale*: Standardized, handles parquet/arrow formats efficiently.
- **Decision**: Use `scikit-learn` for statistical tests.
 - *Rationale*: CPU-optimized, lightweight.
- **Decision**: Subsample ImageNet to a representative subset of images (balanced per dataset type).
 - *Rationale*: Full dataset exceeds RAM/Disk limits; N=200 balances power and feasibility.
- **Decision**: Use Laplacian variance for texture complexity.
 - *Rationale*: Computationally cheaper than full FFT on high-res images, sufficient proxy for high-frequency energy.
- **Decision**: Remove ChestX-ray14.
 - *Rationale*: No verified source; CI compatibility risk.
- **Decision**: Use Paired t-test.
 - *Rationale*: Corrects the statistical invalidity of a one-sample test against an empirical mean.
- **Decision**: Exclude ImageNet from semantic alignment metrics.
 - *Rationale*: Lack of ground-truth captions for ImageNet makes semantic similarity uninterpretable.
- **Decision**: Compare against native 1024x1024 ground truth.
 - *Rationale*: Avoids interpolation bias from upsampled low-res targets.
- **Decision**: Compute Low-Res Baseline by resizing same high-res images.
 - *Rationale*: Isolates resolution shift effect from information density.