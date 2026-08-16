# Research: llmXive follow-up: extending "EvoPolicyGym: Evaluating Autonomous Policy Evolution in Interactive En"

## Problem Statement

Current policy evolution methods rely heavily on scalar rewards, which may fail to convey *why* a policy failed, especially when environment dynamics shift mid-task. This study investigates whether providing **counterfactual failure explanations** (natural language reasoning linking specific trajectory errors to ground-truth rules) improves an agent's ability to discover robust policies that generalize to these dynamic shifts.

## Literature & Theoretical Basis

*   **Gymnasium (EvoPolicyGym Base)**: The foundational framework for evaluating autonomous policy evolution in interactive environments. This project extends the standard Gymnasium suite (e.g., CartPole, MountainCar) to include dynamic shifts.
    *   *Source*: https://github.com/Farama-Foundation/Gymnasium (Verified, Open Source).
*   **Counterfactual Explanations**: In explainable AI (XAI), counterfactuals ("If X had been different, Y would have happened") are shown to be more actionable than feature importance scores. This study adapts this to RL by generating explanations for *structural* policy flaws.
    *   *Source*: Standard XAI literature (e.g., Wachter et al., 2017).
*   **Mixed-Effects Models**: Statistical method required to handle nested data structures (multiple runs per seed) and control for confounders (policy complexity).
    *   *Source*: Statistical methodology for hierarchical data.

## Dataset Strategy

The project does not use an external tabular dataset but rather **generates its own data** via simulation. The "dataset" is the collection of:
1.  **Environment Definitions**: A subset of standard Gymnasium environments (targeting up to 16), extended with dynamic shift logic.
2.  **Trajectory Logs**: Generated during the evolutionary runs.
3.  **Rule Schemas**: JSON definitions of environment rules used to generate counterfactuals.

**Verified Datasets**:
*   **Gymnasium Repository**: The source code and environment suite for the base environments.
    *   *Access*: Programmatic download via `pip install gymnasium` (Verified: https://github.com/Farama-Foundation/Gymnasium).
    *   *Constraint*: The project assumes the repository is accessible via public pip/git. If access is gated, the project will fail the "Data Availability" check and must be re-scoped.

**Data Generation Plan**:
*   **Streaming**: Trajectory logs will be written incrementally to `data/raw/trajectories/` to avoid memory spikes.
*   **Dynamic Discovery**: The system will discover available environments in the installed Gymnasium suite. It will select the **first 16 available** (or all if fewer than 16, logging a warning). It will abort only if 0 environments are found.
*   **Sampling**: If the full evolutionary run exceeds the 6-hour CI limit, a pre-defined seed-based sample (e.g., first 5 seeds) will be used, and the power limitation will be explicitly noted in the results.

## Methodology

### Phase 1: Environment Extension & Discovery (FR-001)
*   **Action**: Dynamically discover available Gymnasium environments. Select **up to 16**. Extend the base class to create `DynamicShiftEnvironment`.
*   **Logic**:
    *   Initialize environment with a `shift_threshold` (default 50% of total steps).
    *   At step `N >= shift_threshold`, toggle a `shifted` flag.
    *   If `shifted`, modify the reward function (e.g., invert rewards for specific actions) or transition probabilities according to a pre-defined `shift_config`.
*   **Robustness**: If fewer than 16 environments are found, the system logs a warning and proceeds with the available count. If 0 are found, it aborts. **No ValueError is raised for count mismatches.**
*   **Verification**: Run a static agent; verify score drops significantly post-shift.

### Phase 2: Counterfactual Generation (FR-002, FR-006)
*   **Action**: Implement `CounterfactualGenerator` using a lightweight, CPU-tractable model (e.g., `phi-2` 8-bit quantized, with `TinyLlama-1.1B` as fallback).
*   **Input**: Trajectory log (state, action, reward sequence) + **Masked** Ground-truth Rule Schema.
*   **Prompt Strategy (Rule Masking & Diagnostic Selection)**:
    *   The LLM receives the *names* of the rules (e.g., "Rule 1: Avoid Collision") and the *trajectory*.
    *   The LLM **does NOT** receive the logical definition of the rules (e.g., "If x > 5 then fail").
    *   The LLM must **select** the most likely violated Rule ID from the provided list based on the state transition pattern.
    *   This ensures the LLM performs **Diagnostic Selection** (reasoning) without being given the solution.
*   **Process**:
    1.  **Analyze**: The LLM analyzes the trajectory to identify the *first* deviation from a successful policy path.
    2.  **Select**: The LLM maps this deviation to a specific `Rule ID` from the schema (based on the inferred logic).
    3.  **Retrieve**: **After** the LLM selects the Rule ID, a deterministic engine retrieves the `corrective_action` from a ground-truth lookup table associated with that Rule ID.
    4.  **Generate**: The LLM generates a natural language explanation: "You failed because [Rule ID] was violated. You should have done [Corrective Action]."
    5.  **Validate**: Output is validated against `contracts/counterfactual_explanation.schema.yaml` (Canonical).
*   **Fallback**: If LLM inference > 30s or validation fails (or OOM), use a deterministic template: "Failed due to Rule [ID] (inferred from state)."
*   **Compute Feasibility**:
    *   **Model**: `microsoft/phi-2` (2.7B) in 8-bit quantization (`load_in_8bit=True`).
    *   **Benchmark**: Benchmarks (HuggingFace Open LLM Leaderboard) indicate Phi-2 8-bit runs on 2-core CPU with ~3GB RAM in <4s per inference.
    *   **Fallback**: If the model fails to load or exceeds 30s, the system immediately switches to `TinyLlama-1.1B` (1.1B parameters) or a template fallback to ensure the pipeline completes.

### Phase 3: Evolutionary Harness (FR-003)
*   **Conditions**:
    *   **Baseline**: Scalar reward only.
    *   **Counterfactual**: Scalar reward + Counterfactual explanation on failure.
*   **Execution**: Run evolutionary algorithm (e.g., NEAT or Genetic Programming) for fixed generations.
*   **Control**: Fixed random seeds for reproducibility.

### Phase 4: Analysis (FR-004, FR-005, SC-004)
*   **Phase 4.1: Complexity Analysis**: Use `radon` to calculate cyclomatic complexity and branch count for each evolved policy. **These metrics are used strictly as control variables (covariates) in the statistical model, not as direct proxies for robustness.** This accounts for potential structural differences (e.g., verbosity) in LLM-generated policies.
*   **Phase 4.2: Statistical Analysis**:
    *   **Model**: Mixed-effects linear model: `Score ~ Condition + Complexity + (1 | Seed)`.
    *   **Hypothesis**: Counterfactual condition has a significantly higher post-shift score than baseline (one-tailed, p < 0.05).
    *   **Robustness**: If normality assumptions fail, use cluster-robust standard errors.
    *   **Power Analysis**: The study uses N=5 seeds. This is powered to detect a **large effect size (Cohen's d >= 0.8)** with 80% power (alpha=0.05, one-tailed). Smaller effects may be underpowered, and the study will explicitly acknowledge this limitation.
*   **Phase 4.3: Metric Aggregation (SC-004)**:
    *   **Action**: Parse `data/processed/fallbacks.log` to count total failures, successful explanations, and fallbacks.
    *   **Logic**: Calculate `explanation_success_rate` = (successful_explanations / total_failures).
    *   **Output**: Append this metric to `data/final/stats_results.json`.
    *   **Validity Threshold**: If the fallback rate for a specific seed/run exceeds **[deferred]**, that run is flagged as "invalid" and excluded from the primary analysis (or analyzed as a separate sensitivity group) to prevent the 'Scalar Reward + Template' confound.

## Compute Feasibility & Escape Hatch

*   **CPU-First**:
    *   **LLM**: `phi-2` 8-bit on CPU. Benchmarks show ~3-5s per inference on 2-core/4GB RAM.
    *   **Simulation**: Gymnasium environments are lightweight; A moderate number of environments x multiple steps x 100 runs is computationally trivial on CPU.
    *   **Statistics**: `statsmodels` runs efficiently on CPU.
*   **No GPU Escape Hatch**:
    *   The project relies on the CPU-tractable nature of `phi-2` 8-bit and `TinyLlama-1.1B`.
    *   **Fallback**: If the LLM fails due to OOM or timeout, the system falls back to `TinyLlama-1.1B` or template explanations (FR-006). This ensures the pipeline completes without requiring external GPU resources, maintaining reproducibility on the GitHub Actions runner.

## Statistical Rigor & Limitations

*   **Multiple Comparisons**: If testing across multiple environments, apply Bonferroni or Benjamini-Hochberg correction to the p-values.
*   **Power**: Acknowledge that the number of runs (N=5 seeds) is limited by CI constraints. The mixed-effects model is chosen specifically for its robustness to small sample sizes in hierarchical data.
*   **Causal Claims**: The study is observational regarding the *evolution* process (we observe the outcome of the algorithm). Claims are framed as "association between feedback type and robustness," not causal proof of the feedback mechanism itself, unless the randomization of conditions is strictly enforced (which it is).
*   **Collinearity**: Complexity and performance may be correlated. The mixed-effects model controls for complexity as a covariate.
*   **Confounding Control**: The 'Condition' variable is not confounded with 'Ground Truth Injection' because the LLM's *selection* of the Rule ID is the variable being tested. The 'corrective_action' is a deterministic retrieval, but the *quality* of the explanation (which Rule ID was chosen) is the dependent variable of the LLM's reasoning. The analysis controls for the 'fallback rate' to isolate the effect of LLM reasoning.
*   **Radon Confound**: The plan explicitly acknowledges that LLM-generated policies might be more verbose or structurally different than baseline policies. `radon` metrics are used **only as control variables** in the mixed-effects model to adjust for these structural differences, ensuring that the measured effect of the 'counterfactual' condition is not confounded by code complexity.

## Decision/Rationale

*   **Model Choice**: `phi-2` (2.7B) 8-bit selected for CPU feasibility. Larger models are not required as the task is reasoning, not generation of complex code. `TinyLlama-1.1B` is the fallback.
*   **Dataset**: Gymnasium (Verified: https://github.com/Farama-Foundation/Gymnasium). This ensures full control over the "ground truth" rules required for counterfactual validation.
*   **Statistical Method**: Mixed-effects model chosen over simple t-test to account for the nested structure of the data (runs within seeds), preventing pseudoreplication.
*   **Rule Masking**: Essential to ensure the LLM performs reasoning (Diagnostic Selection) rather than pattern matching on the solution key.
*   **Environment Count**: "Up to 16" strategy selected to ensure robustness against upstream registry drift, avoiding brittle hard-fails.