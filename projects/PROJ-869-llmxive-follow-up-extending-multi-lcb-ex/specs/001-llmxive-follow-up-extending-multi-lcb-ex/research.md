# Research: llmXive follow-up: extending "Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages"

## Problem Statement

The core hypothesis is that Large Language Models (LLMs) fail to generate correct code in low-resource programming languages (e.g., Rust, Kotlin) not because they lack the algorithmic reasoning capability, but because they struggle with syntax translation and idiom adaptation. By providing a "Partial Logic Trace" (the first 3 algorithmic steps from a successful Python solution) as a few-shot anchor, we aim to scaffold the model's reasoning, enabling it to complete the logic in the target language. 

**Important Scope Note**: This study tests the hypothesis on a **specific subset of difficult tasks** (selected via stochasticity filter). The findings will be framed as **associational improvements** on this subset, not general causal claims for the entire population of code generation tasks, due to the non-randomized, pre-screened design.

## Dataset Strategy

The study relies on the **Multi-LCB** dataset, which extends LiveCodeBench to multiple programming languages. The dataset provides ground-truth solutions in Python and target languages, along with test cases.

### Verified Datasets

| Dataset Name | Source URL | Format | Usage in Study |
| :--- | :--- | :--- | :--- |
| LCB-R (Test) | https://huggingface.co/datasets/huypn16/LCB-R/resolve/main/data/test-00000-of-00013.parquet | Parquet | Primary source for Python ground-truth solutions and problem statements. |
| LCB-R-F (Test) | https://huggingface.co/datasets/huypn16/LCB-R-F/resolve/main/data/test-00000-of-00006.parquet | Parquet | Supplementary test cases for cross-validation. |
| LCB CCP Easy (Train) | https://huggingface.co/datasets/sigcp/lcb_ccp_easy/resolve/main/data/train-00000-of-00001.parquet | Parquet | Used for initial model warm-up or calibration if needed (optional). |

**Dataset Fit Verification**:
-   **Required Variables**: Problem statement, Python ground-truth solution, target language ground-truth solution (for verification), test cases, difficulty level, topic.
-   **Verification**: The LCB-R dataset contains `problem_statement`, `python_solution`, `test_cases`, and `difficulty`. The target language solutions are not strictly required for the *guided* condition (as we generate them), but are useful for baseline validation. The dataset provides sufficient coverage for the "Stochasticity Filter" (re-running blind conditions) and stratification by difficulty/topic.
-   **Constraint Check**: The dataset is in Parquet format, which is efficiently loadable via `pandas` or `datasets` library, fitting within the 7GB RAM constraint when subsetted.

### Data Selection Protocol

1.  **Initial Pool**: Select tasks from LCB-R where the model (in a pre-screening run) failed in the target language (Pass@1 < 1.0) but succeeded in Python.
2.  **Stochasticity Filter**: Re-run the "blind" condition (no anchor) 3 times for each candidate task. Include the task in the final evaluation set **only if** it fails in **≥ 2 of the 3** blind runs. This ensures we are testing on genuinely difficult tasks, not stochastic flukes.
3.  **Attrition Handling**: If the filtered set is < 200, sample replacements from the next available pool (excluding rejected tasks) until the target is reached.
4.  **Stratification**: Ensure the final set of tasks is stratified by Difficulty (Easy/Medium/Hard) and Topic (e.g., DP, Graphs, Math) to avoid bias. No single Topic > 30% of the set.

## Methodology

### Experimental Design

-   **Independent Variable**: Presence of "Partial Logic Trace" (Anchor) in the prompt.
    -   *Blind Condition*: Prompt contains problem statement + previous failed output (context).
    -   *Guided Condition*: Prompt contains problem statement + previous failed output + **Partial Logic Trace** (first 3 steps from Python solution).
-   **Dependent Variable**: Pass@1 (binary: Pass/Fail against test suite).
-   **Control Variables**: Model version, temperature (fixed), random seed, target language, difficulty level.
-   **Statistical Test**: Paired McNemar's test comparing Pass@1 rates of the *same* 200 tasks under Blind vs. Guided conditions.

### Partial Logic Trace Extraction

1.  Parse the ground-truth Python solution into an Abstract Syntax Tree (AST).
2.  Identify the **first 3 critical algorithmic operations** (e.g., variable initialization, loop entry, recursive call). **Heuristic**: Prioritize steps that are complex or likely to be failure points (e.g., nested loops, recursion) rather than simple initialization.
3.  Serialize these steps into a pseudo-code or Python syntax block. **Crucially, do not translate to the target language.** The anchor must remain in Python/pseudo-code to avoid syntax bias.

### Execution & Error Categorization

-   **Sandbox**: Execute generated code in an isolated CPU environment (e.g., `subprocess` with `timeout` or Docker).
-   **Timeout**: Hard limit of 10 seconds per test case to prevent infinite loops (SC-005).
-   **Error Categorization (FR-004)**:
    1.  **Syntax Error**: Compilation fails (log contains "error:", "failed to compile").
    2.  **Library Misuse**: Runtime import error (log contains "ModuleNotFoundError", "ImportError").
    3.  **Runtime Error**: Execution crash/hang (log contains "RuntimeError", "Panic", "Timeout", "Segmentation fault").
    4.  **Logic Transfer Failure**: Execution **Passes** all test cases BUT the generated code fails to implement at least one of the 3 anchor steps **AND** does not use a valid alternative (e.g., a standard library function that encapsulates the logic). **Detection Method**: **Keyword/Control-Flow Matching** (e.g., searching for specific function calls, loop structures, or variable names defined in the anchor). *Note: Structural AST subgraph checks are explicitly rejected per spec FR-004.*

### Statistical Analysis

-   **Baseline**: Record the Pass@1 rate for the 200 tasks under the Blind condition (after stochasticity filtering).
-   **Comparison**: Run the Guided condition on the same set of tasks.
-   **Test**: Perform McNemar's test on the 2x2 contingency table (Blind Pass/Fail vs. Guided Pass/Fail).
-   **Significance**: Report p-value. If p < 0.05, the improvement is statistically significant.
-   **Regression to the Mean**: Acknowledge that the stochasticity filter may artificially depress the baseline. Use **bootstrap resampling** to estimate confidence intervals and quantify the uncertainty introduced by the selection process.

## Compute Feasibility & Constraints

-   **Hardware**: GitHub Actions free-tier (standard CPU, moderate RAM, 14GB disk, no GPU).
-   **Model**: Use a **CPU-quantized 1.1B parameter model** (e.g., TinyLlama-1.1B-Chat-GGUF `q4_0`) via `llama-cpp-python`. This avoids the forbidden `bitsandbytes` (CUDA) and fits within RAM. **A 7B model is rejected** as it would require 13-26 hours, violating the 6h constraint.
-   **Runtime**: Total pipeline (200 tasks × 4 runs) must complete in ≤ 6 hours.
    -   *Strategy*: Parallelize independent tasks (e.g., 2 concurrent workers).
    -   *Optimization*: Use a smaller context window if possible. Skip tasks where the anchor extraction fails.
    -   *Fallback*: If the base model fails to generate valid code, switch to a larger model with a reduced task set (50 tasks).
-   **Memory**: Subset the dataset to only the selected tasks before loading into memory. Use streaming for large files if necessary.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use `llama-cpp-python` with GGUF (1.1B)** | Complies with "Assumption about compute" (standard CPU quantization). Avoids `bitsandbytes` which requires CUDA. Fits GB RAM and 6h runtime. The larger model is rejected due to runtime constraints. |
| **Keyword/Control-Flow Matching for Logic Transfer** | Explicitly mandated by spec FR-004. Structural AST checks are more complex and not authorized. Includes "Valid Alternative Check" to avoid tautology. |
| **Stochasticity Filter (≥2/3 failures)** | Required by spec FR-006.2 to ensure we are testing on genuinely difficult tasks, not noise. |
| **Paired McNemar's Test** | Required by spec FR-005 and Constitution Principle VII. Unpaired tests are invalid for this design. |
| **10s Timeout per Test Case** | Required by spec FR-003 to prevent runner exhaustion (SC-004). |
| **Stratified Sampling (Topic ≤ 30%)** | Required by spec FR-006.3 to ensure diverse algorithmic coverage. |
| **Associational Claims** | The study design (pre-screened subset) limits claims to the specific subset, not general causality. |
