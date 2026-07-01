# Research: Macaron-A2UI Reproduction & Validation

## 1. Problem Statement

The goal is to reproduce the quantitative and qualitative results of the "Macaron-AUI" paper within a constrained computational environment (2 CPU, 7GB RAM, 6h limit). The primary challenge is adapting a likely GPU-optimized generative UI model to run on CPU-only infrastructure while maintaining the ability to generate visual artifacts and calculate the "Overall" accuracy metric.

**Critical Constraint**: This is a **strict reproduction** study. If the exact model weights are not available or cannot be run on CPU (even with quantization), the quantitative validation of the "75.6" score is declared **Uncomputable**. No proxy models or sub-sampled scores are used for the final claim.

## 2. Dataset Strategy

The project relies on the `Macaron-AUI-Bench` benchmark.

| Dataset Name | Description | Source / URL | Status |
| :--- | :--- | :--- | :--- |
| **A2UI-Bench** | The primary evaluation benchmark containing tasks for `annomi`, `esconv`, `multiwoz`, and `sgd`. | **NO verified source found** (Vendored Submodule) | **Vendored** |

**Analysis**:
- The `Macaron-AUI-Bench` is not available via a public URL in the verified datasets list.
- **Strategy**: The project assumes the repository is provided as a git submodule in `vendor/Macaron-A2UI-Bench`.
- **Risk**: If the submodule does not contain the `data/eval_300` directory or the model weights, the pipeline will fail at the data-loading step.
- **Mitigation**: The `setup-evaluation.sh` script will include a check for the existence of `data/eval_300` and the model weights. If weights are missing, the run proceeds in "Mock Mode" (if available) or fails gracefully with `status: "uncomputable"`.

**Variable Fit Check**:
- The study requires `annomi`, `esconv`, `multiwoz`, and `sgd` task instances.
- The benchmark is specifically designed for these datasets.
- **Conclusion**: The dataset fit is **valid** provided the submodule is correctly initialized.

## 3. Methodology & Statistical Rigor

### 3.1 Execution Strategy
The evaluation will be performed by invoking `evaluate_api_model.py` with the following constraints:
- **Device**: `cpu` (Explicitly forced).
- **Quantization**: **Mandatory GGUF (Q4_K_M)**. Standard FP/FP is physically impossible for 7B+ models on 7GB RAM. `bitsandbytes` is excluded as it often requires CUDA kernels.
- **Inference Engine**: `llama-cpp-python` is the required engine for CPU quantization.
- **Sub-sampling**: **None for scoring**. The full dataset must be processed. If the run times out (exceeds 6h), the score is marked "Incomplete". A "Mock Mode" with sub-sampling is available for debugging only.

### 3.2 Metric Definition
- **Primary Metric**: "Overall" Accuracy.
- **Paper Claim**: 75.6.
- **Validation Logic**:
  1. Check `model_name` in `EvaluationReport` matches the paper's model.
  2. If match: Calculate delta `|Reproduced_Score - 75.6|`.
  3. If no match or weights missing: Score is "N/A", Status is "Uncomputable".
  4. If timeout: Score is "N/A", Status is "Incomplete".

### 3.3 Causal/Associational Claims
- This is a **reproduction** study. No new causal claims are being made.
- The study validates the **implementation** of the model and the **consistency** of the benchmark.
- Any deviation in scores is attributed to:
  1. Hardware constraints (CPU vs GPU floating point differences).
  2. Randomness in generation (seed variance).
  3. **Missing Weights**: If weights are missing, the claim is invalid, not approximated.

### 3.4 Multiple Comparisons
- The study evaluates multiple datasets.
- Since the primary outcome is a single "Overall" score, family-wise error correction is not strictly required for the main metric.
- However, per-dataset scores will be reported descriptively without inferential statistical testing.

## 4. Computational Feasibility

- **Memory**: Limited RAM is tight for LLM inference.
  - **Plan**: Use **GGUF quantization** (Q4_K_M) via `llama-cpp-python`. This reduces a B model to ~4-5GB RAM, fitting within the 7GB limit.
  - **Fallback**: If the vendor code does not support `llama-cpp-python`, the run is marked "Incompatible".
- **Time**: 6 hours.
  - **Plan**: Run the full dataset. Monitor time-per-task. If the rate suggests the run will exceed 6h, the pipeline continues but marks the final score as "Incomplete".
  - **Monitoring**: The script will log time-per-task. If the run exceeds 6h, it exits with code 0 but sets `status: "timeout"`.

## 5. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-Only Execution** | Mandatory due to CI constraints. |
| **Mandatory GGUF Quantization** | FP16/FP32 for 7B+ models exceeds 7GB RAM. `bitsandbytes` is excluded due to CUDA dependency risks. |
| **No Model Substitution** | Substituting a model invalidates the "75.6" score comparison (Category Error). |
| **No Sub-sampling for Scoring** | Sub-sampling introduces high variance, making the "75.6" comparison statistically invalid. |
| **Vendored Benchmark** | No verified URL exists; submodule is the only viable source. |

## 6. References

- **Macaron-A2UI Paper**: (Referenced in spec, details to be extracted from `vendor/` README).
- **A2UI-Bench**: (Vendored, no external URL).