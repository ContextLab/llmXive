# Research: EfficientRollout: System-Aware Self-Speculative Decoding for RL Rollouts

## 1. Paper Analysis & Reproduction Strategy

### 1.1 Core Concept
The paper "EfficientRollout" proposes **System-Aware Self-Speculative Decoding (SD)**. Unlike traditional speculative decoding which uses a small, independent model, this method induces a "drafter" from the target model itself (self-speculation) and uses a **toggle mechanism** to decide when to speculate based on system constraints (batch size, memory pressure).

**Key Hypothesis**: On GPU (A100), speculation yields up to 19.6% latency reduction. On CPU, the overhead of verification might negate benefits unless the toggle logic correctly disables speculation in memory-bound regimes.

### 1.2 Validation Scope
This reproduction focuses on **mechanism validation** and **algorithmic efficacy** rather than exact metric replication:
-   **Validated**: The ability to generate a quantized drafter on CPU, the logic of the toggle (including synthetic forcing), and the relative latency comparison (Speedup > 0 or < 0).
-   **Validated (Algorithmic Efficacy)**: Using a small, full-precision model (TinyLlama) to demonstrate that SD *can* be faster on CPU when the model is small enough, proving the algorithm works.
-   **Deferred**: Exact percentage of latency reduction (expected to differ on CPU), full dataset scale, statistical significance.

## 2. Dataset Strategy

### 2.1 Target Dataset: SimpleRL-Zoo (Local SSoT)
The spec identifies `SimpleRL-Zoo` as the target dataset for prompts.

| Dataset Name | Required Format | Verified Source URL | Status |
| :--- | :--- | :--- | :--- |
| SimpleRL-Zoo | JSONL / Parquet | **NO verified source found** | **Critical Gap** |

**Analysis**: The "Verified datasets" block provided in the prompt does **not** contain a URL for `SimpleRL-Zoo`.
-   **Action**: The implementation plan **MUST NOT** fabricate a URL.
-   **Fallback Strategy**:
    1.  **Primary**: Use a local file `prompts.jsonl` as the **Single Source of Truth (SSoT)**.
    2.  **Fail-Fast**: If `prompts.jsonl` is missing, the system MUST exit with an error. No silent fallback.
    3.  **Content**: 10 generic instruction-following prompts.

*Decision*: The plan assumes a **local prompt file** approach for the 10-prompt subset to ensure the CI job is self-contained and does not rely on an unverified external URL.

### 2.2 Data Subset
-   **Size**: 10 prompts (as per US-2).
-   **Trials**: 3 repetitions per prompt (Total N=30 data points) to estimate variance and establish consistency.
-   **Rationale**: Ensures runtime < 15 minutes on CPU and fits within 7GB RAM.
-   **Content**: Generic instruction-following prompts (e.g., "Write a poem about...", "Explain quantum physics...").

## 3. Technical Feasibility & Constraints

### 3.1 Compute Environment
-   **Hardware**: 2 vCPU, 7GB RAM, 14GB Disk.
-   **Constraint**: **NO GPU**.
-   **Implication**:
    -   `bitsandbytes` (8-bit quantization) is **incompatible** (requires CUDA).
    -   **Solution**: Use `torch.ao.quantization` (dynamic quantization) as the primary method. This avoids the need for a calibration dataset and reduces peak RAM during the quantization process.
    -   **Fallback**: `optimum` with `gguf` if `torch.ao` fails to meet memory constraints.
    -   **Risk**: Quantization on CPU is slower than FP32 inference for small batches. The "toggle" logic is critical here to disable speculation if the overhead is too high.

### 3.2 Memory Management
-   **Model Size**: Llama-3.1-8B (FP16 ~16GB, INT4 ~5GB, INT8 ~8GB).
-   **Constraint**: 7GB RAM.
-   **Strategy**:
    -   Load the target model in **INT8** (via `torch.ao.quantization.quantize_dynamic`) to fit in RAM.
    -   **Dynamic Capping**: The `sd_toggle` module must monitor `psutil` for CPU RAM and reduce batch size to 1 if usage > 6GB.
    -   **Streaming**: Use `device_map="auto"` or chunked loading to prevent OOM during initialization.

## 4. Statistical & Methodological Rigor

### 4.1 Latency Measurement
-   **Metric**: End-to-end time (seconds) for generating `N` tokens.
-   **Baseline (8B)**: Standard Autoregressive (AR) decoding using the **same quantized model**.
-   **Baseline (TinyLlama)**: Standard Autoregressive (AR) decoding using **full-precision** model.
-   **Speculative**: Self-Speculative Decoding (Draft -> Verify) using the **same model** (quantized or full-precision).
-   **Comparison**: `Speedup = (Time_Baseline - Time_SD) / Time_Baseline`.
-   **Statistical Note**: With N=30, statistical significance is low. The result is **descriptive** (directionality of speedup) rather than inferential.
-   **Variance**: Calculate Coefficient of Variation (CV) across the 30 data points to quantify system jitter.

### 4.2 Confounding Factors & Controls
-   **Confound**: CPU cache thrashing and quantization overhead may dominate the latency signal on the 8B model.
-   **Control 1 (8B)**: The Baseline uses the **same quantized model** running in AR mode. This isolates the *algorithmic* overhead of SD (draft + verify) from the *quantization* overhead.
-   **Control 2 (TinyLlama)**: The Baseline uses a **full-precision** small model. This provides a scientifically valid baseline where SD is expected to be faster, validating the *algorithmic efficacy* of the method.
-   **Synthetic Regime**: To validate the toggle logic (which might always "Disable" on the 8B model), a synthetic test will artificially inflate the "draft cost" (e.g., by repeating the draft step) to force the toggle to "Enable", proving the logic works.

### 4.3 Assumptions & Limitations
-   **Assumption**: The "System-Aware" toggle logic works on CPU metrics (RAM usage) as a proxy for GPU memory pressure.
-   **Limitation**: CPU cache behavior differs significantly from GPU; speedup may be negative on the 8B model. This is an expected outcome for CPU validation, not a failure.
-   **Power**: The study is underpowered for statistical claims; it validates the *implementation* of the algorithm, not the *efficacy* at scale.
-   **Ground Truth**: 
    *   For the 8B model, the "Baseline" is the quantized AR model. The validation is of the *relative* efficiency of SD on a quantized kernel.
    *   For the TinyLlama model, the "Baseline" is the full-precision AR model. The validation is of the *algorithmic* speedup of SD.

## 5. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use Local Prompts** | No verified URL for `SimpleRL-Zoo`. Local file ensures reproducibility without external dependency. |
| **Use `torch.ao.quantization` (Dynamic)** | `bitsandbytes` requires CUDA. `torch.ao` dynamic quantization is CPU-native, requires no calibration, and fits within 7GB RAM. |
| **Dual-Model Strategy** | A single 8B quantized comparison is tautological for speedup claims; a small full-precision model is needed to validate the algorithm's efficacy. |
| **3 Trials per Prompt (N=30)** | N=1 is insufficient to distinguish signal from jitter. 30 data points provide minimal variance estimate. |
| **Synthetic Regime Test** | Validates toggle logic mechanism even if natural CPU regime always disables speculation. |
| **Fail-Fast on Missing Data** | Ensures Data Integrity (SSoT) and prevents silent fallback to unverified sources. |
| **Accept Negative Speedup (8B)** | CPU overhead for speculation often exceeds benefits. Validating the *logic* (toggle) is the goal, not matching the [deferred] paper claim. |
| **Positive Speedup (TinyLlama)** | Validates that the algorithm *can* work on CPU under favorable conditions, proving the "system-aware" claim is not inherently flawed. |