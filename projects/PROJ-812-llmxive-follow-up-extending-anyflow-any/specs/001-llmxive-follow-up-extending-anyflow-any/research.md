# Research: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## 1. Problem Statement & Hypothesis

**Problem**: Validating whether "flow-map divergence" (L2 distance between predicted and Euler-rolled latent states) serves as a reliable proxy for temporal instability in video diffusion models, specifically distinguishing continuous motion from abrupt scene cuts.

**Hypothesis**: Clips with high **external physical discontinuity** (measured by optical flow variance) will exhibit significantly higher **internal flow-map divergence** scores. The correlation between these two measures is the primary validation target.

**Theoretical Justification**: Distilled models approximate the flow map of a teacher model. While they are efficient, they may be less robust to high-frequency discontinuities (scene cuts) than the teacher. We hypothesize that the "distillation error" (divergence from the stable Euler trajectory) is amplified when the input contains a scene cut, creating a measurable correlation between internal error and external discontinuity.

**Assumption Check**: The spec assumes the AnyFlow model weights are available in a CPU-optimized format. The research plan proceeds under this assumption but flags the lack of a verified public URL for the model itself (see Dataset Strategy).

## 2. Dataset Strategy

### Verified Datasets
The following datasets are used for video clips. Note: **AnyFlow** and **CPU-optimized** models have **NO verified source found**. The implementation will require the user to provide the model weights locally or via a trusted internal channel; no URL is cited for the model.

| Dataset Name | Description | Source/Loader | Status |
| :--- | :--- | :--- | :--- |
| **UCF101** | Human action recognition dataset. Contains continuous motion. | `ucimlrepo` (with manual download fallback script) | Verified |
| **Kinetics-400** | Large-scale video dataset. Mix of actions and cuts. | `datasets.load_dataset("kinetics-400")` | Verified |
| **DAVIS** | Dense video annotation dataset. Good for object continuity. | Manual download (licensing) via script | Verified |

*Note: The plan uses `ucimlrepo` for UCF101 as the standard HF `datasets` loader often lacks raw video files. DAVIS requires manual download due to licensing restrictions. If a specific subset (e.g., "16-frame clips") is not directly available, the curation script will sample and crop from the raw source.*

### Dataset Variable Fit
- **Required**: Video frames (16 frames), labels (manual score), external flow variance.
- **Available**: Raw video files from UCF101/Kinetics/DAVIS.
- **Gap**: The datasets do *not* contain "temporal continuity scores" or "optical flow variance". These must be generated via the manual annotation process (FR-002) and the optical flow computation script (FR-004 proxy).
- **Fit**: The datasets provide the raw material (video) required to generate the variables. No fatal mismatch found, provided the manual annotation and optical flow steps are executed.

## 3. Methodology

### 3.1 Data Curation (FR-001, FR-002)
1.  **Sampling**: Randomly select a representative set of clips (16 frames each) from UCF101, Kinetics, and DAVIS. Ensure a mix of action types (continuous) and editing styles (cuts).
2.  **Annotation**: A human annotator reviews each clip and assigns a score $S \in [0.0, 1.0]$.
    - 0.0: Perfect continuity.
    - 1.0: Maximum discontinuity (e.g., hard cut).
    - **Reliability Protocol**: **A subset of clips is double-annotated.** Krippendorff's Alpha is calculated. If Alpha < 0.6, the phase halts and the rubric is revised.
3.  **Binarization**: For sensitivity analysis, scores are binarized:
    - $S < 0.4 \rightarrow$ 'Continuous' (0)
    - $S > 0.6 \rightarrow$ 'Discontinuous' (1)
    - $0.4 \le S \le 0.6 \rightarrow$ 'Ambiguous' (Excluded from binary metrics)
4.  **Storage**: Save as `data/raw/annotations.csv` with columns: `video_id`, `source`, `score`, `annotator_id`.

### 3.2 Metric Calculation (FR-003, FR-004)
1.  **Model Integrity & Architecture Verification**: Load the frozen AnyFlow model converted to ONNX format. Use `onnxruntime.InferenceSession` with `providers=['CPUExecutionProvider']`.
    - **Integrity Check**: Compute SHA-256 hash of the model file. Log 'Unverified Source' if no known-good hash exists.
    - **Architecture Verification**: Verify the model's layer count and input/output shapes match the "On-Policy Flow Map Distil" architecture defined in the paper. If mismatch, halt with error.
    - **Quantization Test**: Run a subset of clips with float16 and float32. Verify $\Delta r < 0.05$. **If failed, halt.**
2.  **Latent Extraction**: For each frame in a clip, extract the latent representation $z_t$.
3.  **Internal Divergence**:
    - Compute predicted state $\hat{z}_{t+1}$ from $z_t$.
    - Compute ground-truth rollout $z_{t+1}^{Euler}$ using N=1000 steps (high-resolution).
    - Calculate $D_{internal} = \frac{1}{T} \sum_{t=1}^{T} || \hat{z}_{t+1} - z_{t+1}^{Euler} ||_2$.
    - *Note*: This is an internal numerical measure (distillation error), not the ground truth for discontinuity.
4.  **External Proxy (Optical Flow)**:
    - Compute optical flow fields using `raft-small` (CPU-optimized).
    - Calculate **Optical Flow Variance** ($V_{flow}$) across the 16 frames. High variance indicates scene cuts/discontinuity.
    - *Rationale*: This provides the physical ground truth proxy for the hypothesis.
5.  **Error Handling**: If a clip fails (corrupted), log error, skip, and flag in report (Edge Case).

### 3.3 Statistical Analysis (FR-005, FR-006, FR-007)
1.  **Distribution Analysis**: Calculate variance, mean, and histogram of manual scores (SC-004). **Explicitly report variance.**
2.  **Power Analysis**: Calculate minimum detectable effect size (Cohen's d) for N=500, power=0.8, alpha=0.05. Report that the study is powered to detect correlations > 0.15.
3.  **Correlation**:
    - Calculate Pearson $r$ and Spearman $\rho$ between **$D_{internal}$** and **$V_{flow}$**.
    - Compute p-values.
    - **Framing**: Explicitly state results are **associational** (observational study), not causal.
4.  **Sensitivity Analysis**:
    - Sweep threshold $T \in \{0.01, 0.05, 0.1\}$ on $D_{internal}$.
    - Calculate False Positive Rate (FPR) and False Negative Rate (FNR) using the **Binarized** labels from 3.1.
    - *Note*: If scores are bimodal, interpret as binary classification performance.
5.  **Report Generation**: Generate final JSON report including **Runtime Environment** (SC-005) and **Provenance Declaration** (Constitution II). **Explicitly state "CPU-only (ONNX Runtime, no CUDA)" in the report.**

### 3.4 Statistical Rigor & Limitations
- **Multiple Comparisons**: Only two primary tests (Pearson, Spearman) are run. No family-wise error correction is strictly required for just two tests, but the p-values are reported transparently.
- **Power**: The sample size (N=500) is fixed by the spec. The plan acknowledges this as a limitation if the effect size is small, but it is the maximum feasible within the 6-hour CI budget.
- **Collinearity**: The manual score and the divergence metric are distinct constructs (human perception vs. model error). No definitional collinearity exists.
- **Measurement Validity**: The "temporal continuity score" relies on human rubric. The plan assumes the rubric is consistent.
- **Model Provenance**: The study is conditional on the user-provided model matching the paper's architecture. The 'Unverified Source' flag is carried to the final report.

## 4. Compute Feasibility

- **Hardware**: GitHub Actions Free (CPU, limited RAM).
- **Model**: ONNX Runtime (CPU) + `raft-small` (CPU).
- **Data**: 500 clips x 16 frames.
- **Time Budget**: ≤6 hours.
- **Strategy**:
    - Process clips in batches of moderate size to manage memory.
    - Use `torch.no_grad()` to reduce overhead.
    - Pre-compute Euler rollouts if caching is allowed (otherwise compute per clip).
    - If runtime exceeds a predefined threshold, reduce sample size to a fallback level.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **AnyFlow model unavailable or mismatched** | Fatal (cannot compute metric) | Plan requires user to provide weights. Architecture verification step halts if structure is wrong. |
| **Memory Overflow** | High (CI job killed) | Process in small batches; clear CPU memory after each clip. |
| **Annotation Bias** | Medium (Ground truth skewed) | Double-annotate %; Krippendorff's Alpha < 0.6 triggers halt. |
| **Runtime > 6h** | High (CI failure) | Optimize ONNX session; reduce N=1000 to N=500 if necessary (documented). |
| **Circular Metric** | High (Invalid hypothesis) | Use external optical flow variance as ground truth proxy; reframe hypothesis. |
| **Unverified Model Source** | Medium (Constitution II failure) | Log 'Unverified Source' flag; final report must explicitly state this limitation. |
| **Quantization Instability** | High (Invalid metric) | Mandatory Quantization Sensitivity Test. Halts if $\Delta r > 0.05$. |

## 6. Decision Rationale

- **Why ONNX?** Native PyTorch CPU inference is slower. ONNX Runtime is optimized for CPU and fits the 6-hour budget better.
- **Why Manual Annotation?** Automated metrics (e.g., optical flow) cannot capture "semantic" discontinuity (e.g., a cut between two similar-looking objects) as well as a human. The spec requires human ground truth.
- **Why Pearson AND Spearman?** The relationship between model error and human perception may be non-linear. Spearman captures monotonic trends; Pearson captures linear strength.
- **Why Optical Flow Proxy?** The model's own Euler rollout is an internal numerical baseline, not a physical ground truth. Using external optical flow variance breaks the circularity and validates the hypothesis against physical reality.