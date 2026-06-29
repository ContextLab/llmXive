# Research: KVarN Variance-Normalized KV-Cache Quantization

## 1. Dataset Strategy

The study relies on four reasoning benchmarks. Per the verified dataset list, the following sources are used. **No other URLs are cited.**

| Dataset | Verified Source URL(s) | Loader Strategy | Notes |
|:--- |:--- |:--- |:--- |
| **MATH500** | ` | `datasets.load_dataset("di-zhang-fdu/MATH500", split="test")` | Primary math reasoning benchmark. |
| **AIME24** | ` | `datasets.load_dataset("hendrydong/aime24", split="test")` | Advanced math competition problems. |
| **HumanEval** | ` | `datasets.load_dataset("openai_humaneval", split="test", revision="v1.1")` | Code generation benchmark. **Cited canonical HF ID `openai_humaneval` with version pin `v1.1`.** |
| **IFEval** | ` | `datasets.load_dataset("google/IFEval", split="train")` (or test if available) | Instruction following benchmark. |

**Dataset Variable Fit Check**:
- **Required**: Prompts, Ground Truth Answers.
- **Available**: All listed datasets contain prompt and answer fields.
- **Gap**: No dataset provides per-token "reasoning traces" or "hidden states" from a reference model. The plan calculates reconstruction error *internally* by comparing the quantized vs. full-precision (simulated) KV caches during the forward pass. This is a valid proxy for error accumulation without needing external traces.

## 2. Algorithm Design: Variance-Normalized Quantization

### 2.1 Problem Definition
Standard uniform quantization (e.g., 8-bit linear) applies a fixed scale `S` and zero-point `Z` to a tensor $X$:
$$ Q(X) = \text{round}(X / S) + Z $$
This assumes the activation distribution is uniform or has a fixed variance. In LLMs, KV-cache activations often exhibit heavy tails or varying variance across layers and tokens, leading to high reconstruction error for outliers.

### 2.2 KVarN Method
The KVarN algorithm introduces a local variance normalization step before quantization:
1. **Windowing**: Define a sliding window $W$ over the sequence dimension (e.g., last 32 tokens).
2. **Variance Calculation**: Compute local variance $\sigma^2_w$ for each head/layer within $W$.
3. **Normalization**: $X'_{w} = (X_w - \mu_w) / \sqrt{\sigma^2_w + \epsilon}$, where $\epsilon = 10^{-8}$ (FR-008).
4. **Quantization**: Apply uniform 8-bit quantization to $X'$.
5. **Dequantization & Rescaling**: $X_{rec} = (Q(X') - Z) \cdot S \cdot \sqrt{\sigma^2_w + \epsilon} + \mu_w$.

**Handling Near-Zero Variance (FR-008)**:
If $\sigma^2_w < 10^{-8}$, the denominator is clamped to $10^{-8}$ to prevent division by zero. This effectively treats near-constant regions as having a minimal noise floor.

### 2.3 Baseline
Uniform 8-bit linear quantization (no variance normalization, fixed scale based on min/max of the entire tensor). **Crucially, the baseline runs on the same model weights (Phi-2 FP16) to isolate the KV quantization variable. No 4-bit weight quantization is used.**

## 3. Experimental Protocol

### 3.1 Inference Setup
- **Model**: **Phi-2 (2.7B)** loaded in **FP16** (full precision) to satisfy FR-002 and fit 7GB RAM. **No 4-bit weights used.**
- **Engine**: `transformers` with a custom `generate` loop to inject KVarN hooks. This is the **only** CPU-compatible path.
- **Constraints**: Max 512 tokens generation (FR-004). Batch size = 1 (to minimize RAM).
- **Seeding**: `torch.manual_seed(42)`, `numpy.random.seed(42)`.

### 3.2 Metrics Collection
For each instance $i$ in benchmark $B$:
1. **Reconstruction Error**: Compute **per-token MSE** between the **FP16 KV cache captured before quantization** and the **quantized KV cache**.
 $$ \text{MSE}_i^{(t)} = || \text{KV}_{fp16}^{(t)} - \text{KV}_{quant}^{(t)} ||^2 $$
 *Note: "Full-precision" here refers to the internal FP16 state of the model at step $t$ before the quantization hook modifies it. This is captured in the same forward pass, avoiding the need for a separate heavy model run.*
 **Relative Nature**: The hypothesis is about the **relative** error accumulation (difference in slopes) between KVarN and Uniform, not absolute error against an external ground truth. The metric is a relative measure of reconstruction fidelity against the *same* FP16 input tensor.
 **Per-Token Logging**: The system MUST log `mse_per_token` as a list of floats (one per generated token) to enable slope analysis.
2. **Task Accuracy**: Exact match between generated answer and ground truth.
3. **Memory Footprint**: Peak memory usage of KV cache.
4. **Cache Size**: Calculate `kv_cache_size_bytes` and `reduction_percent` relative to the FP16 baseline (FR-007). This is computed as: `reduction_percent = (1 - (quantized_cache_size / fp16_cache_size)) * 100`.

### 3.3 Statistical Analysis Plan (FR-006, FR-010)
1. **Binary Accuracy (SC-003)**:
 - Test: McNemar's test (paired, binary outcomes).
 - Null Hypothesis ($H_0$): No difference in accuracy between KVarN and Uniform.
 - Significance: $\alpha = 0.05$.
2. **Continuous MSE (SC-001, SC-005)**:
 - Test: Paired t-test (if normality holds) or Wilcoxon signed-rank test.
 - Check: Shapiro-Wilk test for normality of MSE differences.
3. **Error Accumulation Slope (SC-005, FR-010)**:
 - **Data**: Use the **`mse_per_token` list** (one value per generated token) from each instance to fit a linear regression: $\text{MSE}_{cumulative} = \beta_0 + \beta_1 \cdot \text{TokenPos}$.
 - **Comparison**: Compare slopes $\beta_{1, \text{KVarN}}$ vs $\beta_{1, \text{Uniform}}$ using ANCOVA or interaction term significance.
4. **Correlation (SC-006, FR-009)**:
 - **Data**: Aggregate `cumulative_mse` and `exact_match` across all instances.
 - **Test**: Pearson correlation (or Point-Biserial) between cumulative MSE and binary accuracy.
 - **Caveat**: This correlation is observational and may be confounded by input difficulty. It is framed as a "proxy validation" rather than a causal proof. The analysis cannot distinguish between 'quantization error causes reasoning failure' and 'reasoning failure causes quantization error' (or both being driven by input difficulty).

## 4. Compute Feasibility & Risk Mitigation

### 4.1 Resource Constraints
- **RAM**: 7 GB. **Phi (2.7B) in FP16 requires ~5.4GB for weights.** With KV cache overhead (8-bit) and Python runtime, this is tight but feasible.
 - *No Fallback*: 4-bit weights are **not** used as a fallback to avoid confounds (FR-002). If OOM occurs, the sample size is reduced.
 - *Model Choice*: **Phi-2 (2.7B)** is the default to ensure FR-002 is not confounded by weight quantization.

### 4.2 Runtime
- **Time Limit**: 6 hours.
- **Strategy**: Run a subset of each benchmark (e.g., a small number of samples) if full run exceeds time.
 - *Power Justification*: A sample size of 50 per benchmark allows McNemar's test to detect moderate effect sizes (odds ratio > 2.0) with [deferred] power. For smaller effect sizes (e.g., 1.2), power is lower; the study will report observed effect sizes with confidence intervals and explicitly acknowledge this limitation rather than claiming definitive power.
 - *Timeout Handling*: If the 6-hour limit is reached, the system will stop processing new instances but immediately compute the slope comparison on the *accumulated* per-token trajectories so far, ensuring a valid (though potentially underpowered) result is produced. Partial results are saved to ensure statistical validity of the slope comparison even if underpowered.
