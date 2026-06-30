# Research: Self-Distilled Agentic Reinforcement Learning (SDAR) Reproduction

## 1. Research Objective

To reproduce and validate the *implementation* of the Self-Distilled Agentic Reinforcement Learning (SDAR) algorithm as described in arXiv:2605.15155. The primary goal is **mechanism execution validation** on the ALFWorld environment under strict CPU-only constraints, specifically verifying:
1. The correct execution of the SDAR training loop (gating + RL) without CUDA errors.
2. The ability to generate real loss metrics (Gate Loss, RL Loss) from actual environment interaction (or mock interaction if Thor fails).
3. A comparative baseline run (SDAR vs. PPO) to verify *implementation parity* (i.e., both algorithms run without crashing).

**Scope Limitation**: Due to the 6-hour CI limit and 2-core constraint, the training horizon (1000 steps) is insufficient for policy convergence. The statistical comparison (paired t-test) is **diagnostic only**. A non-significant result (p > 0.05) is expected and does not invalidate the reproduction; it simply reflects the lack of training convergence. The project does *not* claim that SDAR is superior to PPO.

## 2. Dataset Strategy

The "dataset" for this project is the **ALFWorld** environment, which provides the simulated household tasks for training and evaluation. No external static datasets are used; the data is generated dynamically during execution.

| Dataset/Source | Role | Verified Source | Loading Method |
|:--- |:--- |:--- |:--- |
| **ALFWorld (Text-Only)** | Environment for RL training/evaluation. | ` (Official) | `import alfworld` (via `pip install alfworld`). Fallback to `alfworld-text-only` if Thor binary fails. |
| **Vendored SDAR Code** | Implementation of the algorithm. | `external/SDAR` (Git Submodule) | Local import from `external/SDAR/agent_system/` |
| **Base LLM** | Teacher/Student model backbone. | `distilbert-base-uncased` (HuggingFace) | `transformers` (CPU-only load). Replaces 8B models for CPU feasibility. |

**Thor Binary Fallback**: If the official Thor binary download fails or cannot run on the CI headless environment, the pipeline will switch to `alfworld-text-only` mode (if available in the vendored code) or a mock environment that simulates the `success` flag and `reward` structure to verify the gating logic without the full simulator.

## 3. Methodology & Statistical Rigor

### 3.1 Experimental Design
The experiment consists of two parallel tracks:
1. **SDAR Track**: Training with the self-distillation gating mechanism enabled.
2. **PPO Baseline Track**: Training with standard PPO (no distillation) for comparison.

Both tracks will run for **5 independent random seeds** (`seed=0` to `seed=4`). To satisfy the 6-hour CI limit on 2 CPUs, the number of training steps per seed will be aggressively downscaled to **1000 steps**.

**Fixed Evaluation Set**: To ensure the paired t-test is valid, the same 5 ALFWorld tasks (hardcoded IDs from the test split) will be used for all seeds and both methods. This controls for task difficulty variance.

### 3.2 Statistical Analysis
- **Metric**: Final Success Rate (binary: 0 or 1 per task) and/or Cumulative Reward.
- **Test**: Paired t-test (or Wilcoxon signed-rank test if normality assumptions fail) comparing SDAR vs. PPO success rates across the 5 seeds.
- **Significance Threshold**: $p < 0.05$.
- **Power Limitation**: Acknowledged that with $N=5$ seeds and 1000 steps, the statistical power to detect any meaningful effect size is effectively zero. The result is reported as a "diagnostic metric" only. A non-significant result is expected and does not imply algorithmic failure.
- **Multiple Comparisons**: Not applicable, as only one primary comparison is performed.

### 3.3 Measurement Validity
- **Success Rate**: Defined strictly by the ALFWorld environment's `success=True` flag (or mock flag if Thor fails).
- **Loss Values**: Parsed directly from the `train.py` stdout logs to ensure they reflect actual gradient computations.
- **Device Binding**: Verified by checking logs for "0 GPUs detected" and explicit `device="cpu"` assignments.
- **Gate Activation**: Explicitly logged as a boolean per step to validate the self-distillation mechanism (Constitution Principle VI).

## 4. Compute Feasibility Strategy

To ensure the plan is runnable on the GitHub Actions free-tier (2 CPU, 7GB RAM, 6h):
- **Model Size**: `distilbert-base-uncased` (approx. 80M params). This fits comfortably in 7GB RAM on CPU, unlike 8B models.
- **Batch Size**: Fixed to `1` to minimize memory footprint.
- **Ray Configuration**: `ray.init(num_cpus=2, num_gpus=0)` to prevent resource contention.
- **Timeouts**: Hard 60s timeout per task in the evaluation loop to prevent hanging.
- **Memory Management**: Explicit garbage collection (`gc.collect()`) and tensor deletion between seeds to prevent memory leaks.
- **Feasibility Rationale**: 1000 steps x 5 seeds x 2 methods on a 80M model is estimated to take [deferred] per seed on 2 cores, totaling [deferred], which fits within the 6-hour limit.

## 5. Risk Mitigation

| Risk | Mitigation Strategy |
|:--- |:--- |
| **CUDA Import Errors** | Force `CUDA_VISIBLE_DEVICES=""` in environment variables before import. |
| **ALFWorld Binary Missing** | Rely on `alfworld` package's auto-download; if it fails, switch to `alfworld-text-only` or mock mode. |
| **Memory Overflow (OOM)** | Monitor RAM usage; if OOM occurs, reduce model size (e.g., to a smaller DistilBERT variant) or further downsample steps. |
| **Timeout Exceeded** | Enforce `signal.alarm(60)` in the evaluation loop; log "Timeout" as failure and continue. |
| **Statistical Non-Significance** | Report the p-value and effect size regardless of significance; the goal is validation of the *process*, not necessarily a positive result. |
| **Thor Binary Failure** | Fallback to text-only mode or mock environment to verify the SDAR gating logic without the simulator. |