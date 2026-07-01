# Research: Reproduce & Validate Domino Speculative Decoding Framework

## 1. Objective

To reproduce the **algorithmic principle** of the Domino speculative decoding framework (arXiv:2605.29707) in a CPU-only environment. 

**Critical Validity Note**: The paper's specific claim of "5.49x speedup" was measured on Qwen3 (likely >7B) with GPU acceleration. Validating this exact magnitude on a 0.5B model (Qwen2-0.5B) on CPU is scientifically invalid due to hardware and model-size non-linearities. 
**Reframed Goal**: Validate that Domino provides a speedup over standard autoregressive decoding *within the same CPU environment*. The 5.49x value is treated as a "Reference Claim" for context only.

## 2. Dataset Strategy

The benchmark relies on a set of prompts to measure latency and throughput. Since the paper does not specify a unique dataset for the benchmark and the vendored code likely uses a standard HuggingFace dataset (e.g., `c4`, `wikitext`, or a custom prompt list), we will use a small, curated subset of prompts to ensure runtime feasibility.

| Dataset Name | Source/URL | Usage | Notes |
| :--- | :--- | :--- | :--- |
| **Prompts (Subset)** | *Local/Generated* | Benchmark Input | A list of diverse text completion prompts. No external URL is required; prompts are generated or hardcoded to ensure reproducibility and minimize I/O. |
| **CPU-supported Models** | NO verified source found | Model Loading | The target model (Qwen) is not available as a verified source in the provided list. We will use `Qwen/Qwen2-0.5B` or `HuggingFaceTB/SmolLM2-360M` as a proxy. |

> **Note**: The "Verified datasets" block indicated NO verified source for CPU-supported models. Therefore, we rely on the HuggingFace Hub for model loading but must explicitly select a model known to fit in 7GB RAM.

## 3. Model Selection & Feasibility Analysis

### Target Model: Qwen3 (Paper Claim)
- **Status**: **Unavailable / Infeasible**.
- **Reasoning**: The paper mentions Qwen3, but no verified source exists for it in the provided list. Furthermore, Qwen3 (likely a large model) would exceed the 7GB RAM limit on a CPU-only runner, especially with FP32/FP16 precision.
- **Strategy**: Substitute with a smaller, open-weights model that supports CPU inference and fits within RAM constraints.
- **Selected Proxy**: `Qwen/Qwen2-0.5B` (0.5 Billion parameters).
  - **RAM Estimate**: ~1GB for weights (FP32) + ~2GB for KV cache and activation buffers = ~3-4GB peak. Safe for 7GB limit.
  - **Rationale**: It is a compatible architecture (Qwen family) and allows for a fair comparison of the *algorithm* (speculative decoding) even if the absolute speedup differs from the paper's large-model claims.

### Precision Strategy
- **Constraint**: No `bitsandbytes` or CUDA-specific quantization.
- **Plan**: Use standard `torch.float32` (FP32) or `torch.float16` (if supported on CPU by the specific PyTorch version).
- **Fallback**: If FP16 fails on CPU, revert to FP32. The plan must explicitly log the precision used.

## 4. Benchmarking Methodology

### Execution Flow
1.  **Environment Setup**: Install `requirements-hf.txt` with `pip install --no-deps` for CPU-only torch if necessary, or use a pre-built CPU wheel.
2.  **Hardware Detection**: The script must detect `device = "cpu"` and set `device_map = "cpu"`.
3.  **Model Loading**: Load the proxy model (Qwen2-0.5B) and the draft model (if Domino requires a separate draft model, use a smaller variant or the same model with a different configuration).
4.  **Dry Run**: Execute 1 prompt to estimate latency. Adjust prompt count if total estimated time > 35 mins.
5.  **Benchmark Loop**: Run multiple independent iterations.
    -   Each iteration: Load model, run a batch of prompts.
    -   Record `total_latency`, `tokens_per_second`, and `per_prompt_speedup` for each prompt.
6.  **Memory Tracking**: Use `psutil` to track peak RSS during the run.
7.  **Environment Capture**: Log `torch` and `transformers` versions.
8.  **Aggregation**: Calculate mean, std, min, max, and 95% CI for speedup ratios.
9.  **Comparison**: Compare `mean_speedup` against `reference_claim_speedup` (5.49) and report deviation.
10. **Reporting**: Generate a JSON artifact and a human-readable report.

### Statistical Rigor
-   **Multiple Comparisons**: Not applicable for a single aggregate metric, but variance is reported.
-   **Sample Size**: 5 runs × 10 prompts = 50 data points. Justified as maximum feasible within 45 mins while allowing CI calculation.
-   **Causal Inference**: Direct performance comparison (Domino vs. Baseline) on same hardware.
-   **Measurement Validity**: Metrics are standard. Proxy model validity acknowledged.

### Risk Mitigation

| Risk | Mitigation Strategy |
| :--- | :--- |
| **OOM (Out of Memory)** | Use 0.5B model. If OOM, reduce prompts to 5. |
| **Timeout (>45 min)** | Dynamic prompt sizing based on Dry Run. Hard kill at m. |
| **CUDA Errors** | `CUDA_VISIBLE_DEVICES=""`. No `bitsandbytes`. |
| **Model Unavailable** | Fallback to `HuggingFaceTB/SmolLM2-135M`. |

## 5. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use Qwen2-0.5B instead of Qwen3** | Qwen3 is unavailable and likely too large for CPU/7GB RAM. Qwen2-0.5B is a valid proxy for testing the algorithm. |
| **Enforce CPU-only execution** | Required by CI constraints (no GPU). |
| **Use 5 runs × 10 prompts** | Balances statistical significance (variance analysis) with the 45-minute runtime limit. |
| **No 8-bit quantization** | `bitsandbytes` requires CUDA; CPU-only runners cannot use it. |
| **5.49x as Reference Only** | Scientific validity requires acknowledging that GPU/large-model claims cannot be directly reproduced on CPU/small-model. |