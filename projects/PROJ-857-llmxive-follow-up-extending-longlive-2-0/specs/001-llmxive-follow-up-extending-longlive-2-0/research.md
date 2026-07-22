# Research: llmXive follow-up: extending "LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation"

## Research Question

What is the specific bit-width threshold (e.g., 2-bit vs 4-bit vs 8-bit) at which **local temporal coherence** (a proxy for narrative consistency in short clips) degrades non-linearly when simulated via stochastic rounding on a CPU-only infrastructure?

*Note: The study reframes "narrative consistency" as "frame-to-frame semantic stability" for 4-second clips, as Kinetics-400 does not contain long-form narrative data. This reframing addresses the construct validity gap identified in the spec.*

## Methodology & Statistical Rigor

### Experimental Design
The study employs a **factorial design** with two factors:
1.  **Bit-width**: 2-bit, 4-bit, 8-bit (Simulated).
2.  **Random Seed**: Multiple independent seeds per bit-width to estimate variance.

**Total Runs**: 9 experimental runs.

### Statistical Analysis Plan
1.  **Primary Outcome**: Narrative Consistency Score (derived from CLIP-ViT).
2.  **Threshold Detection**: A **Slope Comparison Analysis** will be performed.
    *   *Method*: Calculate the degradation rate (slope) between 2-bit and 4-bit, and between 4-bit and 8-bit.
    *   *Rationale*: With only 3 distinct X-values (2, 4, 8), non-linear models (piecewise, logistic) are underdetermined. Slope comparison identifies a non-linear break by testing if the degradation rate significantly changes between intervals.
    *   *Threshold Definition*: The "threshold" is the bit-width where the degradation rate significantly increases (e.g., slope(2->4) < slope(4->8)).
3.  **Significance Testing**:
    *   **Effect Size (Cohen's d)**: The primary metric for degradation.
    *   **Confidence Intervals**: 95% CI for the mean consistency scores.
    *   **Pairwise T-tests**: Comparing 4-bit vs 8-bit and 2-bit vs 4-bit to quantify degradation.
    *   **Multiple Comparison Correction**: **Bonferroni correction** will be applied to the alpha level (e.g., $\alpha_{adj} = 0.05 / 2 = 0.025$) to control family-wise error rate.
    *   **Power Limitation**: With only 3 seeds per condition, the study has low power to detect small effect sizes. The analysis will explicitly report **Effect Size (Cohen's d)** and **95% Confidence Intervals** as the primary evidence of degradation, rather than relying solely on p-values. Claims of "non-linear degradation" will rely on the magnitude of the drop and the slope difference, with a clear acknowledgment of the Type II error risk.
4.  **Collinearity**: Bit-width is a discrete, independent variable. No collinearity issues exist between predictors.
5.  **Measurement Validity**: The CLIP-ViT metric is validated against **synthetic ground truth** (injected discontinuities) per FR-007. If the model fails to detect injected discontinuities (score drop < 15%), the metric is flagged as invalid.

### Compute Feasibility Strategy
*   **CPU-First**: The entire training loop uses `torch` on CPU. Stochastic rounding is implemented via Python/NumPy masking and noise injection on 32-bit tensors.
*   **Evaluation Model**: The CLIP-ViT model is replaced with a **CPU-optimized, distilled variant** (e.g., `clip-vit-tiny` or `ViT-Tiny`) to ensure inference completes within the 6-hour limit on CPU. **GPU offload is explicitly rejected** to maintain strict reproducibility on a single runner.
*   **Memory Management**: The Kinetics-400 subset is streamed or loaded in small batches to stay within 7GB RAM. The theoretical memory formula `(Params × Bits / 8) + 1.2GB` is used for reporting, not runtime profiling, to avoid profiling overhead.

### Simulation Fidelity Limitation
*   **Scope**: This simulation models **numerical stability and noise characteristics** (stochastic rounding) as a proxy for NVFP4.
*   **Limitation**: Stochastic rounding on 32-bit floats does **not** replicate the specific non-linear quantization curves, saturation behaviors, or hardware-specific error distributions of actual NVFP4 hardware.
*   **Impact**: The "precision threshold" identified is valid for the *numerical behavior* of the algorithm under stochastic rounding, but may not perfectly predict the behavior of the actual NVFP4 infrastructure. The study explicitly frames its findings as "Numerical Stability Thresholds" rather than "Hardware Performance Thresholds".

### Reference Mechanism for FR-009
*   **Theoretical Uniform Distribution**: Generated using `numpy.random.uniform(low=0, high=1, size=N)` where N is the number of quantization steps.
*   **KL-Divergence Calculation**: The simulated noise distribution (from stochastic rounding) is binned and compared against the theoretical uniform distribution using the Kullback-Leibler divergence formula: $D_{KL}(P || Q) = \sum P(i) \log(P(i)/Q(i))$.
*   **Validation**: The run is valid if $D_{KL} < 0.05$.

## Dataset Strategy

### Primary Dataset: Kinetics-400
*   **Source**: HuggingFace Datasets (`kinetics-400` or `kinetics-700` filtered).
*   **Verification**: The dataset contains video clips with action labels. It is verified to be downloadable via the `datasets` library.
*   **Usage**: A **downsampled subset** of 4-second clips will be extracted.
*   **Constraint Handling**: The full dataset is too large. The plan explicitly defines a **sampling strategy** (e.g., first 500 clips per action class) to ensure the total size fits within the 7GB RAM limit.
*   **Feasibility**: The dataset is open and directly downloadable. No credentials required.
*   **Construct Validity**: Kinetics-400 is an action recognition dataset, not a narrative consistency dataset. The study reframes the research question to "local temporal coherence" (frame-to-frame stability) as a proxy for narrative consistency in short clips.

### Evaluator Model: CLIP-ViT (CPU-Optimized)
*   **Source**: HuggingFace Transformers (`openai/clip-vit-tiny` or similar distilled model).
*   **Usage**: Frozen weights. Used to compute cosine similarity between frame embeddings to assess temporal coherence.
*   **Feasibility**: The model is small. Inference on short-duration clips is computationally light on CPU, ensuring the temporal limit is met without GPU offload.

### Verified datasets
- Kinetics-400: `datasets.load_dataset("kinetics-400", split="train", streaming=True)` (Verified via HuggingFace Hub).
- CLIP-ViT (Tiny): `transformers.AutoModel.from_pretrained("openai/clip-vit-tiny-patch16-224")` (Verified via HuggingFace Hub).

## Decision/Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-Only Simulation** | Matches the "Compute Feasibility" constraint. Stochastic rounding on 32-bit floats is a valid proxy for bit-width noise without needing hardware. |
| **CPU-Optimized Evaluator** | Ensures the entire pipeline runs within 6 hours on CPU, maintaining reproducibility on a single runner. GPU offload is rejected. |
| **Slope Comparison Analysis** | Required to identify a "threshold" (non-linear break) with only 3 data points. Piecewise linear regression is underdetermined. |
| **Downsampled Subset** | Mandatory to fit within 7GB RAM. The sampling is random and documented to avoid bias. |
| **Synthetic Ground Truth** | Required for FR-007 validation as human-labeled data is unavailable. Injected discontinuities provide a valid proxy for metric sensitivity. |
| **Bonferroni Correction** | Mandatory to control family-wise error rate when running multiple t-tests across bit-widths. |

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Model Collapse (2-bit)** | 2-bit simulation may cause model to output constant noise, making consistency score undefined (NaN). | Handle NaN/Inf gracefully; record "Collapse" status; exclude from regression but report as a data point. |
| **Low Statistical Power** | 3 seeds may not yield significant p-values. | Report confidence intervals and Effect Size (Cohen's d); focus on curve shape; acknowledge limitation in paper. |
| **Dataset Access Failure** | Kinetics-400 download fails due to rate limiting. | Use `streaming=True`; implement retry logic; fallback to a smaller, verified subset (e.g., `kinetics-600` sample). |
| **Simulation Fidelity Gap** | Stochastic rounding does not match NVFP4 hardware exactly. | Explicitly frame findings as "Numerical Stability Thresholds" and add a "Simulation Fidelity Limitation" section in the paper. |
| **GPU Offload Rejection** | Reliance on external GPU breaks reproducibility. | Mandate CPU-optimized CLIP-ViT; no GPU offload. |
