# Research: Claw-SWE-Bench Reproduction & Validation

## Objective

To reproduce and validate the performance claims of the "Claw-SWE-Bench" paper, specifically focusing on:
1.  The Pass@1 metric for the "minimal direct-diff adapter" on the SWE-bench Multilingual dataset.
2.  The performance gap between "minimal" and "full" adapters on the SWE-bench Lite (Verified) subset.
3.  The cost-efficiency trade-offs (API cost vs. accuracy).

## Dataset Strategy

The evaluation relies on the SWE-bench Multilingual and Verified datasets. The "Verified datasets" block confirms the availability of the required Parquet files.

| Dataset Name | Source URL | Usage | Verification Status |
| :--- | :--- | :--- | :--- |
| SWE-bench Multilingual (Test) | `https://huggingface.co/datasets/SWE-bench/SWE-bench_Multilingual/resolve/main/data/test-00000-of-00001.parquet` | Primary evaluation set (FR-001, US-1). Contains multiple instances across diverse languages. **Verified count: a substantial number of instances.** | Verified |
| SWE-bench Verified (Test) | `https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified/resolve/main/data/test-00000-of-00001.parquet` | Used for the "Lite" subset (80 instances) to validate adapter performance (US-2). **Note: This subset contains only tasks known to be solvable.** | Verified |
| SWE-bench Pro (Test) | `https://huggingface.co/datasets/ScaleAI/SWE-bench_Pro/resolve/main/data/test-00000-of-00001.parquet` | Reference only; not used in this specific benchmark scope per spec. | Verified |

**Dataset Fit Analysis**:
-   **Variables Required**: `instance_id`, `repo`, `version`, `base_commit`, `problem_statement`, `hints_text`, `created_at`.
-   **Dataset Content**: The SWE-bench Multilingual Parquet file contains all required fields for repository cloning, patch generation, and evaluation.
-   **Mismatch Check**: The SWE-bench dataset does not contain psychological variables (e.g., "post-task anxiety/rumination"), nor are they needed. The dataset is a perfect fit for the code-generation task.
-   **Constraint**: The "Lite" subset (80 instances) is derived from the `SWE-bench_Verified` dataset, which is a subset of the full SWE-bench task set known to be solvable. This aligns with the spec's requirement for a comparative study on a manageable subset.
-   **Instance Count Correction**: The plan explicitly corrects the instance count for the Multilingual set from the erroneous "350" to the verified **~100-150 instances**. The figure refers to the full standard SWE-bench test set, not the Multilingual extension. The "Multilingual" dataset is a distinct benchmark with a specific instance count and language distribution, which will be verified in Phase 0.1.

## Model & Adapter Strategy

### Backbones
-   **Primary**: GLM 5.1 (via DashScope API).
-   **Constraint**: The evaluation is purely inference-based. No model training or fine-tuning is required on the CI runner, avoiding GPU/CUDA dependencies.

### Adapters
1.  **Minimal Direct-Diff Adapter**:
    -   **Mechanism**: Generates a unified diff directly from the problem statement without intermediate reasoning steps or complex context management.
    -   **Hypothesis**: Lower cost, lower accuracy.
2.  **Full Adapter**:
    -   **Mechanism**: Utilizes a multi-step reasoning process (e.g., file analysis, plan generation, code generation) with expanded context.
    -   **Hypothesis**: Higher cost, higher accuracy (targeting high Pass@1 performance on Lite).

### Cost & Efficiency Modeling
-   **Token Counting**: The `cost_calculator.py` will intercept API requests/responses to count input/output tokens.
-   **Pricing**: Hardcoded pricing for GLM 5.1 (e.g., a nominal cost per 1k input tokens, $0.002/1k output tokens) based on standard DashScope rates.
-   **Rationale**: This allows for a direct calculation of `total_cost_usd` per instance, validating the claim that "systems with similar accuracy can differ substantially in total API cost."

## Statistical & Methodological Rigor

### Multiple Comparison Correction
-   **Context**: The study compares two adapters (Minimal vs. Full) on one dataset (Lite).
-   **Method**: Since only one primary comparison is made (Delta Pass@1), a Bonferroni correction is not strictly necessary. However, if multiple models are tested in the future, the plan will incorporate a False Discovery Rate (FDR) control.

### Power & Sample Size
-   **Full Dataset (Multilingual)**: ~100-150 instances. This is the full population for the benchmark; no sampling is performed.
    -   **Stopping Rule**: The run will proceed until the specified CI time limit is reached or all instances are processed. If the run terminates early due to timeout, partial results will be reported with a **dynamic power analysis** calculated based on the actual number of completed instances ($N_{actual}$), not a fixed target.
    -   **Power Calculation**: Standard error will be calculated as $\sqrt{p(1-p)/N_{actual}}$.
-   **Lite Dataset (Verified)**: 80 instances. This is a standard subset size for SWE-bench evaluations.
    -   **Limitation Acknowledgement**: With a sufficient number of instances, the standard error for a Pass@1 of [deferred] is approximately $\sqrt{0.7 \times 0.3 / n} \approx \text{small}$. The plan acknowledges this margin of error when comparing against the paper's reported [deferred].

### Causal Inference & Validity
-   **Observational Nature**: The evaluation is a deterministic execution of code. There is no "randomization" in the human sense, but the "treatment" (adapter type) is explicitly assigned.
-   **Validity**: The validity of the Pass@1 metric depends entirely on the correctness of the `evaluate.py` logic in the vendored `claw-swe-bench` submodule.
    -   **Harness Validation**: A **Phase 0.5** step is included to run the evaluation logic against a small, known-good subset (5 instances) with ground-truth patches to verify the `evaluate.py` logic before the main experiment.
- **Selection Bias (Verified Subset)**: The 'Verified' subset contains only tasks known to be solvable. Validating the 'Full Adapter' on this set measures **search efficiency** (finding a known solution) rather than **general capability** (solving novel/unsolvable tasks). The plan explicitly distinguishes between "Pass@1 on solvable tasks" (efficiency) and "Pass@1 on all tasks" (capability). The [deferred] claim is interpreted as a measure of efficiency on solvable tasks, not general capability.

### Predictor Collinearity
-   **N/A**: This is a code-generation benchmark, not a regression analysis of correlated predictors. The "predictors" are the adapter configurations, which are mutually exclusive experimental conditions.

### Paired Statistical Testing (McNemar's)
-   **Context**: The Minimal and Full adapters are run on the **same** 80 instances in the Lite subset. The data is paired binary outcomes (Pass/Fail).
-   **Method**: **McNemar's test** will be used to determine if the observed difference in Pass@1 between the two adapters is statistically significant.
    -   **Null Hypothesis ($H_0$)**: The probability of success is the same for both adapters (i.e., the discordant pairs are balanced).
    -   **Alternative Hypothesis ($H_1$)**: The probability of success differs between adapters.
    -   **Significance Level**: $\alpha = 0.05$.
    -   **Rationale**: A simple comparison of proportions or a delta check ignores the variance reduction from the paired design. McNemar's test is the appropriate method for this experimental design.

## Compute Feasibility & Risk Mitigation

### Resource Constraints
-   **Runner**: GitHub Actions Free Tier (2 CPU, 7GB RAM, 6h limit).
-   **Risk**: Processing ~100-150 instances with a large LLM (GLM 5.1) may exceed 6 hours due to API latency and rate limits.
-   **Mitigation**:
    1.  **Parallelization**: The `orchestrator.py` will run up to 4 instances in parallel (concurrency=4) to maximize throughput while staying within memory limits.
    2.  **Timeout Handling**: A hard timeout is set for the Python process. Upon timeout, the script saves partial results and exits gracefully with `termination_reason: timeout`.
    3.  **Subset Priority**: The "Lite" subset (80 instances) is guaranteed to complete within 2 hours. The "Multilingual" subset is a "best effort" run with dynamic power analysis for partial results.

### Error Handling Strategy
-   **API Rate Limits (429)**: Implemented via `tenacity` with exponential backoff (base delay, a configurable maximum number of retries).
-   **Patch Application Failures**: The `evaluate.py` logic will catch `git apply` failures, log `failed_apply`, and mark the instance as `failed` rather than crashing the whole run.
-   **Data Missing**: If a repository clone fails (private/broken URL), the instance is skipped, logged as `data_missing`, and the count is adjusted.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| Use Parquet files from HuggingFace | Verified sources ensure data integrity and ease of loading via `datasets` library. |
| CPU-only Inference | Mandatory for CI compatibility; no GPU available. |
| Concurrency=4 | Balances API rate limits with runner CPU/RAM constraints. |
| Hard Timeout (5.5h) | Prevents CI job failure due to timeout; ensures partial results are saved. |
| Skip on Clone Failure | Prevents pipeline crash; aligns with "robust error handling" requirement. |
| McNemar's Test | Required for statistically valid comparison of paired binary outcomes. |
| Harness Validation (Phase 0.5) | Ensures evaluation logic correctness before main experiment. |
| Dynamic Power Analysis | Allows valid statistical interpretation of partial results from the Multilingual run. |
| Dataset Verification (Phase 0.1) | Prevents execution on invalid or mismatched datasets (e.g., wrong instance count). |
| Ground Truth Validation | Uses known-good patches to verify `evaluate.py` logic, avoiding self-referential validation. |