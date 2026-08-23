# Research: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Summary
This research investigates the hypothesis that numerical instability in distilled flow-matching models (measured as "flow-map divergence") correlates with semantic temporal discontinuities (scene cuts) in video data. The study relies on a CPU-tractable pipeline to compute divergence metrics on real video clips and correlates them with human-annotated continuity scores.

## Dataset Strategy

### Verified Datasets
The following datasets are used, sourced strictly from the verified list provided:

| Dataset | Source URL | Usage in Plan |
| :--- | :--- | :--- |
| **UCF101** | `https://huggingface.co/datasets/ucf101` (via `datasets.load_dataset('ucf101')`) | Source for continuous motion clips. Sampled proportionally to natural distribution. |
| **Kinetics-400** | `https://huggingface.co/datasets/kinetics-400` (via `datasets.load_dataset('kinetics-400')`) | Source for scene cut/discontinuous clips. Contains natural scene edits. |
| **AnyFlow Model** | `https://huggingface.co/simbahuang/AnyFlow@v1.0.0` (stable repo, version pinned) | Reference for model checkpoint weights. Weights are downloaded by SHA256 hash to ensure version stability. |

*Note: DAVIS 2017 is primarily an object tracking dataset and does not natively contain 'scene cuts'. Kinetics-400 is used for cuts.*

### Data Acquisition & Processing
1.  **Download**: `code/data/download.py` fetches the UCF101 and Kinetics-400 datasets using canonical Hugging Face loaders.
2.  **Extraction**: Clips are extracted as sequences of frames at a standard frame rate.
3.  **Sampling**: A **simple random sample** is drawn **proportional to the natural distribution** of the source datasets (likely skewed towards continuous motion). This avoids the bias of artificial stratification.
4.  **Annotation**: A human annotator reviews clips using a Likert scale (converted to 0.0–1.0). **Blinding Protocol**: Annotators receive clips with randomized IDs and **NO metadata** regarding the source dataset or the pre-computed 'cut' label. This process is manual and pixel-space only (FR-002).
5.  **Disagreement Resolution**: If Cohen's Kappa < 0.81, the system halts. If Kappa >= 0.81 but individual clips disagree (diff > 1 point), ambiguous clips are discarded. The system **oversamples** initially (N=600) to ensure a final valid N >= 500 after discards.

## Methodological Rigor

### Statistical Approach
1.  **Correlation Analysis**:
    *   **Pearson ($r$)**: Tests linear relationship between divergence and continuity.
    *   **Spearman ($\rho$)**: Tests monotonic relationship (robust to non-linearity).
    *   **Bimodality Check**: If scores are bimodal (0.0/1.0) and $N \ge 50$, an **Independent Samples t-test (Welch's)** is used to compare mean divergence of group 0 vs group 1. **Fisher's Exact Test** is used **only** as a protocol-mandated exception per Spec FR-005/US-1 for binary classification of the outcome variable, acknowledging the statistical limitation of using it with a continuous predictor.
    *   **Variance Check**: Variance must be $\ge 0.05$ (FR-010).
2.  **Multivariate Analysis**: **Logistic Regression** to predict discontinuity type (cut vs. continuous) using divergence features (kurtosis, clustering). **Inverse Probability Weighting (IPW)** is applied to correct for the natural class imbalance (skewed distribution) when estimating population-level accuracy.
3.  **Sensitivity Analysis**: Thresholds $\{0.01, 0.05, 0.1\}$ and Euler steps $\{500, 200, 100\}$ are swept to assess robustness (FR-006).

### Statistical Rigor & Assumptions
*   **Multiple Comparisons**: Since multiple correlation tests (Pearson, Spearman) and threshold sweeps are performed, a Bonferroni correction or False Discovery Rate (FDR) control will be applied to p-values where appropriate, though the primary focus is on the magnitude of the correlation coefficient.
*   **Sample Size/Power**: The sample size of 500 is estimated to provide sufficient power (>0.8) to detect a moderate correlation ($r \approx 0.12$) at $\alpha=0.05$. If the observed correlation is <0.12, the result will be reported as 'underpowered to detect weak effects' rather than a false negative.
*   **Causal Inference**: The study is **observational**. No randomization of video content occurs. Claims are strictly framed as **associational** (FR-007). We test if numerical error *correlates* with semantic discontinuity, not if it *causes* it.
*   **Measurement Validity**: The manual annotation relies on a 5-point Likert rubric. Inter-annotator agreement (Cohen's Kappa $\ge 0.81$) is verified on a subset before full deployment (FR-010). Ambiguous clips (disagreement > 1 point) are discarded.
*   **Collinearity**: Divergence features (kurtosis, clustering) may be correlated. Variance Inflation Factor (VIF) will be checked; if high, only the primary divergence metric will be used in the logistic model.

### Compute Feasibility (CPU-First)
*   **Model Format**: AnyFlow weights will be converted to ONNX format for CPU inference using `onnxruntime`.
*   **Euler Solver**: The baseline Euler rollout uses $N=500$ steps. If the pre-flight check (FR-009) indicates runtime > 5.5 hours, $N$ will be reduced to 200.
*   **Memory**: Streaming video frames and processing one clip at a time ensures RAM usage stays < 7GB.
*   **GPU Escape Hatch**: None required. The entire pipeline is designed for CPU execution. If the ONNX model fails to load on CPU (e.g., requires specific CUDA kernels), the project will halt with a "Feasibility Error" rather than fabricating a CPU approximation.
*   **Real Data Only**: All divergence scores are computed via real ONNX inference on real video frames. No synthetic or simulated metrics are used.

## Decision/Rationale
*   **CPU-Only**: Chosen to strictly adhere to the GitHub Actions free-tier constraints (FR-002, US-2).
*   **ONNX Runtime**: Selected as the standard for CPU-optimized inference of PyTorch models.
*   **Manual Annotation**: Required to avoid circular logic (using model outputs to validate the model).
*   **Euler Baseline**: Chosen as a deterministic, high-resolution numerical ground truth to measure "solver error" (FR-004). The baseline defines numerical error; the *correlation* with manual scores distinguishes semantic error.
*   **Blinding Protocol**: Required to prevent confirmation bias during annotation.
*   **Power Analysis**: Required to justify N=500 and interpret null results correctly.
*   **t-test for Bimodal Data**: Required because Fisher's Exact Test is inappropriate for continuous predictors, but the spec mandates it for binary outcomes.
*   **Natural Distribution**: Chosen to reflect real-world video streams. IPW is used to correct for bias in logistic regression.