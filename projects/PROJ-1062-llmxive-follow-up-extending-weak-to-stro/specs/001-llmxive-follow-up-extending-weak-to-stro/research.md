# Research: Cross-Architecture Distillation

## 1. Problem Statement & Hypothesis

**Hypothesis**: The implicit reward signal derived from a dense Transformer teacher's policy shift retains its efficacy when transferred to a student model with a fundamentally different architectural inductive bias (MoE or SSM), provided the signal is computed as a log-ratio of probabilities and applied via on-policy distillation.

**Null Hypothesis ($H_0$)**: There is no significant difference in performance gain (log-probability improvement) between students trained with the implicit reward (Direct-OPD) and those trained with a standard baseline (teacher distribution only), regardless of architecture.

**Alternative Hypothesis ($H_1$)**: Students trained with the implicit reward show a statistically significant performance gain over the baseline.

## 2. Dataset Strategy

The study relies on the **AIME 2024** dataset (MathArena/HuggingFace) for reasoning tasks.

| Dataset | Role | Source URL (Verified) | Access Method |
| :--- | :--- | :--- | :--- |
| **AIME 2024** | Training & Evaluation | `https://huggingface.co/datasets/MathArena/aime_2024/resolve/main/data/train-00000-of-00001.parquet` | `datasets.load_dataset(..., trust_remote_code=True)` |
| **AIME 2024 (Human-Verified Subset)** | Validity Check (SC-006) | `data/raw/human_verified_subset.jsonl` (Curated manually) | Local file, checksummed. |

**Dataset-Variable Fit Verification**:
- **Required Variables**: Math problems (prompts), ground-truth reasoning steps (targets).
- **Fit Confirmation**: The AIME 2024 dataset contains complex mathematical reasoning problems with step-by-step solutions. This aligns with the requirement to evaluate "log-probability of ground-truth reasoning steps."
- **Gap Analysis**: No mismatch exists for the current scope. The "post-task anxiety" warning in the general methodology panel does not apply to this math-reasoning study.

### Teacher Checkpoint Strategy

The "RL-induced" teacher checkpoints (pre-RL vs post-RL) are critical.
1.  **Primary Source**: Attempt to load `MathArena/aime_2024` teacher checkpoints if publicly available (e.g., `MathArena/aime_2024_teacher_pre_rl`, `MathArena/aime_2024_teacher_post_rl`).
2.  **Fallback (Synthetic Shift)**: If specific AIME 2024 RL checkpoints are unavailable (highly likely), the plan will generate a *verified* policy shift:
    - **Base Model**: Load `Qwen/Qwen1.5-1.8B` (verified public base).
    - **Post-RL Model**: Fine-tune the base model on a small, public subset of `HuggingFaceH4/ultrafeedback` (200 examples) using a standard RLHF objective to create a *known* shift.
    - **Verification**: Ensure the `pre-RL` and `post-RL` states are from the *exact same base model* to isolate the RL signal.
    - **Rationale**: This ensures the "shift" is purely RL-induced, not confounded by base model differences, and provides a reproducible source for the experiment.

## 3. Methodology

### 3.1 Implicit Reward Computation (FR-001)
For each token $t$ in a reasoning sequence:
$$ R_{implicit}(t) = \log P_{post}(t | \text{context}) - \log P_{pre}(t | \text{context}) $$
Where $P_{post}$ and $P_{pre}$ are the probability distributions from the teacher's post-RL and pre-RL checkpoints, respectively.
- **Stability**: Epsilon smoothing ($\epsilon = 10^{-9}$) applied before log to prevent NaN.
- **Decoupling**: This computation is performed *before* loading the student, ensuring the reward signal is independent of the student's architecture.

### 3.2 Student Training (FR-002, FR-003, FR-004)
Two student architectures are tested:
1.  **MoE Student**: Mixtral-8x7B (quantized to int8) or similar 1B MoE variant.
2.  **SSM Student**: Mamba-1.3B (quantized to int8).

**Training Loop**:
- **Objective (Direct-OPD)**: Maximize $\sum R_{implicit}(t)$ for the student's generated tokens.
- **Objective (Baseline)**: Maximize $\log P_{teacher\_final}(t)$ (Standard Distillation).
  - *Note*: The Baseline controls for the *static* teacher distribution. The Direct-OPD controls for the *shift* (log-ratio). This isolates the contribution of the RL-induced shift by comparing the *incremental* gain of the shift against the static baseline.
- **Constraints**:
  - Batch Size: Minimal (hard limit).
  - Gradient Accumulation: 8 steps (to simulate batch size 8).
  - Precision: int8 (via `bitsandbytes`).
  - Device: CPU.
  - Steps: A sufficient number of iterations per architecture to ensure convergence.

### 3.3 Human Verification Protocol (SC-006, FR-009)
To address the tautology concern and satisfy SC-006:
1.  **Subset Selection**: Select a representative subset of problems from the AIME 2024 test set.
2.  **Human Labeling**: Human experts verify the correctness of the reasoning steps for a representative set of problems. If the teacher's output was incorrect, the human-verified ground truth will differ.
3.  **Ground Truth**: The "ground truth" for evaluation is the human-verified solution, not the teacher's output.
4.  **Metric**: The evaluation metric "log-probability improvement" will be calculated *only* against these **human-verified** steps. This ensures the metric measures the student's ability to learn *correct* reasoning, not just mimic the teacher's (potentially wrong) distribution.

### 3.4 Statistical Analysis (FR-006, US-3)
- **Unit of Analysis**: The 200 problems. The "improvement" is aggregated per problem (sum of log-prob differences for all tokens in the ground-truth sequence for that problem). This ensures N=200 for the statistical test, satisfying the independence assumption.
- **Test**: Paired t-test (or Wilcoxon signed-rank if normality fails, tested via Shapiro-Wilk) on the vector of 200 difference scores.
- **Correction**: Bonferroni correction for 2 comparisons (MoE vs Baseline, SSM vs Baseline).
  - Adjusted $\alpha = 0.05 / 2 = 0.025$.
- **Assumption**: Observational regarding architecture; results framed as associational.
- **Power Limitation**: Explicitly acknowledge that N=200 may be underpowered for small effect sizes. Report Minimum Detectable Effect Size (MDES). Null results will be framed as "inconclusive" if power is insufficient.

### 3.5 Hardware Confound Control (Methodology-bd8c9780)
- **Constraint**: CPU training introduces noise and slower convergence.
- **Mitigation**: All four experimental arms (MoE-Direct, MoE-Baseline, SSM-Direct, SSM-Baseline) use *identical* hyperparameters, batch sizes, and accumulation steps.
- **Isolation**: The "architectural" variable is isolated because the "hardware" variable is constant across all arms. The comparison is *relative* (Direct vs. Baseline) within each architecture, not absolute.

## 4. Compute Feasibility & Escape Hatch

### CPU-First Strategy
- **Models**: 1B-1.3B parameters in int8 (~1.5GB - 2GB VRAM/RAM).
- **Memory Budget**: 7GB RAM.
  - Model Weights: ~GB.
  - Activations/Context: ~GB (with small batch).
  - Overhead: Significant memory overhead.
- **Strategy**: Use `torch.backends.cpu` optimized kernels. Disable CUDA. Use `accelerate` with `device_map="cpu"` and `load_in_8bit=True`.

### GPU Escape Hatch (Kaggle)
- **Trigger**: If the training loop fails with `CUDA out of memory` (unlikely on CPU-first plan) or if the spec explicitly requires a GPU-native operation (e.g., specific SSM kernel not available on CPU).
- **Plan**: The implementation will include a fallback flag. If the runner detects a GPU requirement (via error log), the execution stage will re-run on Kaggle with:
  - `device="cuda"`.
  - Reduced steps (e.g., 200) to fit within 9h kernel.
  - **Note**: This plan is designed to run on CPU. The GPU escape hatch is a contingency for *unexpected* CUDA requirements, not a primary path.

## 5. Risk Management

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Model OOM** | High | Enforce batch size 1 + gradient accumulation. Use int8. |
| **Time Limit Exceeded** | High | Limit to 500 steps. Use streaming dataset. |
| **Reward Instability** | Medium | Epsilon smoothing. Clip log-ratios. |
| **Dataset Unavailable** | High | Use verified HuggingFace URLs. Fallback to local cache if network fails. |
| **Statistical Power** | Medium | Acknowledge limitation in report if $N < 30$. Define MDES. |
| **Teacher Checkpoint Missing** | High | Fallback to synthetic shift generation on a verified base model. |

## 6. Decision Rationale

- **Why CPU?** The free-tier runner has no GPU. The models (1B) are small enough for int8 CPU inference/training.
- **Why MoE & SSM?** To test the "architectural inductive bias" variable (US-1, US-2).
- **Why Bonferroni?** To control Family-Wise Error Rate (FWER) across the two distinct architecture tests (US-3).
- **Why AIME 2024?** It provides a standardized, objective reasoning benchmark with ground-truth steps, suitable for log-prob evaluation (SC-005).
- **Why Human Verification?** To break the tautology between training signal and evaluation metric (SC-006).