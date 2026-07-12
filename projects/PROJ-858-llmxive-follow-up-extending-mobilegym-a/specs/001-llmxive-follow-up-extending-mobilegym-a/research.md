# Research: State-Guided Curriculum for MobileGym

## Problem Statement & Hypothesis

**Problem**: Training mobile GUI agents via random task sampling (Static Baseline) is inefficient, often wasting compute on tasks that are either too easy (already mastered) or too hard (impossible given current policy). This slows convergence and may lead to policies that overfit to specific easy tasks, failing to generalize to complex, state-dependent scenarios.

**Hypothesis**: A curriculum that dynamically selects tasks based on **State Coverage Vectors** (tracking high-impact UI variables) and targets the **30-70% success rate "sweet spot"** will achieve faster convergence (fewer steps to target success rate) and lower variance in Sim-to-Real transfer compared to a static random baseline.

**Key Assumption**: The selected "semantic state proxies" (e.g., `dark_mode`, `unread_count`) are statistically significant predictors of task difficulty. This is validated via the sensitivity analysis (FR-008) using **Point-Biserial Correlation** between **Task-Intrinsic State Complexity** (static count of required transitions) and **Task Success Rate** (measured on a static baseline), not the curriculum's own learning dynamics.

## Dataset Strategy

The project utilizes the **MobileGym** simulation environment and task definitions.

**Dataset Sources**:
1. **MobileGym Environment & Task Definitions**:
 * *Source*: **Official MobileGym Repository**: ` (Tag: `v1.0.0` or latest stable).
 * *Access*: The implementation will fetch the source code and task definitions from the official repository.
 * *Reproducibility*: The specific commit hash used is resolved at runtime and recorded in `data/raw/.checksums.txt` to satisfy Constitution Principle I. The `requirements.txt` will pin the dependency to this specific commit hash.
 * *Note*: No external HuggingFace dataset URL is provided in the "Verified datasets" block for MobileGym. The core training data comes from the official MobileGym repository.

**Data Split**:
* **Training Set**: 160 tasks (MobileGym standard train split).
* **Validation Set**: Subset of training tasks used for sensitivity analysis (FR-008) and scheduler tuning.
* **Test Set**: 256 tasks (MobileGym standard test split), including high state-dependency apps for transfer evaluation.
* **Held-out for Sensitivity**: 500 tasks (derived from combining train/test or a specific validation split if available) to compute the correlation. **Crucially, this set is evaluated using the Static Baseline only to prevent circular validation.**

## Methodology & Statistical Plan

### 1. State Coverage Instrumentation (FR-001, US-002)
* **Mechanism**: A wrapper around the MobileGym environment intercepts state transitions after every rollout.
* **Variables**: A predefined list of "semantic state proxies" (e.g., `app_settings.dark_mode`, `message_list.unread_count`).
* **Vector**: Binary array ($0=$ unexplored, $1=$ explored).
* **Aggregation**: Parallel rollouts (multiple tasks) aggregate transitions into a single coverage update without race conditions (US-002).

### 2. Dynamic Curriculum Scheduler (FR-002, US-001)
* **Input**: Current coverage vector, historical success rates per task parameter.
* **Estimated Success Rate Mechanism**: Calculated as an **Exponential Moving Average (EMA)** of the success rates of the last 50 rollouts for each specific task parameter ($\alpha=0.3$). This provides a real-time, non-circular difficulty estimate.
* **Phase 1 (Novelty)**: Select tasks where coverage < 5% (low novelty).
* **Phase 2 (Difficulty)**: Select tasks with estimated success rate (EMA) between 30-70%.
 * *Fallback*: If no tasks in 30-70%, expand to 10-90%. If still empty, fallback to maximum entropy selection.
* **Constraint**: Selection logic must complete in < 10% of batch execution time (US-001).
* **Traceability**: Log the specific state metrics triggering each selection (Constitution Principle VI) to `scheduler_trace.json` via the `metrics_triggered` field.

### 3. Training Protocol (FR-003, US-003)
* **Model**: **Qwen2-VL-2B-Instruct** (CPU-optimized).
 * *Rationale*: Qwen3-VL-4B is too slow for 2 vCPU/6h window. 2B is the largest model feasible.
 * *Fallback*: If 2B fails to complete [deferred] steps in 4 hours, switch to a distilled 1.8B model and reduce steps to [deferred].
* **Configuration**: Identical for both Baseline (Static Random) and Experimental (State-Guided).
 * *Quantization*: 4-bit quantization via `bitsandbytes` (CPU-optimized path) or `transformers` native.
 * *Context Window*: Adjusted if necessary to fit memory.
* **Duration**: Hard -hour wall-clock limit per run (FR-004).
* **Stopping Condition**: Time limit reached OR target success rate reached.

### 4. Evaluation & Analysis
* **Convergence (SC-001)**: Steps to reach [deferred] success rate.
* **Transfer Robustness (SC-002)**: Variance of success rates across high state-dependency apps on the held-out test set.
* **Curriculum Effectiveness (SC-003)**: % of batches in the 30-70% sweet spot.
* **Methodological Validity (SC-006, FR-008)**:
 * **Static Validation Set**: A set of 500 tasks evaluated *only* by the Static Baseline. The dynamic curriculum results are **excluded** from this validation to prevent circular logic.
 * **Metric**: **Point-Biserial Correlation** (for binary state transitions) or **Logistic Regression** (for multi-state complexity) between **Task-Intrinsic State Complexity** (static count of required transitions from task metadata) and **Success Rate** (from Static Baseline).
 * *Threshold*: $r \ge 0.5$ = Valid Proxy. $r < 0.3$ = Invalid Proxy (flag study).
 * *Note*: The plan explicitly uses "Task-Intrinsic State Complexity" rather than "unique states covered" to avoid the category error of correlating a global training state with a local task outcome.

### 5. Statistical Rigor Considerations
* **Statistical Power & Replication**: Given the 6-hour CPU constraint, a single run is underpowered. The plan mandates **3 independent training runs** per mode (Static vs. Dynamic) with different random seeds. The final metrics (convergence, variance) will be reported as mean ± 95% confidence interval across these 3 runs.
* **Effect Size**: The study is designed to detect large effect sizes (Cohen's $d > 0.8$) in convergence steps.
* **Multiple Comparisons**: Bonferroni correction applied if multiple metrics (convergence, variance, proxy validity) are tested simultaneously.
* **Causal Inference**: The comparison is experimental (controlled environment). Claims of "causality" are supported by the randomized control (Static Baseline) and identical model configurations.
* **Collinearity**: The "State Coverage Vector" variables are selected to be distinct semantic proxies. If variables are definitionally related, the analysis will report descriptive statistics and acknowledge potential collinearity.

## Compute Feasibility Analysis

* **Hardware**: GitHub Actions Free Tier (multi-core CPU, standard memory allocation, 14GB disk, No GPU).
* **Model Load**: Qwen-VLB in low-bit quantization (approx. 1.5-2GB RAM) is feasible on CPU.
* **Inference**: CPU inference for 2B models is slow. To fit the 6-hour window:
 * **Tiered Fallback Strategy**:
 1. **Primary**: Qwen2-VL-2B, [deferred] steps, batch size 4.
 2. **Fallback 1**: If time > 4h at [deferred] completion, switch to Qwen2-VL-1.8B (distilled).
 3. **Fallback 2**: If time > 5h, reduce steps to [deferred].
 * *Decision*: The plan explicitly includes these fallbacks in `code/training/runner.py` to guarantee completion.
* **Scheduler**: The scheduler logic is lightweight (matrix operations on binary vectors) and will easily meet the <10% latency constraint.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Model too slow for 6h** | High | Tiered fallback strategy (Model Size -> Step Count -> Batch Size) ensures completion. |
| **State Proxies Invalid** | High | Sensitivity analysis (FR-008) uses Static Baseline data; if $r < 0.3$, flag study and recommend expanding variable set. |
| **Scheduler Deadlock** | Medium | Fallback to random selection if all states covered or no tasks in sweet spot (Edge Case). |
| **Data Loss in Parallel** | Medium | Use file-locking or atomic writes for coverage vector aggregation. |
| **Circular Validation** | High | Sensitivity analysis explicitly excludes Dynamic Curriculum data; uses Task-Intrinsic Complexity vs. Static Baseline results. |