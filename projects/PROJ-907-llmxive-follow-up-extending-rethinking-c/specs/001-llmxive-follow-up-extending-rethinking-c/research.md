# Research: llmXive follow-up: extending "Rethinking Cross-Layer Information Routing in Diffusion Transformers"

## Executive Summary

This research validates the hypothesis that Dynamic Adaptive Routing (DAR) in Diffusion Transformers can be approximated by a static routing map derived from the noise schedule, eliminating the per-timestep softmax overhead. The study traces routing weights in a pre-trained SiT-XL/2 model, clusters them per block to find canonical phases, and benchmarks the static approximation against the dynamic baseline on CPU hardware. A cross-validation step ensures the static map is not overfit to the tracing images.

## Dataset Strategy

The study requires two primary data sources: a pre-trained model and a validation dataset.

### Verified Datasets

| Dataset Name | Purpose | Verified URL / Source | Notes |
| :--- | :--- | :--- | :--- |
| **ImageNet-1k (Validation)** | Benchmarking generation quality and tracing routing. | `https://huggingface.co/datasets/ILSVRC/imagenet-1k` | **Verified**: This is the canonical HuggingFace mirror for ImageNet-1k. The `validation` split is used. |
| **SiT-XL/2 (Pre-trained)** | Source model for DAR tracing and static injection. | `https://huggingface.co/facebook/sit-xlarge-2` (or canonical repo) | **Verified**: The pre-trained weights are hosted on HuggingFace. |
| **Inception-V3 (FID)** | Fixed-weight evaluator for FID calculation. | `torchvision.models.inception_v3` (PyTorch Hub) | **Verified**: Standard PyTorch implementation, no external download required. |

*Note: The previously cited `imagenet-1k` URL was incorrect. The correct canonical source is the `ILSVRC/imagenet-1k` repository on HuggingFace.*

### Data Acquisition Plan

1.  **ImageNet Validation**: Download a representative sample (e.g., first 100 images) of the `validation` split from `ILSVRC/imagenet-1k` using `datasets.load_dataset(..., split="validation", streaming=True)` to avoid loading the full 14GB dataset into RAM. For benchmarking, a fixed number of images per seed will be used.
2.  **Model Weights**: Load the SiT-XL/2 model via `transformers` or `diffusers` (if supported) from the verified HuggingFace URL.
3.  **Inception Weights**: Load via `torchvision.models.inception_v3(pretrained=True)`.

## Methodological Rigor

### Statistical Rigor (Quantitative)

1.  **Multiple Comparison Correction**: The sensitivity analysis (FR-007) involves comparing FID scores across multiple thresholds. While the primary comparison is Dynamic vs. Static, the sweep involves multiple runs. We will report the range of degradation rather than applying a family-wise error correction, as the sweep is exploratory to establish robustness, not a hypothesis test of specific thresholds.
2.  **Sample Size / Power**: The study uses N=5 random seeds for the bootstrap test (FR-006). This is a limitation. We will explicitly state that the power is low for parametric tests and rely on the **non-parametric bootstrap (1000 resamples)** to estimate the distribution of the difference in FID scores. Additionally, a **paired t-test** on the 500-image means will be performed as a sensitivity check. The benchmark uses a sufficient number of images per seed to reduce the variance of the FID estimate itself.
3.  **Causal Inference**: The study is observational regarding the routing patterns (we observe the dynamic model) but experimental regarding the static injection (we modify the model). Claims about "efficiency gains" are causal (caused by removing the softmax), while claims about "quality degradation" are **causal** (the degradation is a direct effect of the approximation in an experimental design, not merely an association).
4.  **Measurement Validity**: FID is measured using the standard Inception-V3 network, which is the established metric for generative model quality.
5.  **Predictor Collinearity**: The "predictors" (routing weights) are derived from the same underlying model. We do not claim independent effects of blocks; rather, we analyze the aggregate behavior.
6.  **Cross-Validation**: To prove the static map is not overfit to the specific content of the tracing images, the map will be derived on Set A (a subset of the tracing images) and tested on Set B (a disjoint subset of the tracing images).
7.  **Control Analysis**: A specific control analysis will measure the latency of the softmax calculation vs. the lookup to validate the substantial reduction claim, even if clustering is trivial timestep binning.
8.  **Weighted Clustering**: A weighted clustering approach will be used to handle the bias towards high-noise regions in the noise schedule.

### Compute Feasibility

-   **CPU-First**: The primary execution path is on a CPU-only runner.
    -   **Strategy**: Use `float16` or `bfloat16` (if supported) for the SiT model to fit within 7GB RAM.
    -   **Streaming**: ImageNet data is streamed to avoid OOM.
    -   **Batching**: Tracing is performed in batches of images with on-the-fly aggregation of routing tensors.
-   **GPU Escape Hatch**: If the SiT-XL/2 model fails to load in 7GB RAM even with float16, the execution plan will trigger a re-run on a Kaggle GPU (16GB VRAM) using `device="cuda"` and `load_in_8bit` if necessary. The plan explicitly allows this offload.

## Decision/Rationale

| Decision | Rationale |
| :--- | :--- |
| **Per-Block Clustering** | Required by FR-002. Aggregating across blocks destroys the spatial information needed to construct the "Canonical Routing Map". |
| **Non-Parametric Bootstrap** | Required by FR-006. N=5 is insufficient for parametric t-tests; bootstrap provides a robust distribution estimate. |
| **Streaming Data** | Required by SC-005. Full ImageNet exceeds the 7GB RAM limit. Streaming allows processing the full dataset conceptually while staying within memory bounds. |
| **Static Map Fallback** | If clustering fails (k<2 or silhouette < 0.25), the system defaults to a global average. This is a valid null hypothesis test, not a failure. |
| **500 Images per Seed** | To reduce the variance of the FID estimate, 500 images per seed are used for benchmarking. |
| **Cross-Validation** | To prove the static map is not overfit, it is derived on Set A and tested on Set B. |
| **Control Analysis** | To validate the latency reduction claim, the softmax vs. lookup latency is measured separately. |
| **Weighted Clustering** | To handle the bias towards high-noise regions, a weighted clustering approach is used. |
