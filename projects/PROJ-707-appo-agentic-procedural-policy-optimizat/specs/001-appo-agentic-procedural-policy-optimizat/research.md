# Research: APPO: Agentic Procedural Policy Optimization

## 1. Research Question & Hypothesis

**Question**: How does the Branching Score (Token Entropy × Future Value) affect sample efficiency in agentic RL tool-use tasks compared to standard PPO?

**Hypothesis**: The Branching Score, defined as `ReLU(V(s) - mean(V)) * H_t`, provides a more targeted exploration bonus than standard entropy regularization. This will lead to a statistically significant reduction in the number of steps required to reach [deferred] success rate (p < 0.05) on the MATH benchmark, compared to the No-Score baseline.

**Note on Circularity**: The Branching Score uses V(s), which is trained on task rewards. The hypothesis is not that V(s) *is* the success signal, but that the *interaction* of entropy and value (exploration in high-value, uncertain states) accelerates the learning of V(s) itself in sparse-reward environments. The validation compares the *speed* of convergence, not the final value.

## 2. Dataset Strategy

The project utilizes the **MATH** benchmark. HotpotQA and WebShop are excluded from the primary run due to lack of verified URLs in the input block and the inability to verify their tool-use modality.

| Dataset | Verified URL | Usage | Notes on Variable Fit |
|:--- |:--- |:--- |:--- |
| **MATH** | ` | Math reasoning benchmark | Contains problems and solutions. **Synthetic Environment**: The `environments.py` wrapper will simulate tool-use actions (e.g., "Search", "Calculate") based on the problem text to generate the action space and reward signals required for PPO. |
| **HotpotQA** | *No verified raw URL provided* | Excluded | Not used due to lack of verified source. |
| **WebShop** | *No verified raw URL provided* | Excluded | Not used due to lack of verified source. |

**Dataset Variable Fit Check**:
- **Required**: Interaction traces (tool calls, success/failure).
- **MATH**: Does not natively contain tool-call traces. The **Synthetic Environment Wrapper** (Phase 0) will define a discrete action space (e.g., `['Search', 'Calculate', 'Answer']`) and generate synthetic rewards based on intermediate steps. The "future-value" V(s) is learned from these synthetic rewards, not pre-existing data.
- **Validation**: Phase 0 includes a pre-check to ensure the synthetic environment generates non-trivial reward signals and that V(s) converges on a small subset.

## 3. Methodology

### 3.1 Model & Architecture
- **Base Model**: Llama 3.1 8B (Quantized 4-bit GGUF).
- **Loading Strategy**: `llama-cpp-python` with `q4_k_m` quantization to ensure <GB RAM usage.
- **Context**: 256 tokens (FR-001).
- **Value Head**: Standard PPO value head trained on task rewards.

### 3.2 Branching Score Calculation (FR-002)
To address the issue of negative values and circularity:
1. **Entropy ($H_t$)**: Compute Shannon entropy of the policy distribution over the vocabulary at the current step.
2. **Future Value ($V(s)$)**: The value function estimate for the current state $s$.
3. **Baseline Subtraction**: Calculate $V_{base} = \text{mean}(V(s))$ over a window.
4. **Branching Score ($B_s$)**: $B_s = \text{ReLU}(V(s) - V_{base}) \times H_t$.
 - This ensures the bonus is zero or positive, encouraging exploration only when the value is above the average (high-value regions) and uncertainty is high.
5. **Bonus**: Add $B_s$ (scaled by $b$) to the standard reward $R_t$.

### 3.3 Training Configurations (FR-003)
1. **No-Score (Baseline)**: Standard PPO. Bonus = 0.
2. **Score-Default**: $\epsilon=0.1, \epsilon'=0.05, b=0.5$.
3. **Score-Ablation**: Grid search over $\epsilon \in \{0.05, 0.2\}, \epsilon' \in \{0.02, 0.1\}, b \in \{0.3, 0.7\}$. (Limited to 1 seed per config due to time).

### 3.4 Statistical Analysis (FR-007, SC-001, SC-002, SC-007)
- **Metric**: "Steps to reach [deferred] success rate".
- **Unit of Analysis**: The **Training Run** (seed).
- **Event Definition**: Crossing the 80% success threshold within a rolling window of episodes.
- **Censoring**: If a run does not reach [deferred] by [deferred] steps, it is censored.
- **Test**: Kaplan-Meier survival analysis with Log-Rank test to compare Baseline vs. Score-Default.
- **Variance Check (SC-002)**: Calculate the variance of steps-to-threshold across the ablation grid. Report if variance < 15% of the mean.
- **Collinearity Check (FR-009, SC-007)**: Pearson correlation between $H_t$ and $V(s)$. If $|r| \ge 0.9$, log a **WARNING** to `stderr` and `results/warnings.log`.

## 4. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free (2 CPU, 7GB RAM).
- **Model Size**: 8B parameters (4-bit quantized).
- **Time Limit**: 6 hours.
- **Step Limit**: **[deferred] steps** per run (reduced from 2M to fit time).
- **Seeds**: **2 seeds** per config (reduced from 5 to fit time).
- **Optimization**: Ablation limited to seed per config.

## 5. Decision Rationale

- **Quantization**: Mandatory for CPU feasibility.
- **Survival Analysis**: Mandatory due to censored data (runs that don't converge).
- **Metric**: "Steps to [deferred]" is the standard sample-efficiency metric.
- **Dataset Limitation**: Only MATH is used due to verified URL constraints. Synthetic wrappers are required to simulate tool-use.
- **Reduced Scale**: 2 seeds and 50k steps are the maximum feasible subset on the target hardware.

## 6. Limitations

- **Statistical Power**: With only 2 seeds, the study is underpowered.
- **Circularity**: The Branching Score uses V(s), which is derived from the reward signal. The hypothesis is that the *interaction* with entropy accelerates learning, but this is a weak empirical claim.
- **Synthetic Environment**: The tool-use actions are simulated, not real. Results may not generalize to real tool-use environments.