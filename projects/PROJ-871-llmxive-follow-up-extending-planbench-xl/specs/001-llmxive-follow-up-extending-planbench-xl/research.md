# Research: llmXive follow-up: extending "PlanBench-XL: Evaluating Long-Horizon Planning of LLM Tool-Use Agents "

## 1. Problem Statement & Hypothesis

**Problem**: LLM tool-use agents often fail to recover from "implicit" tool failures (e.g., silent data corruption, unexpected output formats) because they rely solely on internal reasoning, which may not recognize the failure mode without explicit error messages.

**Hypothesis**: Augmenting LLM tool-use agents with lightweight, rule-based "failure signature" retrieval significantly improves recovery rates from implicit tool failures in large-scale, dynamic tool ecosystems compared to agents relying solely on internal reasoning.

**Null Hypothesis ($H_0$)**: There is no statistically significant difference in task completion success rates between the baseline agent and the signature-augmented agent.

**Alternative Hypothesis ($H_1$)**: The signature-augmented agent has a statistically significantly higher task completion success rate than the baseline agent (one-tailed test, $p < 0.05$).

**Causal Inference Scope**: This study uses a controlled intervention (synthetic failure injection) on a matched set of tasks. The random assignment of tasks to the "injected failure" condition (via the injection logic) and the use of the original ground truth as the outcome measure allow for **causal inference regarding the intervention** (signature retrieval) on recovery from these specific injected errors.

## 2. Dataset Strategy

The study relies on the **PlanBench** dataset. Since the canonical PlanBench dataset does not contain explicit "implicit failure" labels or tool-level failure traces, the study employs a **Synthetic Failure Injection** protocol to construct the test set.

### Verified Datasets
The following datasets have been verified for reachability and format. **Only these sources will be used.**

| Dataset Name | Verified URL | Relevance to Study |
|--------------|--------------|--------------------|
| PlanBench (Parquet) | ` | Primary source for task definitions, tool schemas, and original ground-truth outcomes. |
| PlanBench (Alternative 1) | ` | Backup source if primary link is unstable; same schema expected. |
| PlanBench (Alternative 2) | ` | Backup source; ensures redundancy. |

**Dataset Fit Analysis**:
- **Required Variables**: `task_id`, `goal`, `tool_definitions`, `ground_truth_success` (boolean), `execution_trace` (optional).
- **Synthetic Injection Strategy**: To create the "implicit failure" subset, the `code/dataset/injector.py` module will:
 1. Select a random subset of tasks (targeting 327 tasks as per Constitution) where `ground_truth_success` is `True`.
 2. Programmatically inject a deterministic error pattern (e.g., "Error: None") into the simulated tool output for a specific step in these tasks.
 3. This creates a known "failure" condition for the agent to recover from, independent of the original dataset's labels.
- **Constraint Check**: The dataset is in Parquet format, which is CPU-tractable. The synthetic injection is performed in memory, ensuring no modification of raw data.
- **Gap Handling**: The absence of native "implicit failure" labels is addressed by the synthetic injection protocol, which creates a valid, controlled test environment for the hypothesis.

## 3. Methodology

### 3.1. Failure Signature Index Construction (FR-002)
1. **Source**: *Synthetic Injection Logic*, NOT the dataset ground truth.
2. **Process**:
 - The `code/dataset/injector.py` defines a set of deterministic error patterns (e.g., `["Error: None", "Result: []"]`) that will be injected into the tool outputs.
 - The `code/dataset/indexer.py` constructs a static JSON index mapping tool IDs to these *injected* patterns and their corresponding recovery strategies (e.g., "retry", "fallback").
 - This index is **static**, **CPU-tractable**, and **independent** of the evaluation ground truth.
3. **Constraint**: This index is derived from the *injection logic*, ensuring no circular dependency with the outcome metric.

### 3.2. Agent Execution
**Environment**: CPU-only (2 cores, 7GB RAM).
**LLM**: A small, open-source model (e.g., `TinyLlama-1.1B`) hosted locally to ensure feasibility.

#### Baseline Agent (FR-003)
- **Logic**: Receives task goal and tool definitions.
- **Loop**:
 1. Generate tool call.
 2. Execute tool (with *injected* error if applicable).
 3. Receive output (containing the injected error).
 4. **No external check**: Relies on LLM to interpret the output and decide next steps.
 5. Repeat until success or max steps.
- **Output**: Execution log with final status.

#### Augmented Agent (FR-004, FR-008)
- **Logic**: Same as Baseline, but with an added step after tool execution.
- **Loop**:
 1. Generate tool call.
 2. Execute tool (with *injected* error if applicable).
 3. Receive output (containing the injected error).
 4. **Signature Check**: Compare output against the static JSON index for the invoked tool.
 - **Match**: Trigger predefined recovery strategy (e.g., re-plan with error context, retry with different parameters).
 - **No Match**: Proceed to LLM reasoning.
- **Output**: Execution log with flags for signature matches and recovery actions.

### 3.3. Statistical Analysis (FR-006, SC-003)
- **Metric**: Task Completion Success Rate = (Number of Successful Tasks) / (Total Tasks).
- **Test Selection**:
 - **Strict Adherence**: Per Constitution Principle VII, a **two-proportion z-test** is used exclusively.
 - **Power Analysis**: A power analysis is conducted to determine the minimum sample size required to detect a [deferred] effect size (MDES) with 80% power at alpha=0.05.
 - **Underpowered Protocol**: If the available subset (targeting 327 tasks) is smaller than the required sample size, the study will **not** perform a z-test. Instead, it will report the observed effect size with a 95% confidence interval and a disclaimer stating the study is "underpowered to validate the primary success criterion."
- **Significance Threshold**: $\alpha = 0.05$.
- **Reporting**: p-value (if powered), confidence interval (95%), and absolute difference in success rates.

## 4. Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (multiple vCPU, 7GB RAM, 14GB Disk).
- **Strategy**:
 - **Data**: Load only the necessary subset of PlanBench (up to 327 tasks) into memory.
 - **Model**: Use a small model (e.g., `TinyLlama-1.1B`) to ensure CPU compatibility.
 - **Runtime**: Limit to a reasonable duration. If the full subset is too large, the sample size will be reduced, and the underpowered protocol will be triggered.
 - **Memory**: Monitor RAM usage; use `pandas` with `dtype` optimization to stay under 7GB.

## 5. Decision Log & Rationale

| Decision | Rationale |
|----------|-----------|
| **Synthetic Failure Injection** | Resolves the lack of "implicit failure" labels in PlanBench and breaks the circular dependency between index construction and outcome measurement. |
| **Static JSON Index** | Ensures determinism (Constitution Principle VI) and low computational overhead (CPU-tractable). |
| **Strict Z-Test** | Adheres to Constitution Principle VII. The "underpowered" protocol handles small samples without violating the exclusive mandate. |
| **Small LLM Model** | Ensures feasibility on CPU-only runners; large models would exceed RAM or time limits. |
| **Sampled Subset (Target 327)** | Aligns with the Constitution's specific task count and the power analysis requirements for a [deferred] effect size. |

## 6. Risk Assessment

- **Risk**: Dataset lacks explicit "implicit failure" labels.
 - **Mitigation**: Resolved via Synthetic Failure Injection protocol.
- **Risk**: LLM inference exceeds 6-hour limit.
 - **Mitigation**: Use a smaller model; implement a timeout mechanism; reduce the number of tasks if necessary.
- **Risk**: Signature index produces false positives.
 - **Mitigation**: The index is derived from deterministic injection logic; false positives will be logged and analyzed as a limitation.
- **Risk**: Study is underpowered to detect a [deferred] effect size.
 - **Mitigation**: Power analysis is performed; if underpowered, the study reports the effect size with a limitation disclaimer rather than claiming significance.
