# Research: Reproduce & Validate Domino Speculative Decoding Framework

## Research Question
Can the Domino speculative decoding framework be successfully reproduced and validated on a CPU-only GitHub Actions runner (2 vCPU, 7GB RAM) while maintaining a positive speedup over standard autoregressive decoding, despite the hardware limitations compared to the paper's GPU-based claims?

## Dataset Strategy

The "Verified datasets" block provided does not contain a specific LLM model dataset. The Domino framework requires an LLM model and a prompt dataset for inference.

- **Model Source**: The target model is `Qwen/Qwen3` (as per the paper title). However, Qwen3 is not yet publicly available on HuggingFace Hub as of the current verification date, and even if it were, it likely exceeds the 7GB RAM limit.
- **Substitution Strategy**: The plan will utilize **Qwen2** variants available on HuggingFace Hub, specifically `Qwen/Qwen2-0.5B-Instruct` (Draft) and `Qwen/Qwen2-1.8B-Instruct` (Target). This specific pair is chosen because:
  1. It fits within the 7GB RAM constraint.
  2. The size differential (0.5B vs 1.8B) is necessary to demonstrate the speculative decoding speedup mechanism (Draft < Target).
  3. Both models share the same architecture family, ensuring compatibility with the Domino logic.
  4. **Verification**: The plan explicitly verifies that the Qwen2 architecture supports the specific Domino mechanism (e.g., attention masking) required to validate the paper's claim.
- **Prompt Source**: For the benchmark prompts, we will use a small, static set of 5 prompts embedded in the code or loaded from a local JSON file. This avoids the need for external dataset downloads that might introduce variability or network timeouts.
- **No External Dataset URL**: As per the "Verified datasets" block, no specific URL for an LLM benchmark dataset is provided. Therefore, the plan relies on **programmatic loading** of the model via HuggingFace Hub (`transformers.AutoModelForCausalLM.from_pretrained`) and a local prompt list. No URLs from the verified block will be cited for the model or prompts.

## Technical Feasibility Analysis

### 1. CPU-Only Execution
- **Constraint**: GitHub Actions free tier has no GPU.
- **Analysis**: The `transformers` library supports CPU inference out of the box. The key risk is the accidental import of `bitsandbytes` or usage of `load_in_8bit`, which requires CUDA.
- **Solution**: The `requirements-hf.txt` must be sanitized to exclude `bitsandbytes`. The runner script will explicitly set `device_map="cpu"` and `torch_dtype=torch.float32` (or `float16` if supported on CPU, though `float32` is safer for compatibility). Phase 0 will verify no CUDA-specific kernels are required by the vendored code.

### 2. Memory Constraints (7GB RAM)
- **Constraint**: 2-core, 7GB RAM runner.
- **Analysis**: 
  - Qwen3 (if available) is likely > 10GB.
  - Qwen-7B is too large.
  - Qwen-1.8B is approximately 3.6GB (FP16) or 7.2GB (FP32). This is risky for FP32.
  - Qwen2-0.5B is approximately 1GB, leaving ample room for the OS and Python overhead.
- **Solution**: Use a dual-model setup: 0.5B (Draft) + 1.8B (Target). The total memory footprint will be within the multi-gigabyte range for FP16 precision or the multi-gigabyte range for FP32 precision. We will default to FP16 if supported on CPU, otherwise FP32 with aggressive garbage collection. If OOM occurs, the system will fallback to 0.5B for both (reducing speedup potential but ensuring run completion).

### 3. Runtime Constraints (45 Minutes)
- **Constraint**: 45-minute timeout.
- **Analysis**: LLM inference on CPU is slow. Generating multiple tokens for a 0.5B/1.8B model might take several seconds per prompt. 5 prompts x 10 runs = 50 prompts. 50 * 5s = 250s ([deferred]). This is safe.
- **Solution**: Limit the benchmark to 5 prompts repeated 10 times (n=10). Implement a hard timeout kill at a predefined duration.

## Methodological Rigor

### 1. Statistical Validity
- **Metric**: Speedup Ratio = `Baseline_Latency` / `Domino_Latency`.
- **Baseline**: Standard autoregressive generation (no draft).
- **Domino**: Speculative decoding with a draft model.
- **Rigour**: Since this is a non-deterministic benchmark on a shared CI runner (OS scheduling noise, thermal throttling), a single run is insufficient. We will run each configuration **10 times** (n=10) and report the **mean**, **standard deviation**, and **95% confidence interval** of the speedup ratio. A bootstrap test with a sufficiently large number of iterations will be used to determine if the mean speedup is statistically significantly greater than 1.0.
- **Comparison**: The paper claims a significant speedup on GPU. We will explicitly state that CPU speedups are expected to be lower (e.g., 1.5x - 3x) due to the overhead of Python loops and lack of parallelism. The success criteria is **Speedup > 1.0x (with 95% CI > 1.0)**, not matching the 5.49x exactly.

### 2. Causal Inference & Assumptions
- **Assumption**: The "Domino" algorithm provides a speedup regardless of hardware, provided the draft model is smaller/faster.
- **Limitation**: We cannot claim the exact x speedup on CPU. We are validating the *existence* of the speedup, not the magnitude. The comparison to the 5.49x claim is purely for context and will be flagged as "N/A (Hardware Mismatch)" if the hardware differs.

### 3. Measurement Validity
- **Instruments**: `transformers` library's `generate()` method with `time.perf_counter()` for latency.
- **Validation**: The output JSON must contain `tokens_per_second` > 0 and `latency` > 0.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Model**: Qwen2-0.5B (Draft) + Qwen2-1.8B (Target) | Fits in 7GB RAM; available on HuggingFace; size differential ensures speculative decoding potential. |
| **Precision**: FP16 (preferred) or FP32 | FP16 reduces memory footprint; FP32 used if FP16 unsupported on CPU. |
| **Prompt Count**: 5 prompts x 10 runs | Ensures < 45 min runtime; sufficient for statistical significance (n=10). |
| **Hardware**: CPU Only | Mandatory for GitHub Actions free tier. |
| **Success Criteria**: Speedup > 1.0 (95% CI) | Realistic for CPU; validates algorithmic efficacy without over-promising. |
| **Validation Target**: Mechanism Feasibility | Decoupled from GPU claim magnitude to avoid category error. |

## References

- **Paper**: "Domino: Decoupling Causal Modeling from Autoregressive Drafting in Speculative Decoding" (arXiv:2605.29707). *Note: arXiv ID 2605.29707 appears to be a future date or typo in the prompt; standard arXiv IDs are YYMM.NNNNN. Assuming the title is correct and the code is vendored.*
- **Model**: Qwen2-0.5B-Instruct, Qwen2-1.8B-Instruct (HuggingFace Hub).
- **Library**: `transformers` (HuggingFace).
