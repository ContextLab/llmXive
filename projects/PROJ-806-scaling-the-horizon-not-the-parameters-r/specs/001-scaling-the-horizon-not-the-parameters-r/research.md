# Research: Reproduce & Validate: Scaling the Horizon, Not the Parameters

## Executive Summary

This research phase validates the feasibility of reproducing the "Scaling the Horizon, Not the Parameters" paper's claims on a CPU-only, free-tier CI environment. The primary challenge is fitting a 35B parameter MoE model into ~7 GB of RAM while executing long-horizon benchmarks. The strategy involves using CPU-offloading techniques, sampling a subset of the benchmark data, and strictly enforcing resource limits.

**Critical Finding**: A large-scale model is likely infeasible on 7 GB RAM. The plan explicitly defines an **ABORT** behavior (`ERR_OOM_CPU`) if the model fails to load, adhering to the "No Silent Fallbacks" principle.

## Dataset Strategy

The research relies on the following verified datasets.

| Benchmark | Source/URL | Format | Usage Strategy |
|-----------|------------|--------|----------------|
| **IFBench** | (Official Repository) | Parquet/JSONL | Primary validation target. Uses the "binary" system to test reasoning chains. **Risk**: Data format may differ from official IFBench. If the official repo is inaccessible, the pipeline will skip the benchmark. |
| **SciCode** | https://huggingface.co/datasets/Zilinghan/scicode/resolve/main/problems_dev.jsonl | JSONL | Secondary validation target. Tests code generation capabilities. |
| **SEAL-0** | NO verified source found | N/A | **Excluded** from automated pipeline due to lack of verified source. Paper claims regarding specific quantitative metrics will be noted but not computationally validated in this CI run. |

*Note: The plan uses `datasets.load_dataset` or direct HTTP download for the verified URLs. No local files are assumed to exist.*

## Methodology & Statistical Rigor

### 1. Model Loading & Memory Strategy
- **Approach**: Use `transformers` with `device_map="auto"` and `torch_dtype=torch.float32` (or `float16` if supported by the CPU backend) combined with `accelerate` for offloading.
- **Constraint Handling**: The large-scale MoE model (active parameters) is estimated to require a substantial memory footprint in full precision. To fit in 7 GB:
 - **Aggressive Sampling**: Only a subset of samples per benchmark will be processed.
 - **Offloading**: Layers will be offloaded to disk (CPU RAM swap) if necessary, though this is slow.
 - **Abort Strategy**: If the model fails to load within 7 GB RAM, the system will **ABORT** with exit code `ERR_OOM_CPU`. It will **NOT** switch to a smaller model.
- **Risk**: The model will likely fail to load. The plan treats this as a "Feasibility Failure" rather than a logic error.

### 2. Inference & Token Limits
- **Horizon**: The spec mentions up to 45k tokens.
- **KV Cache Risk**: Even with a smaller proxy model, the KV cache for 45k tokens may exceed 7 GB RAM.
- **Strategy**: Implement a hard token counter and a **Context Truncation** strategy. If the estimated KV cache exceeds a safe memory threshold, the generation will be truncated to a safe token count (e.g., 4k) to prevent OOM. If `token_count > 4000`, stop generation, log `TIMEOUT_EXCEEDED`, and record the partial result.
- **Rationale**: Prevents a single long trajectory from consuming the entire 6-hour CI budget or causing an OOM crash. **Note**: This is a stability constraint, not a scientific validation of the 45k horizon.

### 3. Scoring & Validation
- **Logic**: Use the exact `judger/evaluate.py` from the `agents-a1` submodule.
- **Comparison**: Compare the calculated score against the paper's reported values (e.g., IFBench ≥ 80.6).
- **Statistical Note**: This is a *feasibility check*, not a statistical power study. The sample size (N=5) is insufficient to claim "reproduction" in a statistical sense (p-value, confidence intervals). The metric is **NOT** a pass/fail based on tolerance. The report will state "INCONCLUSIVE" for statistical validity.
- **Multiple Comparisons**: Not applicable (only one metric per benchmark).

### 4. Causal/Associational Claims
- The paper claims "Trillion-Parameter Performance" via scaling the horizon. This is a performance claim, not a causal inference study. No causal assumptions (randomization, identification) are required for this reproduction task.

## Compute Feasibility Analysis

- **Hardware**: GitHub Actions Free Tier (2 vCPU, ~7 GB RAM, ~14 GB Disk).
- **Model**: 35B MoE.
- **Feasibility**: **High Risk / Likely Infeasible**.
 - Loading a 35B model in `float32` requires ~140 GB.
 - Loading in `float16` requires ~70 GB.
 - Loading in `int8` (if available for CPU) requires ~35 GB.
 - **Conclusion**: A full 35B model **cannot** fit in 7 GB RAM, even with quantization, unless the "35B" refers to *active* parameters in a massive MoE (e.g., 35B active out of 1T total) and the loading strategy is extremely aggressive (e.g., loading only active experts for each token). Even then, the KV cache for 45k tokens will likely exceed 7 GB.
 - **Mitigation**: The plan explicitly assumes the "35B" refers to active parameters and that the model architecture allows loading only the active experts per step. If the codebase requires loading all parameters, the job will fail with `ERR_OOM_CPU`. The plan **DOES NOT** fallback to a smaller model.
 - **Token Constraint**: The automated run will cap generation at a token limit to ensure completion.

## Decision Rationale

1. **Exclusion of SEAL-0**: The spec lists SEAL-0 as a target, but the "Verified datasets" block states "NO verified source found". Inventing a URL is a blocking flaw. Therefore, the plan excludes SEAL-0 from the automated pipeline and focuses on IFBench and SciCode.
2. **CPU-Only Constraint**: The spec explicitly forbids GPU. Using `bitsandbytes` 8-bit quantization often requires CUDA. The plan will attempt to use `torch.cpu` quantization or `accelerate` offloading. If these fail, the job fails gracefully with `ERR_OOM_CPU`.
3. **Sample Size**: Running the full benchmark suite is impossible in hours with a 35B model on CPU. A sample of 5 items is chosen to verify the *pipeline* works and to get a rough score estimate.
4. **No Silent Fallbacks**: If the 35B model fails to load, the job will **ABORT** with `ERR_OOM_CPU`. It will **NOT** switch to a smaller model, ensuring the failure is explicit and not hidden.
5. **Statistical Validity**: The plan explicitly states that a small sample (N=5) cannot validate the paper's claims. The report will state "INCONCLUSIVE" for statistical validity.
