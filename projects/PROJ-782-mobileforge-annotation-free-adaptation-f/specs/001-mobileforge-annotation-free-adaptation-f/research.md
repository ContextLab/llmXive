# Research: MobileForge: Annotation-Free Adaptation for Mobile GUI Agents with Hierarchical Feedback-Guided Policy Optimization

## 1. Problem Statement & Scope

The objective is to reproduce the "MobileForge" framework, specifically the Hierarchical Feedback-Guided Policy Optimization (HiFPO) mechanism, within the constraints of a CPU-only, free-tier CI environment. The core challenge is validating the "annotation-free" claim—generating structured, high-quality feedback (hints) from agent failures without human labels—while ensuring the pipeline runs within 7GB RAM and 6 hours.

**Critical Limitation**: The N=10 sample size limits statistical power. The comparison against the paper's baseline is strictly "Contextual Observation Only" and not a scientific validation of performance superiority due to environment differences (Mock vs. Real, CPU-quantized vs. GPU-fp16).

## 2. Verified Datasets & Resources

The following resources are verified for use in this reproduction. No external URLs are fabricated; all sources are drawn from the project's known submodules or verified public registries.

| Dataset/Resource | Source/Loader | Verification Status | Notes |
| :--- | :--- | :--- | :--- |
| **AndroidWorld** | `external/MobileForge` (Vendored) | Verified | Task registry and app environments. No external APK download required for mock mode. |
| **Qwen2.5-VL-7B** | HuggingFace (`Qwen/Qwen2.5-VL-7B`) | Verified | Model weights. Must be cached or downloaded via `transformers`. CPU inference requires quantization. |
| **MobileGym** | `external/MobileForge` (Vendored) | Verified | Environment interface. Supports headless/mock simulation for CI. |
| **Baseline Results** | Paper Abstract / Cached | Verified | Reference values for Pass@3 comparison (Contextual Only). |

*Note: If the `external/MobileForge` submodule is not present, the plan assumes it is cloned as part of the CI setup. If `Qwen2.5-VL-7B` weights are not pre-cached, the pipeline must handle the download or fail gracefully with `FR-007`.*

## 3. Dataset Strategy

The reproduction relies on the **AndroidWorld** task registry. Since the full Android emulator is too resource-intensive for the 7GB RAM limit, the strategy is to use the **Mock/Headless Interface** provided by `MobileGym`.

*   **Input**: A list of 10 distinct task IDs from the AndroidWorld registry.
*   **Processing**: The agent interacts with the mock environment, generating a sequence of states and actions.
*   **Output**: A `trajectories.jsonl` file containing the full interaction history.
*   **Validation**: Ensure every task ID exists in the registry and that the mock environment can simulate the required states.

**Variable Fit Check**:
*   *Required*: Task ID, State (Screen/Action), Outcome (Success/Fail).
*   *Available*: AndroidWorld provides these via the `interface.py` abstraction.
*   **Simulation Fidelity Validation**: Before full rollout, a small set of tasks will be manually inspected (or compared against gold standards if available) to ensure the mock environment produces valid state transitions. If the mock fails to reproduce basic logic, the pipeline halts with a `SIMULATION_INVALID` error.

## 4. Technical Approach & Methodology

### 4.1 Model Inference (CPU Constraints)
The plan utilizes `transformers` with `torch` CPU support. To fit the 7B parameter model into ~7GB RAM:
*   **Quantization**: Use 4-bit quantization via `bitsandbytes` (CPU enabled) or `torch` native quantization (`int8`/`int4`).
*   **Tiered Fallback**: If 7B quantization exceeds 6.5GB RAM (accounting for `MobileGym` overhead), the plan switches to `Qwen2-VL-2B` (or similar small CPU model) and logs a "DEGRADED_MODE" warning. This is a feasibility test only.
*   **Inference Mode**: Batch size = 1. No parallel inference.

### 4.2 Hierarchical Feedback (HiFPO) Generation
The `curriculum_generator` script processes failed trajectories:
1.  **Error Detection**: Identify steps where the agent deviated from the goal or failed.
2.  **Hint Generation**: Use the vision-language model to generate a textual hint based on the error context.
3.  **Validation (Syntactic Proxy)**: Enforce `FR-005` (length ≥10) AND a keyword heuristic check (presence of actionable verbs like 'tap', 'swipe', 'enter').
4.  **Output**: Structured JSON with `error_type`, `hint_text`, `step_id`.
5.  **Limitation**: The keyword heuristic is a syntactic proxy for quality. Semantic quality cannot be fully validated without human review. The goal is to demonstrate the *mechanism* of feedback generation.

### 4.3 Statistical Rigor (Pass@3)
*   **Metric**: Pass@3 = (Number of tasks solved in ≤3 attempts) / (Total tasks).
*   **Confidence Interval**: 95% CI calculated via **Exact Binomial (Clopper-Pearson)** method.
    *   *Rationale*: Bootstrap resampling on N=10 yields unstable, wide intervals that lack inferential power. The Exact Binomial method is the standard for small-sample binary outcomes, providing a statistically valid (though conservative) range.
    *   *Limitation*: The interval will be wide (e.g., 0.10 to 0.90) reflecting the low power of the pilot run. This is an acknowledged limitation of the pilot study, not a methodological flaw.
*   **Comparison**: Compare against the paper's reported baseline **only as Contextual Observation**. Explicitly state that results are not directly comparable due to environment differences (Mock vs. Real, CPU vs. GPU). The "Discrepancy Alert" is removed from the validation logic.

## 5. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Mock Environment** | Full Android emulation requires >10GB RAM and GPU. Mock mode is the only viable path for CPU-only CI. |
| **4-bit Quantization** | Medium-scale models in FP16 require substantial RAM. Quantized models reduce this to a size fitting the target memory limit. |
| **Tiered Fallback (2B)** | If 7B exceeds RAM, 2B model ensures the pipeline completes, albeit with degraded performance. |
| **Exact Binomial CI** | Standard for small-sample binary outcomes. Provides a statistically valid (though wide) range, unlike unstable bootstrapping on N=10. |
| **Hard Timeout (300s)** | Prevents infinite loops which would block the 6-hour CI job. |

## 6. Assumptions & Gaps

*   **Assumption**: The `MobileForge` codebase includes a functional mock interface for `AndroidWorld`.
*   **Assumption**: `bitsandbytes` CPU wheels are available for the target Python version.
*   **Gap**: If the paper's baseline results are not provided in the repo, the comparison will be against the abstract value, which may lack task-level granularity.
*   **Gap**: The "Annotation-Free" claim is validated by the *generation* of hints (syntactic proxy), not by human evaluation of their quality (due to cost/time constraints).
*   **Gap**: The comparison against the paper's baseline is "Contextual Observation Only" and not a scientific validation of performance superiority.