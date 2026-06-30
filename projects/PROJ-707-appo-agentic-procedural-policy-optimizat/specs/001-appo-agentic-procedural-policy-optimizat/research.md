# Research: APPO: Agentic Procedural Policy Optimization

## 1. Problem Statement
The research investigates whether the **Branching Score** (product of token-level entropy and future-value estimate) improves the sample efficiency of agentic RL agents in multi-step tool-use tasks. The primary metric is **steps-to-threshold** (environment interactions to reach [deferred] of the best pilot success rate).

## 2. Dataset Strategy

The project requires datasets for **MATH** and **Tool-Calling** (proxy for WebShop/HotpotQA).
*Note: The spec mentions WebShop and HotpotQA, but the provided `# Verified datasets` block does not contain URLs for them. Per the rules, we cannot invent URLs. We proceed with the available verified MATH data and the Tool-Calling dataset as a validated proxy for agentic behavior.*

### Verified Datasets (from Prompt)
| Dataset | Source URL | Format | Status |
|:--- |:--- |:--- |:--- |
| **MATH** | ` | Parquet | **Verified** |
| **Tool-Calling** | ` | Parquet | **Verified** (Tool-calling data) |

### Gap Analysis & Strategy
* **WebShop & HotpotQA**: The prompt's `# Verified datasets` block **does not** contain URLs for WebShop or HotpotQA.
 * *Action*: The plan **cannot** assume these datasets are available via the verified URLs.
 * *Mitigation*: The implementation will prioritize the **Tool-Calling dataset** as a proxy for "agentic tool-use" (since it contains explicit tool-call actions) and **MATH** for reasoning.
 * *Decision*: The research will focus on **Tool-Calling** and **MATH**. This is a documented deviation from the spec's requirement for WebShop/HotpotQA, justified by the lack of verified sources and hardware constraints.

### Data Preprocessing
* **MATH**: Extract problem statements and ground truth answers. Filter for multi-step reasoning problems.
* **Tool-Calling**: Extract prompt-response pairs with tool usage. **Crucial**: The "Tool-Success Heuristic" for the FVN is derived from the ground-truth success labels in this dataset.
* **Sampling**: To fit 7GB RAM, we will sample **[deferred]** of the training split for each experiment run (approx. 2k-5k samples).

## 3. Model Strategy

### Model Selection
* **Theoretical Target**: Llama 3.1 8B (4-bit).
* **Executable Target**: **TinyLlama 1.1B (4-bit)**.
 * *Rationale*: An B model (quantized to a lower precision) leaves insufficient RAM for context and overhead on a 7GB runner. TinyLlama (4-bit quantized) ensures stability and allows for the required number of training steps within the 6-hour window.
 * *Documentation*: The `research.md` and `paper` will explicitly state: "Due to CI memory constraints (7GB), the 8B model was deemed infeasible; the experiment was executed using TinyLlama 1.1B as a proxy."

### Branching Score Implementation
* **Entropy**: Computed from the softmax of logits at each token generation step.
 * $H_t = -\sum p_i \log p_i$
* **Future-Value Estimate ($V_{future}$)**:
 * *Source*: A **Frozen Value Network (FVN)** trained on a **distinct reward signal**.
 * *Distinct Signal Definition*: The FVN is trained on the **Tool-Success Heuristic** derived from the ground-truth success labels (binary: success/failure) in the Tool-Calling dataset. This ensures the FVN is decoupled from the PPO agent's policy optimization and not a tautological re-weighting.
 * *Formula*: $BS_t = H_t \times V_{future}(s_t)$.
 * *Integration*: $BS_t$ is used to weight the PPO loss term or as an intrinsic reward bonus.

### Threshold Definition
* **Threshold Value**: 80% of the maximum pilot score.
* **Pilot Score Calculation**: Derived from the **3 seeds** of the `No-Score` baseline (not 5, due to hardware constraints).
* **Fallback**: If the `No-Score` baseline fails to reach a stable rate, the threshold defaults to 50% of the max possible score (oracle fallback).

## 4. Statistical Methodology

* **Test**: Wilcoxon signed-rank test (non-parametric, suitable for small N=3).
* **Hypothesis**:
 * $H_0$: Median steps-to-threshold (Score) = Median steps-to-threshold (No-Score).
 * $H_1$: Median steps-to-threshold (Score) < Median steps-to-threshold (No-Score).
* **Multiple Comparison Correction**: Bonferroni correction applied to p-values across multiple ablation variants and a default configuration.
* **Power Analysis**: N=3 is low. We acknowledge low statistical power (often <0.2 for medium effects). The result will be reported as **"exploratory"** with a focus on **effect sizes** (rank-biserial correlation) and 95% confidence intervals, rather than strict p-value significance. This is a necessary trade-off for CI feasibility.

## 5. Computational Feasibility

* **Hardware**: 2 CPU cores, 7GB RAM, 14GB Disk.
* **Runtime Budget**: 6 hours per job.
* **Strategy**:
 * **Sequential Execution**: Run seeds sequentially to avoid memory contention.
 * **Early Stopping**: If an agent reaches threshold at a predefined step, stop immediately.
 * **Batch Size**: Set to 1 to minimize memory.
 * **Sequence Length**: Limit to 128 tokens (reduced from 256 to save memory).
 * **Total Runs**: 3 (No-Score) + 3 (Score-Default) + 12 (Ablation, 1 seed each) = 18 runs.
 * *Estimate*: 18 runs × 15 mins/run = 4.5 hours (plus overhead). Fits within 6-hour limit.
 * **Final Decision**: The plan implements multiple seeds for baseline/default and one seed for ablation to ensure completion.

## 6. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use TinyLlama 1.1B** | 8B model is infeasible on 7GB RAM. 1.1B ensures stability. |
| **Use Tool-Calling as Proxy** | WebShop/HotpotQA URLs not verified. Tool-Calling dataset provides explicit tool-use actions. |
| **Sequential Seed Execution** | Parallel execution would exceed RAM limits on 2-core runner. |
| **Wilcoxon Test with N=3** | Small sample size violates normality assumptions for t-test. Acknowledge low power. |
| **Bonferroni Correction** | Required for multiple comparisons across 12 ablation variants. |
| **Threshold Fallback** | Prevents undefined metric if baseline fails. |