# Research: llmXive follow-up: extending "EvoPolicyGym"

## 1. Research Question & Hypothesis

**Question**: Does providing counterfactual failure explanations (vs. scalar rewards) improve the generalization of evolved policies to dynamic environmental shifts?

**Hypothesis**: Policies evolved with counterfactual feedback will retain a higher percentage of their pre-shift performance on dynamic-shift environments compared to policies evolved with scalar rewards, controlling for code complexity.

## 2. Dataset Strategy

### Verified Datasets
The study relies on the **EvoPolicyGym** suite, which is programmatically accessible via the `gymnasium` library (or a local fork if the specific 16 environments are not yet on HF).
- **Source**: https://github.com/Farama-Foundation/Gymnasium
- **Verification**: The implementation will attempt to load these via `gymnasium.make()` or a local registry.
- **Fallback Protocol**: If the specific 16 environments are not available on a public registry, the study **does not** generate synthetic environments. Instead, it proceeds with the **available subset** (e.g., 4 environments) and explicitly acknowledges the reduced scope in the final report. No synthetic data is used to replace the required dataset, as synthetic environments may not possess the structural complexity required to test the hypothesis (violating the study's validity).
- **Data Loading**: Data is generated on-the-fly during the evolutionary runs (trajectories), not downloaded as a static dataset. The "dataset" is the collection of trajectories and evolved policies.

**Note**: No external static dataset (e.g., UCI, HF) is required. The "data" is the output of the simulation.

## 3. Methodological Rigor

### 3.1. Dynamic Shift Validation (FR-001)
- **Mechanism**: A `DynamicShiftEnvironment` wrapper modifies the underlying environment's reward function or transition probabilities at `step = total_budget * 0.5`.
- **Independence**: The shift configuration is injected via a wrapper that modifies the environment's internal state *after* the step count. Crucially, the shift parameters are **not exposed** to the agent's observation space or reward function prior to the shift step, ensuring the agent cannot "memorize" the shift.
- **Verification**: A static agent (non-adaptive) is run on the dynamic environment. A statistically significant drop (p < 0.05, one-tailed) in post-shift performance vs. pre-shift performance confirms the shift is impactful (US-1).
- **Constraint**: The shift threshold (50%) is fixed per spec, but a sensitivity analysis will sweep [deferred]-60% to ensure robustness. The content of the shift is also varied to include changes to reward structure and transition dynamics.

### 3.2. Counterfactual Generation (FR-002)
- **Model**: A lightweight, 4-bit quantized LLM.
  - **Primary**: `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (revision `main`, quantized via `bitsandbytes` 4-bit).
  - **Fallback 1**: `Phi-3-mini-4k-instruct` (4-bit quantized) if Primary fails (OOM/network).
  - **Fallback 2**: Deterministic `TemplateExplanation` if both LLMs fail.
- **Input**: Trajectory logs (state, action, reward, terminated) + Ground Truth Rule Schema.
- **Output**: Natural language text explicitly stating the violated rule (identified by a unique Rule ID from the environment's JSON schema) and the counterfactual action that would have succeeded.
- **Masking & Validity**: The "correct action" is **masked** from the agent's training signal. The agent receives only the natural language explanation. The "correct action" is used *internally* by the system for validation (SC-002) and to verify the LLM's reasoning, but not as a direct input to the policy's reward function. This prevents circularity where the agent memorizes the rule rather than learning a generalizable strategy.
- **Validation**: Output is validated against a JSON schema to ensure `Rule_ID` is present and matches a known rule. Explanations are filtered based on a minimum semantic similarity score to ensure fidelity.
- **Fallback**: If the LLM times out (>30s) or fails, the system generates a `TemplateExplanation` (text) using a deterministic template: "You failed because [Rule_ID] was violated. The environment requires [correct_action]." **Crucially, the fallback returns text, not a scalar reward**, satisfying US-2.

### 3.3. Statistical Analysis (FR-005)
- **Model**: Linear Mixed-Effects Model (LMM) with `generalization_score` as the dependent variable.
- **Fixed Effects**: `condition` (baseline vs. counterfactual), `complexity` (cyclomatic complexity).
- **Random Effects**: `(1 | seed)` to account for nested runs within seeds.
- **Hypothesis Test**: One-tailed t-test on the `condition` coefficient. Significance threshold: α = 0.05 (one-tailed).
- **Power**: Acknowledging the CPU constraint, the study will run a minimum of 5 seeds per condition. The power limitation will be explicitly stated in the final report. Power analysis (based on an effect size of 0.5) indicates that N=20 runs per condition across 4 environments achieves [deferred] power (target: ≥0.80).
- **Collinearity**: `complexity` is treated as a control variable. If `complexity` is highly correlated with `condition`, the model will report the correlation and interpret the `condition` effect with caution. `fallback_rate` (proportion of runs using the template explanation) is also included as a covariate to account for the potential bias introduced by the fallback mechanism.

## 4. Compute Feasibility

- **CPU-First**: The LLM is run in 4-bit quantization on CPU. If this exceeds RAM limits, the plan falls back to a smaller subset of the trajectory or a simpler rule-based generator (template-only) for the "counterfactual" condition, clearly noting the deviation.
- **GPU Escape Hatch**: If the CPU run fails due to memory, the execution layer will auto-offload the LLM inference step to a Kaggle GPU kernel (scaled to 16GB VRAM) using a 4-bit quantized model. The rest of the pipeline (evolution, analysis) remains on CPU.
- **Data Streaming**: Trajectories are streamed and processed incrementally to avoid loading full episode logs into memory.

## 5. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **4-bit Quantized LLM** | Required for CPU tractability while maintaining natural language output. Full precision is infeasible on constrained memory resources. |
| **Template Fallback (Text)** | US-2 mandates natural language. Returning a scalar reward would violate the core hypothesis (counterfactuals vs. scalar). |
| **Mixed-Effects Model** | Necessary to handle nested data (seeds) and control for complexity, as required by FR-005. |
| **5 Seeds per Condition** | A pragmatic minimum given CPU constraints. The study acknowledges low power but relies on effect size and confidence intervals. |
| **Pilot Scope (4 envs)** | Full multi-env run exceeds 6h/7GB CPU limit. Synthetic data violates "Data Hygiene"; skipping the study is not an option. |