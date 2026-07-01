# Research: Reproduce & Validate iLLaDA

## Objective
To validate the feasibility of running the iLLaDA (Improved Large Language Diffusion Models) evaluation pipeline on CPU-only infrastructure and to generate qualitative artifacts. **Quantitative validation against the paper's full-sample claims is explicitly deemed infeasible** due to hardware constraints and statistical limitations.

## Dataset Strategy

The following datasets are used for the reproduction. Per project rules, only verified sources are referenced.

| Dataset | Purpose | Verified Source / Loader | Status |
|---------|---------|--------------------------|--------|
| **GSM8K** | Math reasoning benchmark | `datasets.load_dataset("gsm8k", "main")` (Verified via HuggingFace Hub) | **Valid** |
| **Big-Bench Hard (bbh)** | Complex reasoning | `datasets.load_dataset("lukaemon/bbh")` (Verified via HuggingFace Hub) | Valid |
| **ARC-Challenge** | Science QA | `datasets.load_dataset("allenai/ai2_arc", "ARC-Challenge")` (Verified via HuggingFace Hub) | Valid |

**Dataset Variable Fit**:
- **Required Variables**: `question`, `answer` (or `choices`), `type`.
- **Fit Confirmation**: All listed datasets contain the necessary `question` and `answer` fields required for the `eval_llada.py` prompt construction.
- **Subset Strategy**: To meet the 6-hour runtime and 7GB RAM constraint, the implementation will load only the first `N=5` samples.
  - **Fallback**: If OOM occurs, `N` is reduced to `1`.
  - **Traceability**: The `subset_id` in the output metadata will reflect the actual `N` used (e.g., `N=5_S=42_F=None` or `N=1_S=42_F=OOM`).

## Statistical Rigor & Methodology

### Multiple Comparisons & Error Control
Since the evaluation will run on a tiny subset (N≤5), no formal hypothesis testing or family-wise error correction is applicable. The goal is not to estimate population parameters but to verify code execution.

### Sample Size & Power
- **Acknowledgement**: The subset size (N≤5) is **statistically insufficient** to estimate benchmark accuracy or compare against the paper's full-sample results.
- **Rationale**: A random sample of 5 items has a standard error of [deferred] for accuracy (p=0.5). A deviation of ±5% from the paper's score is indistinguishable from sampling noise.
- **Conclusion**: **Quantitative validation (score comparison) is scientifically invalid** for this run. The plan explicitly removes this as a success criterion.
- **Reporting**: Results will be labeled as "Smoke Test (N=5)" and "Qualitative Only".

### Causal Inference & Validity
- **Nature of Study**: Observational (Reproduction). No causal claims are made.
- **Measurement Validity**: The benchmarks are standard, but the sample size precludes valid measurement of the model's true performance.

### Predictor Collinearity
N/A for this evaluation pipeline.

## Compute Feasibility Analysis

### Hardware Constraints
- **Runner**: GitHub Actions Free Tier (2 vCPU, ~7GB RAM).
- **Model**: iLLaDA 8B.
- **Memory Calculation**:
  - 8B parameters in `float16` = 16 GB.
  - 8B parameters in `float32` = 32 GB.
  - **Constraint**: 16 GB > 7 GB.
- **I/O Bottleneck Analysis**:
  - **CPU Offloading**: Using `accelerate` to offload weights to disk requires reading GBs of data for *every* forward pass.
  - **Impact**: For a large-scale model, this results in I/O times of minutes per token. Total inference time would exceed **days/weeks**, far exceeding the 6-hour CI limit.
  - **Conclusion**: Full inference with offloading is **physically impossible** within the time budget.

### Solution & Scope
1.  **Strict Subsetting**: Limit to `N=5` samples to minimize memory pressure and runtime.
2.  **Fallback Protocol**: If OOM occurs, reduce to `N=1` (Smoke Test only).
3.  **Qualitative Scope**: Shift "Validation" goal from "Score Matching" to "Artifact Generation" and "Code Execution".

### Runtime Estation
- **Subset (N=5)**: Estimated 1-2 hours (if memory fits without offloading).
- **Fallback (N=1)**: Estimated 10-20 minutes.
- **Risk**: If offloading is triggered, runtime exceeds 6 hours. The script must detect OOM and fallback immediately to avoid timeout.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use `datasets.load_dataset`** | Ensures verified, reachable sources. |
| **Disable GPU/CUDA** | Target runner has no GPU. |
| **Subset N=5 (Fallback N=1)** | Balances feasibility with "Smoke Test" requirements. |
| **Remove Quantitative Validation** | N=5 is statistically invalid for score comparison; CPU offloading is too slow. |
| **Schema Validation Required** | Ensures output integrity despite reduced scope. |

## Spec-Root Cause Flag
**Issue**: User Story 2 in `spec.md` requires a score "within ±5% of the paper's reported iLLaDA-Base score".
**Conflict**: This requirement is **statistically invalid** for N≤5 and **physically impossible** to verify given the hardware constraints.
**Action**: This plan explicitly rejects this success criterion. The spec must be updated to reflect that quantitative validation is out of scope for the CPU-only free-tier runner.