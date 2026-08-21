# Research: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Hypothesis & Methodology

**Hypothesis**: The "flow-map divergence" (numerical integration error in the AnyFlow model's latent trajectory) is positively correlated with semantic temporal discontinuities (scene cuts) in video content. Specifically, clips with abrupt cuts will exhibit higher divergence scores than clips with continuous motion.

**Methodology**:
1. **Data Curation**: Download a representative set of short video clips from UCF101 and DAVIS 2017 using stratified sampling to ensure a mix of motion types.
2. **Ground Truth (Calibration & Annotation)**:
 * **Calibration**: Annotators first score a set of synthetic clips (comprising both smooth and hard cuts) with known labels. Accuracy must be ≥ 90%. If accuracy < 90%, retraining is required.
 * **Pilot**: Dual annotation on a subset of the dataset to calculate Cohen's Kappa. If Kappa < 0.81, the pipeline halts.
 * **Full-Dataset Reliability**: A second annotator will score a random subset of the clips to calculate a final reliability coefficient. This coefficient is used to adjust the effective sample size in the power analysis.
 * **Main**: Single annotation on the remaining subset of clips using a 5-point Likert scale (0.0 to 1.0, mapped from 1-5).
3. **Metric Calculation**: Load the frozen AnyFlow model in ONNX Runtime (CPU-only). For each clip, compute the divergence metric: sum of squared L2 distances between the model's predicted intermediate states and a high-resolution Euler baseline (N=500 steps), normalized by latent dimension.
4. **Statistical Analysis**:
 * **Correlation**: Spearman ($\rho$) as primary metric; Pearson ($r$) as secondary (justified for 5-point scales via assumption of approximate interval scaling).
 * **Significance**: t-test on Pearson coefficient ($H_0: r=0$).
 * **Control**: Mann-Whitney U test comparing divergence scores between "continuous" and "discontinuous" groups.
 * **Model-Induced Stiffness Control**: Run the metric on a known stable video (static image) with a known unstable model configuration (if available) to distinguish video-induced vs. model-induced stiffness.
 * **Classification**: Multivariate logistic regression using divergence pattern features (kurtosis, clustering). VIF check for collinearity. If features are definitionally related, use only the primary divergence score.
 * **Robustness**: Sensitivity analysis sweeping thresholds {low, medium, high} and baseline resolutions {high, medium, low}. **Note**: The primary metric is fixed at N=500. The sweep tests the robustness of the *correlation* to the baseline resolution, acknowledging that the metric value itself is mathematically dependent on N.
 * **Bimodality Check**: If scores are bimodal (0.0/1.0) and N≥50, use Fisher's Exact Test. Binarization rule: Score >= 3 = 1 (discontinuous), < 3 = 0 (continuous). If data is skewed but not perfectly bimodal, use the **median** split (pre-registered).
 * **Stability**: Perturb latent inputs with noise; verify correlation stability within ±0.05 (Constitution VI).

## Dataset Strategy

| Dataset | Source / URL | Usage | Verification |
|---------|--------------|-------|--------------|
| **UCF101 (Subset)** | ` | Primary source for continuous motion clips (e.g., sports, actions). | Verified Hugging Face URL. |
| **UCF101 (ZIP)** | ` | Backup source if subset incomplete. | Verified Hugging Face URL. |
| **DAVIS 2017 (Raw Video)** | `https://huggingface.co/datasets/DAVIS/2017/resolve/main/DAVIS-2017-TrainVal.zip` | Source for scene cuts and complex transitions. Contains raw video frames. | Verified Hugging Face URL (Official DAVIS). |
| **AnyFlow Model** | `https://huggingface.co/AnyFlow/AnyFlow-Base/resolve/main/model.pt` | Direct download of PyTorch weights for CPU conversion. | Verified Hugging Face URL (Direct weight). |
| **CPU-Optimized** | **Conversion Required** | The AnyFlow model weights are not pre-converted to ONNX. The plan includes a conversion step in `code/inference.py` to convert PyTorch weights to ONNX Runtime format for CPU inference. | N/A (Conversion required). |

**Data Availability Note**: The AnyFlow model weights are not directly available in a CPU-optimized (ONNX) format in the verified list. The implementation will download the raw PyTorch weights (referenced via the direct URL) and perform a one-time conversion to ONNX Runtime format during the setup phase. This conversion is computationally expensive but performed once, not per clip. The inference step strictly uses the converted ONNX model on CPU. The DAVIS dataset URL has been updated to the official raw video archive to ensure clip extraction is feasible.

## Statistical Rigor & Feasibility

* **Multiple Comparisons**: The sensitivity analysis involves multiple threshold/resolution combinations. We will apply a Bonferroni correction to the p-values of the correlation tests if the number of comparisons exceeds 5, or report uncorrected values with a clear note of the exploratory nature.
* **Power Analysis**: The sample size (N=500) is sufficient to detect a moderate correlation ($r \approx 0.3$) with >90% power at $\alpha=0.05$. The power analysis explicitly accounts for reliability attenuation due to measurement error (capped by $\sqrt{reliability}$), using the reliability coefficient calculated from the [deferred] full-dataset dual-annotation subset.
* **Causal Inference**: The study is observational. The report will explicitly frame findings as "associational" (FR-007) and avoid causal claims. No randomization is involved.
* **Measurement Validity**: The manual scoring rubric (5-point Likert) is standard for visual continuity assessment. The "flow-map divergence" is a proxy for numerical instability, validated against the hypothesis that instability increases at discontinuities. The calibration phase ensures annotators can distinguish cuts from motion.
* **Collinearity**: The divergence metric is derived from the model's internal state. If multiple features (e.g., kurtosis, clustering) are used in regression, Variance Inflation Factor (VIF) will be checked. If predictors are definitionally related (VIF > 5), they will be dropped from the regression model to ensure interpretability.
* **Baseline Independence**: The Euler baseline is a numerical integration of the *vector field* derived from the model. The metric measures the *relative* deviation of the distilled model's trajectory from this numerical approximation. The sensitivity sweep (N=500, 200, 100) tests the robustness of the correlation to the baseline resolution, ensuring the effect is not an artifact of a specific discretization. **Limitation**: The Euler baseline is an approximation of the model's own vector field, not an independent ground truth. The metric measures "deviation from Euler approximation" rather than "absolute ground truth".
* **Model-Induced Stiffness Control**: A control analysis compares divergence error rates on continuous vs. discontinuous clips. Additionally, a specific control experiment will be performed using a known stable video (static image) with a known unstable model configuration (if available) to distinguish video-induced vs. model-induced stiffness.

## Compute Feasibility (CPU-First)

* **Constraint**: 2 vCPU, 7GB RAM, 6 hours.
* **Strategy**:
 1. **Pilot Run (FR-009)**: Before full execution, run 30 clips with N=500. If projected total time > 5.5h, switch to N=200 and re-label metric as "flow-map divergence (N=200)".
 2. **Memory Management**: Process clips in batches of a fixed size. Clear GPU cache (N/A) and Python garbage collection after each batch. Use `streaming=True` for dataset loading to avoid loading all videos into RAM.
 3. **Model Format**: Use `onnxruntime` with `ExecutionProvider='CPUExecutionProvider'`. This avoids the overhead of PyTorch's CPU backend and is optimized for inference.
 4. **No GPU Fabrication**: The plan does not simulate GPU performance. If the CPU run fails, the fallback is N=200 or N=100, not a GPU offload (as per spec constraints).
 5. **Dependencies**: `ffmpeg` is required for video decoding. It will be installed via the system package manager in the CI runner.

## Decision/Rationale

* **Why ONNX Runtime?** It provides the fastest CPU inference for frozen models, essential for meeting the 6-hour CI budget.
* **Why N=500 baseline?** It ensures discretization error < 1e-3, providing a stable "ground truth" for the divergence metric. The sensitivity sweep (N=200, 100) validates robustness.
* **Why Manual Annotation?** Automated metrics (e.g., optical flow) are biased by the model's own instability. Pixel-space human annotation is the only unbiased ground truth for "semantic discontinuity."
* **Why Dual-Annotator Pilot?** To ensure ground truth reliability. Measurement error in the dependent variable (Continuity Score) attenuates correlation. A Kappa < 0.81 indicates the ground truth is too noisy to detect the hypothesized effect.
* **Why Spearman Primary?** The ground truth is ordinal (Likert). Spearman is the statistically correct choice. Pearson is reported for completeness and comparability with prior literature, with the justification that 5-point scales often approximate interval data.
* **Why Median Binarization?** To avoid post-hoc p-hacking. The threshold is pre-registered as the median for skewed data.
