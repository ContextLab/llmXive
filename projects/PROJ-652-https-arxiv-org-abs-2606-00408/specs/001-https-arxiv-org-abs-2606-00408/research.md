# Research: Reproduce & Validate Observation Masking Regime Map

## Executive Summary

This research validates the existence of the **"Rising Limb"** of the regime map where observation masking improves agent performance for low-to-mid capacity models. The study **explicitly does not** attempt to validate the "Sharp Collapse" regime (284B models) as it is empirically inaccessible on free-tier CPU CI. The strategy relies on the `observation-masking` repository's vendored `eval.py` and the `SWE-bench` dataset. The study is constrained to CPU-only execution, requiring careful selection of model sizes (TinyLlama-1.1B and Phi-2-2.7B) and dataset subsets to fit within 7GB RAM and 6 hours.

**Critical Limitation**: The study cannot empirically verify the "inverted-U" shape (SC-001) because it only produces two data points (Rising Limb). The "Collapse" regime is treated as a theoretical boundary condition. The success of this study is defined by the verification of the **positive accuracy gain** (Rising Limb) and the **mechanistic correlation** (tokens saved vs. turns added), not the full curve shape.

**Correction to Previous Strategy**: The plan explicitly rejects simulating "saturation" via temperature adjustments or using 4B/8B models as proxies for 284B. These methods break the causal mechanism of the "sharp collapse" which relies on actual model scale. The study now focuses strictly on validating the "Rising Limb" using distinct, verified model architectures.

## Dataset Strategy

| Dataset Name | Source URL | Purpose | Variable Fit Check |
|:--- |:--- |:--- |:--- |
| **SWE-bench Verified** | ` | Primary benchmark for agentic search tasks. | **Verified**: Contains `problem_statement`, `repo`, `test_patch`. Sufficient to simulate tool calls and evaluate solution accuracy. **Mechanism Validation**: A diagnostic step is included to verify that SWE-bench trajectories actually contain "stale observation" patterns (redundant tool calls) that the masking logic targets. If no redundancy is found, the dataset is flagged as invalid for this specific mechanism. |
| **SWE-bench Multilingual** | ` | Optional secondary benchmark for robustness (if time permits). | **Verified**: Same schema as Verified. |

**Note**: No other datasets are used. The plan does not fabricate URLs. If the `observation-masking` repo relies on a specific internal dataset not listed, the plan will use the verified SWE-bench subset as the proxy, noting the limitation in the "Limitations" section.

## Model & Method Strategy

### Model Selection
Given the 7GB RAM and CPU-only constraint, the plan will **not** attempt to load 284B models or even large 70B models.
- **Strategy**: Use **two distinct, pre-trained models** as independent proxies for "Low" and "Mid" capacity:
 1. **TinyLlama-1.1B-Chat-v1.0**: Proxy for "Low" capacity (Parameter Count: 1.1B).
 2. **Phi-2-2.7B**: Proxy for "Mid" capacity (Parameter Count: 2.7B).
- **Rationale**: Temperature/top_p adjustments do not simulate capacity. Distinct models provide independent variables for the x-axis of the regime map. The "Saturation" point (284B) is outside the scope of this study; the "Sharp Collapse" regime is acknowledged as a theoretical boundary condition, not an empirical target.
- **Implementation**: Use `transformers` with `device_map="cpu"` and `torch_dtype=torch.float32` (or `float16` if memory allows) to ensure compatibility with CPU runners.
- **Mapping to Quantitative Axis**: To ensure the Regime Map plot has a valid x-axis, the `model_capacity_proxy` string (e.g., "TinyLlama") will be mapped to a quantitative `model_parameter_count` (1.1, 2.7) in the analysis phase.

### Experimental Design
1. **Baseline Run**: Execute `eval.py` with `--masking-off` on a representative subset of tasks from SWE-bench for both models.
2. **Masked Run**: Execute `eval.py` with `--masking-on` on the same set of tasks for both models.
3. **Instrumentation**: The `masking.py` module must explicitly calculate and log `tokens_saved` and `turns_added` for every task. If the base `eval.py` does not output these, the wrapper script will compute them by comparing the masked trajectory against the baseline trajectory (or by counting tokens saved during the masking event directly).
4. **Metrics**: Record `accuracy`, `tokens_used`, `turns_taken`, `masking_events`, `rate_limit_events`, and `truncation_events`.

### Statistical Rigor
- **Multiple Comparisons**: Since we are comparing two conditions (Masked vs. Baseline) across two model types, we will use a paired t-test (or Wilcoxon signed-rank test) for each model type.
- **Sample Size**: 50 tasks per condition is the minimum to visualize the trend. The plan explicitly acknowledges that a 2-point comparison (Small vs. Mid) **cannot statistically prove a non-monotonic 'inverted-U' shape**. The statistical objective is revised to:
 1. Verify **positive accuracy gain** (Masked > Baseline) for both models (Rising Limb validation).
 2. Verify the **mechanistic correlation** (tokens saved vs. turns added).
- **Causal Inference**: This is an observational study of the agent's internal state. We are manipulating the masking flag (intervention), but the model's behavior is emergent. Claims will be framed as "associational" unless the masking intervention is strictly randomized (which it is, by design of the experiment).
- **Collinearity**: `tokens_saved` and `turns_added` are likely definitionally related. We will report the correlation descriptively and avoid claiming independent causal effects between them.

## Mechanistic Analysis Plan

To validate the "token-for-turn" hypothesis:
1. **Correlation Analysis**: Calculate Pearson/Spearman correlation between `tokens_saved` and `turns_added` across all trajectory logs.
2. **Regime Map Plot**: Generate a scatter plot of `Model Capacity` (1.1B vs. 2.7B) vs. `Accuracy Gain` (Masked - Baseline). The expected shape is a positive gain (Rising Limb). The "Collapse" is noted as a theoretical extrapolation.
3. **Mechanism Verification**: Confirm that the correlation between `tokens_saved` and `turns_added` is positive and significant, supporting the "token-for-turn" trade-off.

## Limitations & Assumptions

- **Compute Limit**: The inability to run 284B models means the "Sharp Collapse" regime is **not empirically observable**. The study validates the "Rising Limb" and the mechanism, which are the necessary preconditions for the full regime map.
- **Dataset Fit**: SWE-bench is a software engineering benchmark. The original paper might have used different agentic tasks. We assume SWE-bench is a valid *proxy* for "agentic search" regarding the masking mechanism, but acknowledge the potential mismatch. A diagnostic step is included to verify the presence of "stale observation" patterns in SWE-bench.
- **API Rate Limits**: The plan assumes the use of local models or mock generators if external APIs are rate-limited, as per the spec's assumption. If external APIs are required, the exponential backoff strategy (FR-004) will be enforced.
- **Statistical Power**: A 2-point comparison cannot prove a curve shape. The study is limited to validating the *direction* of the effect (positive gain) and the *mechanism*.
- **Capacity Proxy Validity**: The study explicitly avoids using temperature or small models to simulate "saturation." The "Collapse" regime is treated as a theoretical limit, not an empirical target, to avoid breaking the causal mechanism.

## Decision Rationale

- **Why CPU-only?**: The project must run on GitHub Actions free tier. GPU is not available.
- **Why SWE-bench?**: It is the only verified dataset in the "Verified datasets" block that matches the "agentic search" domain.
- **Why 50 tasks?**: Balances the need for a visible trend with the 6-hour runtime limit.
- **Why TinyLlama and Phi-2?**: These are the largest CPU-feasible models that provide distinct capacity proxies without requiring GPU resources.
- **Why not Temperature Simulation?**: Temperature controls stochasticity, not capacity. Using distinct models is the only valid way to proxy capacity for the "Rising Limb" validation.
