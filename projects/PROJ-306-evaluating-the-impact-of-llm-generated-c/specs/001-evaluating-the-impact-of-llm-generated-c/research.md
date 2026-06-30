# Research: Evaluating the Impact of LLM-Generated Code on Code Coverage

## 1. Problem Formulation

The core research question is: *How does code coverage differ between LLM-generated code and human-written code for equivalent programming tasks, and which code structures or problem types exhibit the largest coverage gaps?*

This study treats coverage differences as **associational** findings (FR-010). It does not claim that LLMs *cause* lower coverage, but rather observes the statistical relationship between the generation source (LLM vs. Human) and the resulting test coverage metrics.

**Critical Reframing**: We acknowledge that in benchmark suites like MBPP and HumanEval, the "coverage gap" is often a proxy for the "test failure rate" (pass@1). If a solution fails a test, coverage drops. Therefore, this analysis focuses on **granular failure** (how much code is missed) and **partial coverage** events, rather than treating coverage as a purely continuous metric. Where data is discrete ([deferred] or [deferred]), we will use Generalized Linear Mixed Models (GLMM) with appropriate families (Binomial/Beta-Binomial) rather than assuming a continuous normal distribution.

## 2. Dataset Strategy

### 2.1 Primary Benchmarks
The study utilizes two standard programming benchmarks:
1.  **MBPP (Mostly Basic Python Problems)**: A dataset of 974 hand-written Python programming problems.
2.  **HumanEval**: A dataset of 164 hand-written programming problems designed to evaluate code generation.

**Dataset Verification Status**:
Per the "Verified datasets" block provided for this project:
-   **MBPP**: NO verified source found.
-   **HumanEval**: NO verified source found.
-   **LLM**: NO verified source found.

**Implementation Strategy**:
Since no verified URLs are available in the provided list, the pipeline will attempt to load these datasets using the standard `datasets` library loaders (e.g., `datasets.load_dataset("mbpp")` and `datasets.load_dataset("google-research-datasets/human_eval")`).
-   If the loader succeeds, the data is cached locally in `data/benchmarks/`.
-   If the loader fails, the pipeline will log a `WARNING`, exclude the task, and update the `exclusion_rate` metric (FR-014).
-   **Critical Note**: No fabricated URLs will be used. If the canonical loaders fail, the study proceeds with whatever subset of tasks is successfully retrieved.
-   **Gate Constraint**: Per Constitution Principle II, this project is currently in a **GATE BLOCKED** state for "research_accepted" status. The pipeline will run in "sandbox mode" to generate data, but no research conclusions can be officially accepted until the Reference-Validator Agent verifies the dataset sources.

### 2.2 Variable Fit Analysis
The study requires the following variables for each task:
-   `task_id`: Unique identifier.
-   `prompt`: The natural language description of the task.
-   `human_solution`: The reference Python code (used as the baseline).
-   `test_suite`: The list of assertions to validate correctness.

**Fit Check & Transformation**:
-   **MBPP**: Contains `prompt`, `test_list` (string of assertions), and `code`. **Fits after transformation**.
-   **HumanEval**: Contains `prompt`, `canonical_solution`, and `test` (string). **Fits after transformation**.
-   **Gap Handling**: FR-009 mandates that if a task lacks a test suite, it is excluded.
-   **Transformation Step**: The pipeline includes a `test_transformer.py` module that parses the `test_list` string into a valid `.py` file with `assert` statements, saved to `data/benchmarks/processed/`. This ensures `pytest-cov` has a runnable file.

## 3. Methodology

### 3.1 Code Generation (FR-002)
-   **Primary Model**: `gpt-4` (via OpenAI API) if `LLM_API_KEY` is provided.
-   **Fallback Model**: `microsoft/phi-2` (2.7B) or `google/gemma-2b-it` (2B) loaded in **4-bit quantization** (`load_in_4bit=True`) via `bitsandbytes` on CPU.
    -   *Rationale*: `starcoderbase-3b` (FP32/FP16) exceeds the 7GB RAM limit. Phi-2 and Gemma-2B in 4-bit quantization fit comfortably within 7GB RAM on a 2-CPU runner.
    -   *Constraint*: The pipeline must retry the Primary Model with a limited number of attempts using exponential backoff. before switching to Fallback. If Fallback is used, results are stratified by model type.
-   **Temperature**: 0.7 (fixed for reproducibility).
-   **Timeout**: **120 seconds** per generation (increased from 60s to account for CPU inference latency).
-   **Streaming**: Generation uses streaming to handle long outputs and prevent truncation.

### 3.2 Coverage Measurement (FR-003, FR-012)
-   **Tool**: `pytest-cov` (v4.0+).
-   **Metrics**:
    -   `line_coverage`: Percentage of executable lines executed.
    -   `branch_coverage`: Percentage of branches taken.
    -   **Exception**: For HumanEval, which often lacks explicit branch tests, `branch_coverage` is reported as `N/A` (FR-009).
-   **Execution**: Each generated solution is run in an isolated `subprocess` to prevent state leakage.
-   **Error Handling**: Syntax errors or runtime crashes are logged, and the task is marked `run_status=failure`. No coverage is calculated for failed runs.

### 3.3 Statistical Analysis (FR-005, FR-016, & New Methodology)
-   **Pairing**: Tasks are paired by `task_id` (LLM solution vs. Human solution).
-   **Model Selection**:
    1.  **Distribution Check**: First, check the distribution of coverage values. If the data is dominated by discrete values (0, 1), proceed to **GLMM**. If continuous, proceed to **LMM**.
    2.  **Linear Mixed-Effects Model (LMM)**: `Coverage ~ Model_Type + Difficulty + (1 | Benchmark) + (1 | Task_ID)`.
        -   `Model_Type`: Fixed effect (GPT-4 vs. StarCoder).
        -   `Benchmark`: Random intercept (MBPP vs. HumanEval) to account for clustering.
        -   `Task_ID`: Random intercept to handle pairing.
    3.  **Generalized Linear Mixed Model (GLMM)**: If data is binary/discrete, use `Binomial` family with `logit` link.
        -   `Outcome`: `Pass/Partial_Fail` (derived from coverage > 0.95).
-   **Effect Size**:
    -   For LMM: **Marginal Means Difference** with 95% Confidence Intervals.
    -   For GLMM: **Odds Ratio** with 95% Confidence Intervals.
    -   *Note*: Cohen's d is **removed** as it is inappropriate for discrete/bounded data.
-   **Multiple Comparisons**: If subgroup tests are performed, **Holm-Bonferroni** correction is applied (FR-006).
-   **Collinearity**: If a multi-variable regression is attempted, VIF is calculated (FR-013).

### 3.4 Stratification & Sensitivity (FR-007, FR-011)
-   **Stratification Dimensions**:
    1.  `difficulty` (Easy, Medium, Hard).
    2.  `code_patterns` (Loops, Conditionals, Recursion).
    3.  `boundary_cases` (Presence of edge-case tests).
-   **Sensitivity Analysis**: Replaced "sign flip" check with **Bootstrap Resampling**.
    -   The pipeline will resample tasks (1000 iterations) to generate a **95% Confidence Interval** for the coverage gap effect size and p-value.
    -   This assesses the stability of the results against subsampling, providing a robust measure of uncertainty.

## 4. Compute Feasibility (Free-Tier Constraints)

-   **Memory**: The pipeline loads datasets into memory. MBPP (a dataset of moderate size) and HumanEval (~MB) are negligible. The fallback model (Phi/Gemma-2B in 4-bit) requires ~2-3GB RAM, leaving ample headroom for the Python runtime and `pytest` execution within the 7GB limit.
- **Time**: A large number of tasks * (120s generation + 5s execution) = [deferred]. A defined time limit is safe..
-   **Disk**: Generated code and reports are small (<100MB).

## 5. Risk Mitigation

| Risk | Mitigation Strategy |
| :--- | :--- |
| **Dataset Unavailability** | If loaders fail, the pipeline logs the error, reports `exclusion_rate=100%` for that dataset, and proceeds with any other available data. Project remains in sandbox mode. |
| **API Rate Limits** | Exponential backoff (increasing intervals) with 3 retries. If all fail, task marked `generation_failed`. |
| **Memory Overflow** | Monitor `psutil`. If RAM > 6.5GB, unload model and retry with smaller batch or skip non-critical tasks. |
| **Syntax Errors** | `try/except` blocks in `coverage_runner.py` to catch `SyntaxError` and log the file without crashing the pipeline. |
| **Discrete Data Distribution** | If coverage is binary, switch from LMM to GLMM (Binomial) to ensure statistical validity. |
