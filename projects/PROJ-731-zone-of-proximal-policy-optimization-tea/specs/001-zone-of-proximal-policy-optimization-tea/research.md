# Research: Zone of Proximal Policy Optimization

## Executive Summary

This research investigates the "Zone of Proximal Policy Optimization" (ZPPO): the hypothesis that increasing the quantity of teacher-provided prompt demonstrations in a PPO training loop improves sample-efficiency (performance per step) up to a point of diminishing returns. The study compares conditions ranging from zero to high-volume examples using a small language model (GPT-NeoX) on a CPU-only infrastructure. The design is a **Controlled Experiment** where prompt size is a fixed manipulation, allowing for causal claims about the effect of prompt quantity on sample efficiency within the experimental bounds.

## Dataset Strategy

The study relies on the **OpenAssistant (oasst1)** dataset for teacher demonstrations. This dataset provides high-quality human-annotated prompt-response pairs suitable for PPO training.

*   **Dataset Name**: OpenAssistant (oasst1)
*   **Source**: HuggingFace Hub (`OpenAssistant/oasst1`)
*   **Usage**:
    *   **Prompt Buffer**: We will sample `N` examples from the dataset to create the teacher demonstration buffer for each condition (0k, 10k, 50k, 200k).
    *   **Role in PPO**: The dataset serves as the *state* (prompt) for the PPO rollouts. The model generates the *action* (response) given the prompt. The "demonstration" is the context provided to the student model, which influences its policy. The model is *not* copying the responses (Imitation Learning) but learning to generate responses that maximize reward *given* these prompted contexts.
    *   **Validation**: The dataset is known to contain English text and is widely used for instruction tuning.
    *   **Constraint**: If the dataset size exceeds memory constraints during loading, we will stream it or sample immediately upon loading.

*   **Benchmark Datasets** (Transfer Tasks):
    *   **lambada_openai**: `lambada_openai` (via `datasets`)
    *   **truthful_qa**: `truthful_qa` (via `datasets`)
    *   **mmlu**: `mmlu` (via `datasets`)
    *   *Note*: These are standard HuggingFace benchmark suites. Access is verified via the `datasets` library.
    *   **Role**: These benchmarks serve as *independent* downstream tasks to measure the *generalization* of the policy trained on the prompt buffer. They are not used to compute the training reward, thus avoiding tautological validation.

**Dataset Fit Analysis**:
*   **Requirement**: The study needs a dataset of prompt-response pairs to serve as the "teacher" context.
*   **Fit**: `oasst1` contains high-quality instruction-response pairs. It is suitable for extracting the `prompt` field to use as the demonstration context for PPO rollouts.
*   **Gap Mitigation**: The spec mentions "teacher-provided prompt demonstrations." We interpret this as using the `prompt` field from `oasst1` as the demonstration context. The `response` field is not used for action copying but may be used to compute the reward (if a reference exists) or as a target for the reward signal.

## Methodological Rigor

### Statistical Design
*   **Design**: Controlled Experiment.
    *   *Rationale*: The prompt-size conditions (0k, 10k, 50k, 200k) are fixed, randomized manipulations. We can claim a causal effect of "prompt quantity" on "sample efficiency" within the experimental setup.
    *   *Claim Framing*: Findings will be framed as causal regarding the effect of prompt quantity on sample efficiency, acknowledging the bounded nature of the experiment.
*   **Sample Size / Power**:
    *   *Plan*: 3 independent seeds per condition (Total N=12 runs).
    *   *Limitation*: This is a pragmatic choice for CPU-tractability. A formal power analysis is deferred. We acknowledge that a small N may limit the detection of subtle effects.
    *   *Metric*: Coefficient of Variation (CV) < 0.05 on final scores (SC-005) will be used to assess stability.
    *   *Hypothesis Refinement*: Due to low power (N=12), **piecewise-linear regression** (which requires dense sampling around a breakpoint) is **statistically unsound** for detecting a specific "breakpoint" or "plateau". The analysis strategy is revised to:
        1.  **Monotonic Trend Test**: Use **Kendall's Tau** to test if performance increases monotonically with prompt size.
        2.  **Group Comparison**: Use **Kruskal-Wallis H-test** to detect if there are significant differences between the four prompt-size groups.
        3.  **Post-hoc Pairwise**: If Kruskal-Wallis is significant, perform Dunn's test with Bonferroni correction to identify which specific conditions differ (e.g., 0k vs 10k, 50k vs 200k).
        4.  **Plateau Detection**: A "plateau" will be inferred descriptively if the difference between the highest two conditions (50k vs 200k) is not statistically significant, while lower conditions show significant gains.
*   **Multiple Comparisons**:
    *   *Method*: Bonferroni correction or Holm-Bonferroni.
    *   *Application*: Applied when performing post-hoc pairwise comparisons across the 4 conditions for each of the 3 benchmarks.
    *   *Threshold*: Family-wise error rate α = 0.05.
*   **Censored Data Handling**:
    *   *Issue*: The larger condition may hit the 6-hour time limit before reaching the same number of PPO steps as the 0k condition, creating censored data.
    *   *Method*: **Tobit Regression** was considered but is inappropriate for N=12. Instead, we will use **Dynamic Step Adjustment** to ensure all runs reach a comparable number of steps or time limit, and treat the final step count as a covariate in the analysis. If a run is terminated early, the final metric is recorded at that step, and the step count is included in the analysis to control for exposure.

### Measurement Validity
*   **Instruments**:
    *   **lambada_openai**: Measures next-token prediction in context. Validated for language modeling.
    *   **truthful_qa**: Measures truthfulness and resistance to common misconceptions.
    *   **mmlu**: Measures knowledge across 57 subjects.
*   **Reward Signal**:
    *   **Definition**: The reward is the **normalized log-probability** of the correct token sequence (or the correct option letter in MMLU) generated by the model.
    *   **Rationale**: This provides a dense gradient for learning, avoiding the sparse reward problem of binary exact match.
    *   **Semantic Collapse Mitigation**: To prevent the model from learning to output only the correct letter (e.g., 'A') regardless of content, the reward will be computed as the log-prob of the *entire* answer string (if available) or the log-prob of the correct option *relative* to others. A negative reward penalty will be applied for high-confidence output on incorrect options during validation.
    *   **Transfer vs. Optimization**: The training reward is computed on the *training* prompts (oasst1), while the benchmarks measure the *outcome* of generalization to *new* tasks. This avoids tautological validation.

### Computational Feasibility (CPU-Only)
*   **Model**: GPT-NeoX-125M.
    *   *Rationale*: Large-scale language models are too large for GB RAM. 125M is small enough to fit in memory and train on 2 CPU cores within 6 hours (with dynamic step adjustment).
*   **Memory Management**:
    *   **Rollouts**: If memory exceeds a high threshold, the system will sample a subset of the prompt buffer (e.g., a maximum limit) and log `MEMORY_FALLBACK`.
    *   **Batch Size**: Dynamically adjusted to fit RAM.
*   **Runtime**:
    *   **Target**: < 6 hours per run.
    *   **Strategy**: Limit PPO iterations to a predefined maximum, but dynamically reduce if time per step exceeds the budget. The 6-hour limit is a hard constraint.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Model Selection**: GPT-NeoX-125M | Large-scale models are infeasible on GB RAM. 125M is CPU-tractable and allows for multiple seeds. |
| **Dataset**: OpenAssistant (oasst1) | Standard, high-quality instruction dataset. Fits the "teacher prompt" requirement as a prompt buffer for PPO rollouts. |
| **Reward**: Normalized Log-Probability | Provides dense gradient, avoids sparse reward problem. Mitigates semantic collapse with relative probability and negative penalties. |
| **Seeds**: 3 per condition | Balances reproducibility (SC-005) with CPU time constraints. |
| **Statistical Test**: Non-parametric (Kendall's Tau, Kruskal-Wallis) | Replaced piecewise-linear regression as it is unsound for N=12 and 4 discrete points. These tests are robust for small samples and ordinal/continuous data. |
| **Design**: Controlled Experiment | Prompt size is a fixed manipulation, allowing for causal claims within the experiment. |
| **Benchmarks**: Transfer Tasks | Used to measure generalization, not direct optimization, avoiding tautology. |