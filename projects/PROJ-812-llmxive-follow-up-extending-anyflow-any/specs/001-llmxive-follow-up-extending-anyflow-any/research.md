# Research: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Problem Statement

The "AnyFlow" model proposes an on-policy flow map distillation for video generation. A key hypothesis is that distilled models may exhibit numerical instability (divergence) in their latent trajectories, particularly when encountering semantic discontinuities (scene cuts). This project aims to validate this hypothesis by correlating a computed "flow-map divergence" metric against a manually annotated ground-truth of temporal continuity.

**Critical Hypothesis**: The correlation between "divergence" and "cuts" is *not* simply a function of "motion magnitude". The study will test this by controlling for motion complexity.

## Dataset Strategy

The study relies on public video repositories containing both continuous motion and abrupt scene cuts. Per the verified dataset list, specific URLs for "AnyFlow" or "CPU-optimized" models are not available. The plan assumes the model weights are available locally or via a standard conversion pipeline to ONNX format as per the spec's assumptions.

### Verified Datasets

| Dataset Source | Content Description | Usage in Plan | Verified URL |
|:--- |:--- |:--- |:--- |
| **UCF101** | Action recognition dataset (human motion). | Source for "continuous motion" clips. | https://huggingface.co/datasets/ucf101/ucf101 (or Kaggle mirror) |
| **Kinetics-400** | Large-scale video dataset with diverse actions and cuts. | Source for mixed continuity and cuts. | |
| **DAVIS** | Dataset of annotated video sequences (object tracking). | Source for high-quality continuous motion. | https://huggingface.co/datasets/davis |
| **AnyFlow Model** | Frozen diffusion weights for latent extraction. | Core inference engine (CPU-optimized). | **NO verified source found** -> **BLOCKED** until verified source found. |
| **ONNX Config** | Configuration for ONNX models. | Reference for CPU runtime settings. | https://huggingface.co/datasets/bakks/flan-t5-onnx/resolve/main/flan-t5-base/config.json |

**Dataset Fit & Limitations**:
- **Variable Fit**: The spec requires "temporal continuity scores" (0.0-1.0) derived from pixel inspection. The public datasets (UCF, Kinetics, DAVIS) provide the raw video content but **do not** provide the specific "temporal continuity score" required. This score must be generated via the manual annotation process defined in FR-002.
- **Missing Data Handling**: If a video clip cannot be downloaded or is corrupted, the system logs the error and skips the clip (Edge Case 2), ensuring the batch job continues.
- **Stratified Sampling**: To satisfy FR-001, the curation script will implement a *Pixel-Difference Heuristic* (frame-to-frame MSE > threshold) to ensure at least 20% of the 500 clips contain abrupt scene cuts. This is an *independent* heuristic, not a manual selection, to avoid circularity.

### Heuristic Orthogonality Check
Before full annotation, a pilot set of 10 clips will be analyzed to ensure the "Pixel-Difference Heuristic" (used for stratification) does not correlate with the model's specific latent failure modes. If the heuristic predicts "cuts" where the model shows *low* divergence (or vice versa) in a pattern that suggests bias, the threshold will be adjusted.

## Methodology

### Phase 1: Data Curation & Baseline Validation (FR-001, FR-002, FR-009)
1. **Download**: Fetch short temporal clips (e.g., 30fps) from UCF101, Kinetics, DAVIS.
2. **Stratification**: Apply a *Pixel-Difference Heuristic* (frame-to-frame MSE > threshold) to identify "cuts". Ensure [deferred] of clips are labeled "cut".
3. **Baseline Validation**: Run a pilot on 10 clips comparing N=500 Euler vs. N=2000 Euler/RK4. If the L2 difference between N=500 and the higher-order baseline exceeds 5% of the mean divergence, the system will reduce N to 200 or halt.
4. **Annotation**: Generate `continuity_scores.csv` with human-annotated scores (0.0-1.0).
 - *Constraint*: No model features used for scoring.
 - *Validation*: Variance must be ≥ 0.05 (FR-010).

### Phase 2: CPU-Tractable Inference (FR-003, FR-004)
1. **Model Loading**: Load AnyFlow weights converted to ONNX format for CPU inference (ONNX Runtime).
 - *Constraint*: No CUDA, no quantization requiring GPU.
2. **Confounding Variable Measurement**: Compute "Motion Complexity" (optical flow magnitude) and "Texture Density" (gradient variance) for each clip.
3. **Divergence Metric**: Compute L2 distance between the model's predicted intermediate state and the Euler baseline.
 - *Metric*: $Divergence = \frac{1}{T} \sum_{t=1}^{T} || \text{Model}(x_t) - \text{Euler}(x_t) ||_2$.
4. **Preflight Check**: Run on first 5 clips to estimate runtime (FR-009). If > 5.5h projected, reduce $N$ to 200 (if validated) or halt.

### Phase 3: Correlation & Sensitivity (FR-005, FR-006, FR-007)
1. **Variance Check**: Calculate variance of `continuity_scores`. If < 0.05, halt and report "Insufficient Variance".
2. **Correlation**: Compute Pearson $r$ and Spearman $\rho$ between `continuity_scores` and `divergence_scores`.
3. **Partial Correlation**: Compute partial correlation controlling for "Motion Complexity" and "Texture Density".
4. **Sensitivity**: Analyze classification rates at low thresholds.
5. **Framing**: Explicitly state "Relationship: Associational" (FR-007).
6. **Output**: Generate `correlation_results.csv`, `sensitivity_report.csv`, and `variance_report.csv`.

### Phase 4: Report Generation (FR-008, SC-004, SC-005)
1. **Report Generation**: Execute `code/report_generator.py`.
 - *Logic*: Read `correlation_results.csv`, `sensitivity_report.csv`, `variance_report.csv`.
 - *Mandatory Injection*: Insert FR-008 statement: "The 'flow-map divergence' metric is a proxy for model instability..."
 - *Mandatory Injection*: Insert SC-005 statement: "CPU-only mode (ONNX Runtime, no CUDA)".
 - *Mandatory Injection*: Insert FR-007 statement: "Relationship: Associational".
2. **Final Output**: Generate `final_report.md`.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Only two primary correlation tests (Pearson, Spearman) are run. A Bonferroni correction is noted but likely not strictly necessary for the primary hypothesis test; however, the sensitivity analysis involves 3 thresholds, so the interpretation of "significant" changes must be cautious.
- **Sample Size/Power**: The target is a substantial corpus of clips. Power analysis for a binary "cut vs. continuous" comparison (Mann-Whitney U) with medium effect size (d=0.5) and alpha=0.05 confirms N=500 is sufficient. If the distribution is bimodal, a non-parametric test (Mann-Whitney U) will be used.
- **Causal Inference**: The study is **observational**. The plan explicitly avoids causal claims (FR-007). The relationship is framed as "model instability correlates with semantic discontinuity," not "instability causes discontinuity."
- **Measurement Validity**: The manual annotation relies on human visual inspection. To mitigate bias, the annotation rubric (not included in code) must be strict: 0.0 = perfect continuity, 1.0 = hard cut.
- **Collinearity**: The divergence metric is derived from the model's latent state, which is also used to generate the video. However, the ground truth is pixel-based. There is no definitional collinearity between the *score* (human) and the *metric* (model error), so independent effects are not claimed; rather, a correlation is tested.
- **Construct Validity**: The plan explicitly tests if the correlation is driven by "motion magnitude" by including it as a covariate. If the correlation disappears when controlling for motion, the hypothesis is rejected.

## Compute Feasibility

- **Environment**: GitHub Actions `ubuntu-latest` (2 CPU, 7GB RAM).
- **Memory**: ONNX Runtime is optimized for CPU. Short-duration clips are small. A sufficient number of clips will fit in memory if processed sequentially or in small batches.
- **Runtime**: The Euler baseline ($N=500$) is computationally expensive. The preflight check (FR-009) is critical. If $N=500$ exceeds the 6-hour budget, the plan allows reducing $N$ to 200, though this may reduce the precision of the "Numerical Baseline."
- **No GPU**: All operations are CPU-bound. `torch` and `onnxruntime` will be installed in CPU-only modes.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **ONNX Runtime for Inference** | Required for CPU-only execution (FR-003). PyTorch CPU inference is slower and less optimized for static graphs. |
| **N=500 Euler Steps** | Spec requirement (FR-004) for "high-resolution" baseline. *Fallback*: N=200 if validated. |
| **Manual Annotation** | Required by FR-002 to ensure ground truth is independent of model features. |
| **Associational Framing** | Required by FR-007 due to observational nature of the study. |
| **Stratified Sampling** | Required by FR-001 to ensure [deferred] of clips are cuts, preventing class imbalance. |
| **Pixel-Difference Heuristic** | Required to avoid manual selection bias and ensure orthogonality to model failure modes. |
| **Partial Correlation** | Required to isolate the "cut" effect from general motion complexity. |