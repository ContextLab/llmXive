# Research: OPID: On-Policy Skill Distillation for Agentic Reinforcement Learning

## Executive Summary

This research phase validates the feasibility of reproducing the OPID algorithm on CPU-only CI. The core challenge is adapting a likely GPU-optimized RL algorithm to a 7GB RAM, 2-CPU environment while preserving the "critical-first routing" and "dual-advantage" mechanisms. 

**Critical Methodological Adjustment**: To strictly adhere to on-policy RL assumptions, the "RingBuffer" approach has been discarded. The strategy now employs a **Strict On-Policy Generator** that collects trajectories, performs a single gradient update, and immediately discards the data. This prevents the bias introduced by stale data from previous policies. Memory safety is achieved by limiting batch sizes, not by buffering.

The strategy involves strict dependency pinning for CPU wheels, implementing a dynamic trajectory buffer with sampling (via batch size limits), and utilizing a small subset of ALFWorld tasks for validation.

## Dataset Strategy

The ALFWorld environment is text-based and does not require a massive pre-loaded dataset for *inference* or *training* in the traditional sense; it generates trajectories on-the-fly. However, for initial setup and potential fine-tuning seeds, we rely on verified sources.

| Dataset | Source | Usage | Verification |
| :--- | :--- | :--- | :--- |
| ALFWorld (Train) | https://huggingface.co/datasets/yijunyang/alfworld-sft-dataset/resolve/main/train.tar.gz | Reference for task distribution; not loaded entirely into RAM. | Verified HuggingFace URL. |
| ALFWorld (Factual) | https://huggingface.co/datasets/Heaplax/ARMAP-RM-ALFWorld/resolve/main/alfworld_factual.json | Validation of environment logic. | Verified HuggingFace URL. |
| ALFWorld (Parquet) | https://huggingface.co/datasets/crislmfroes/alfworld/resolve/main/data/train-00000-of-00001.parquet | Potential sample for initialization. | Verified HuggingFace URL. |
| OPID Algorithm | NO verified source found | N/A | The algorithm logic is vendored in `external/OPID`. |

**Note**: The OPID algorithm itself is not a dataset but a training procedure. We do not cite a URL for the algorithm. We rely on the vendored code in `external/OPID`.

## Algorithmic Feasibility & Constraints

### 1. CPU-Only Execution (FR-001, SC-004)
The primary blocker for CI is the assumption of CUDA.
- **Strategy**: The `training.py` wrapper will enforce `torch.set_device("cpu")` and patch any `cuda()` calls.
- **Library Selection**: `torch` must be installed from the CPU-only wheel index (`--index-url https://download.pytorch.org/whl/cpu`).
- **Risk**: If `external/OPID` uses `bitsandbytes` for 8-bit quantization (common in LLM RL), it will fail on CPU.
- **Mitigation**: The plan mandates a check in `research.md` to replace `bitsandbytes` with standard `float32` precision if detected, noting the memory trade-off.

### 2. Memory Management & On-Policy Integrity (Edge Case: OOM)
- **Constraint**: 7GB RAM total.
- **Strategy**: Implement a `StrictOnPolicyGenerator`. Trajectories are collected for a batch, gradients are computed, the policy is updated, and the trajectories are **immediately discarded**.
- **Justification**: This satisfies the spec's requirement for a "sampling strategy" (via batch size limits) while strictly preserving the on-policy assumption. Discarding old data is not "sampling" in the sense of a buffer, but a necessary step to avoid bias.

### 3. Critical-First Routing (FR-003, SC-005)
- **Mechanism**: The algorithm identifies "critical" steps (e.g., object interaction) to apply step-level distillation.
- **Fallback**: If the heuristic fails (or no critical step is found), it defaults to episode-level skills.
- **Validation**: We will instrument the logger to count `skill_type: episode` vs `skill_type: step`. We expect >10% episode-level fallbacks (SC-005).

### 4. Dual Advantage Calculation (FR-004)
- **Components**: `Outcome Advantage` (reward-based) + `Distillation Advantage` (log-prob shift).
- **Feasibility**: Both are scalar calculations per token/step. Computationally light on CPU.
- **Validation**: We will verify that `log_prob_shift` variance > 0 (SC-002) to ensure the model is not ignoring the distillation signal.

## Statistical Rigor & Validation Plan

### Sample Size & Power
- **Limitation**: Running 100 steps on 5 tasks is a *feasibility smoke test*, not a statistically powered experiment.
- **Approach**: We do **not** claim "superiority" in the final paper sense. We claim "non-degenerate behavior" and "trend consistency" (SC-003).
- **Baseline Comparison**: We will run a simplified "Outcome-Only" RL agent (same architecture, no skill distillation) on the same 5 tasks.
- **Metric**: Success Rate.
- **Tolerance**: OPID success rate must be within ±10% of the baseline. If OPID < 10% success, the implementation is considered broken.
- **Disclaimer**: With N=5, the power to detect a difference is near zero. This check is strictly to ensure the algorithm does not crash or produce degenerate results (e.g., [deferred] success).

### Multiple Comparison Correction
- **Context**: We are running multiple independent task evaluations.
- **Method**: Since this is a trend check and not a formal hypothesis test for publication, we will report the mean success rate and standard deviation. If formal testing were required, a Bonferroni correction would be applied, but for CI smoke tests, the mean/variance check suffices.

### Ablation & Construct Validity (Addressing Methodology Concerns)
To address concerns about construct validity (non-zero variance vs. effective learning):
1.  **Ablation Control**: We will run a configuration where the distillation weight is set to 0.
2.  **Primary Dependent Variable**: Instead of just success rate, we will analyze the **correlation** between `distillation_advantage` magnitude and step-level success (or error reduction) in the full model vs. the ablated model.
3.  **Validation**: If the full model shows a positive correlation between `distillation_advantage` and success, while the ablated model does not, this provides evidence that the distillation signal is driving learning, not just noise.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-Only Torch** | Mandatory for GitHub Actions free tier. GPU wheels are not supported. |
| **Strict On-Policy Generator** | Replaces RingBuffer to preserve on-policy assumptions. Discarding data after update is the only valid approach for on-policy RL. |
| **Small Subset (5 tasks)** | Full ALFWorld evaluation takes hours. A set of tasks provides a representative sample for the established CI time limit. |
| **Ablation Study** | Necessary to prove the distillation signal is effective, not just a byproduct of policy updates. |
| **Vendored Code Wrapper** | Allows us to patch constraints without modifying the original research code, ensuring reproducibility of the core logic. |