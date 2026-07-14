# Research: llmXive follow-up: extending "AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Age"

## 1. Research Question & Hypothesis

**Primary Question**: Does a Dual-Track Agent Architecture (SLM generator + deterministic constraint store) significantly reduce *initial* constraint violation rates compared to a Monolithic Baseline as the number of progressive constraints increases (≥5)?

**Hypothesis**: The Dual-Track architecture will exhibit a statistically significant interaction effect where *initial* violation rates remain stable or decrease slightly as constraint count increases, whereas the Monolithic baseline will show a sharp increase in violations.

**Statistical Formulation**:
- $H_0$: There is no interaction between `architecture_type` and `constraint_count` on `initial_violation_rate`.
- $H_1$: There is a significant interaction ($\beta_{interaction} \neq 0$) in the GLMM, such that the slope of violation rate vs. constraint count differs by architecture.

## 2. Dataset Strategy

### 2.1 Primary Dataset: AdaPlanBench
- **Description**: A benchmark of household tasks designed to evaluate adaptive planning. The dataset includes tasks with progressive constraint reveals.
- **Source Status**: **Verified Source**. The implementation will load the dataset from the HuggingFace Hub using the ID `adaplanbench/adaplanbench`.
- **Blocking Condition**: If the dataset cannot be fetched or lacks the specific `progressive_constraints` field (a time-ordered sequence of reveals), the project **cannot proceed**. The hypothesis relies on the "progressive" nature of constraints. If the dataset only contains static constraints, the independent variable (constraint count) does not represent "progressive accumulation," and the project will halt with a "Data Incompatibility" error.
- **Variable Fit Check**: The dataset MUST contain:
  - `task_prompt`: The initial instruction.
  - `constraints`: A list or sequence of constraints revealed progressively (time-ordered).
  - `ground_truth_solution`: For scoring.

### 2.2 Auxiliary Resources
- **SLM Model**: The plan uses `microsoft/phi-3-mini-4k-instruct` from the HuggingFace Model Hub. This is a standard model weight download, not a dataset. The model is selected for its CPU feasibility (< 4GB RAM).
- **GLMM Reference**: The analysis relies on the `statsmodels` library for GLMM fitting. No external "GLMM reference datasets" are used.

**Decision**: The project relies entirely on the AdaPlanBench dataset. If the "Verified datasets" block does not provide a valid URL or ID for AdaPlanBench, the implementation must include a robust error handling path that halts execution and reports the missing data source as a blocking issue.

## 3. Methodological Approach

### 3.1 Data Filtering (FR-001)
- **Logic**: Load the full dataset. Iterate through tasks. Count the number of constraints in the `constraints` field.
- **Filter**: Keep only tasks where `len(constraints) >= 5`.
- **Distribution Verification**: Before proceeding, generate a descriptive report of the `constraint_count` distribution in the filtered subset. If the variance is too low (e.g., all tasks have exactly 5 constraints), the plan will note the limitation in statistical power.
- **Output**: A subset dataframe with a new column `constraint_count` (integer).

### 3.2 Agent Execution (FR-002, FR-003, FR-004)
- **Execution Order**:
  1. **SLM Generation**: The SLM generates a plan step.
  2. **Independent Oracle Evaluation**: An *Independent Oracle* (a separate, deterministic logic block) evaluates the **raw SLM output** immediately, *before* any correction is applied. It logs `initial_violation` (True/False). The Oracle's logic is based on a human-validated subset of constraints and explicit pattern matching, ensuring independence from the Resolver's intervention logic.
  3. **Resolver Intervention**: If the `initial_violation` is True, the **Resolver** module (part of the Dual-Track architecture) checks the action against the `Constraint Store`.
     - **Detection Logic (FR-007)**: Exact string match, case-insensitive substring, explicit negation patterns.
     - **Implicit Handling (FR-009)**: If a constraint is implicit or pattern fails, log as "implicit_unverified" and exclude from primary violation calculation.
     - **False Negative Handling (FR-008)**: If the Resolver fails to parse intent, log "false_negative", retain original plan, increment counter.
  4. **Correction**: If a violation is detected, the Resolver forces a revision. The final output is logged as `final_adherence`.
- **Monolithic Baseline**:
  - Prompt: `Task: {task_prompt}. Constraints: {all_constraints}. Plan:`
  - Execution: Generate plan. The *Independent Oracle* evaluates the raw output for `initial_violation`. No Resolver intervention occurs.

### 3.3 Statistical Analysis (FR-005, FR-011)
- **Model**: Generalized Linear Mixed Model (GLMM) with binomial link.
- **Formula**: `initial_violation ~ architecture * constraint_count + seed_id + (1 | task_id) + (1 | seed_id)`
  - `initial_violation`: Binary (0/1) outcome from the Independent Oracle (pre-correction).
  - `architecture`: Categorical (Dual-Track, Monolithic).
  - `constraint_count`: Continuous or Ordinal (levels 5, 6, 7+).
  - `seed_id`: Fixed effect covariate (to account for seed variance without singular fit).
  - `(1 | task_id)`: Random intercept for task-specific difficulty.
  - `(1 | seed_id)`: Random intercept for seed-specific variance.
- **Power Analysis (FR-011)**:
  - Before full execution, run a power analysis on the filtered subset size.
  - Target: Detect effect size $f^ \ge 0.15$ with power $\ge 0.80$.
  - If power is insufficient, the plan will note the limitation in the results (acknowledging the limitation rather than claiming significance).

### 3.4 Human Validation (FR-010)
- **Stratified Sampling**: Randomly sample 100 tasks from the filtered subset, stratified by `constraint_count` and `initial_violation` status to ensure representation of different error types.
- **Manual Annotation**: Human annotators label violations.
- **Precision Calculation**: Calculate the agreement rate (Cohen's Kappa) between the Rule-Based Module and Human Ground Truth. The sample size is determined to achieve a margin of error $\le 10\%$ for the Kappa estimate, given the expected prevalence of violations.

## 4. Compute Feasibility & Resource Constraints

- **Environment**: GitHub Actions Free Tier (2 vCPU, 7GB RAM).
- **Model Selection**:
  - **No GPU**: All inference must run on CPU.
  - **Model Size**: Must be < 4GB RAM for the model weights + 2GB for context + OS overhead.
  - **Candidate**: `microsoft/phi-3-mini-4k-instruct` (approx. 2-3GB in FP16/FP32) or `SmolLM2-135M` (very small, fast).
  - **Quantization**: **NO** 8-bit/4-bit quantization requiring `bitsandbytes` (CUDA). Use standard `float32` or `float16` if available in CPU wheels.
- **Data Subset**: The filtered dataset (≥5 constraints) will likely be small (< 100 tasks). Processing this on CPU is feasible.
- **Time Limit**: Execution must complete within 6 hours.
  - **Strategy**: Process tasks in batches. If a single task takes > 5 minutes, log timeout and skip (or retry once).

## 5. Risk Assessment

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Missing** | Fatal | If AdaPlanBench cannot be fetched (no verified URL), the project halts. The plan explicitly states this dependency. |
| **Model OOM** | High | Use a smaller model (e.g., 135M or 1.5B parameters) if 3B+ fails. Monitor RAM usage (FR-006). |
| **GLMM Non-Convergence** | Medium | If the model fails to converge, report the failure and use a simpler fixed-effects logistic regression as a fallback (with caveats). |
| **Rule-Based False Negatives** | Medium | The "implicit_unverified" logging (FR-009) and human validation (FR-010) are designed to quantify this error. |
| **Static Constraints** | Fatal | If the dataset lacks progressive constraints, the hypothesis is invalid. The plan halts immediately. |