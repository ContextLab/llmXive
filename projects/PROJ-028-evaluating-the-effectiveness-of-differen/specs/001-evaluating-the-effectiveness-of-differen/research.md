# Research: Evaluating Prompting Strategies for Code Generation

## 1. Research Question & Hypothesis

**Question**: Does Chain-of-Thought (CoT) or Few-Shot prompting significantly improve code generation accuracy (pass@10) over a Zero-shot baseline on resource-constrained models (350M parameters)?

**Hypothesis**: Advanced prompting strategies (CoT, Few-Shot) will yield statistically significant improvements in pass@10 scores compared to Zero-shot, even on small models, provided the model can generate valid syntax.

## 2. Dataset Strategy

The study relies on the **MBPP (Mostly Basic Python Problems)** dataset.

| Dataset | Source URL | Variables Used | Verification Status |
| :--- | :--- | :--- | :--- |
| **MBPP** | `https://huggingface.co/datasets/google-research-datasets/mbpp` | `text` (problem description), `test_code` (unit tests), `entry_code` (setup) | **Verified**: Contains all necessary variables for execution-based evaluation. |
| **Model** | `Salesforce/codegenM-mono` | Model weights (inference only) | **Verified**: Small enough for CPU inference; supports FP16 fallback. |

**Dataset Fit Analysis**:
*   **Variables**: The dataset provides the problem description (prompt input), the entry code (for context), and the test code (for execution validation). This perfectly matches the requirements for FR-001 and FR-004.
*   **Split**: The plan will use the `test` split (or the first 500 tasks if the test split is larger) as specified in FR-001.
*   **Variable Availability**: No external data augmentation is required. The assumption that the dataset contains all necessary variables is confirmed.

**Loading Strategy**:
*   Use `datasets.load_dataset("google-research-datasets/mbpp", split="test")`.
*   Deterministically select the first 500 tasks (or all if <500) to ensure reproducibility (Constitution I).
*   **Checksum**: Compute SHA-256 of the dataset cache directory upon download and record in project state.

## 3. Model & Methodology

### Model Selection
*   **Model**: `Salesforce/codegen-350M-mono`.
*   **Rationale**: Selected by the spec (US-1) as the target for resource-constrained evaluation.
*   **Precision Strategy**:
    *   **Default**: FP32 (32-bit float) as per FR-002.
    *   **Fallback**: If RAM usage > 6.5GB, switch to FP16 (16-bit float). This is a valid scientific approximation for inference and ensures compliance with Constitution VI.
*   **Device**: CPU only. No CUDA/GPU dependencies.

### Prompting Strategies
1.  **Zero-Shot**: Direct prompt with the problem description.
2.  **Few-Shot**: Prompt includes 3 exemplar (problem, solution) pairs before the target problem.
3.  **Chain-of-Thought (CoT)**: Prompt explicitly requests step-by-step reasoning before the code block.
    *   *Extraction*: A regex parser will extract the *first* valid Python code block from the generation (Edge Case: Model Output Parsing).

### Execution & Evaluation
*   **Sampling Strategy**: **k=10 samples per task for ALL strategies** (Zero-shot, Few-shot, CoT). This ensures the "Pass" outcome is defined consistently (at least one of 10 samples passed) across all conditions, isolating the prompting strategy effect from the sample count.
*   **Seeding**: 3 independent random seeds applied to **ALL** strategies for every task.
*   **Sandbox**: `subprocess` with `resource.setrlimit` for:
    *   Time: A brief, fixed duration (Edge Case: Timeout Handling).
    *   Memory: A bounded allocation per task, consistent with the resource constraints defined in the research question and method. (Edge Case: Memory Pressure).
*   **Metrics**:
    *   **pass@10**: Fraction of tasks where at least 1 of 10 samples passes (binary outcome for McNemar's).
    *   **Statistical Test**: **McNemar's test** (FR-006) on paired binary outcomes (Pass/Fail for pass@10) between Zero-shot and CoT.
    *   **Engineering Metrics**: Timeout rate, Parsing success rate (SC-004, SC-005).

## 4. Statistical Rigor & Power Analysis

*   **Multiple Comparisons**: The primary comparison is Zero-shot vs. CoT. If Few-shot is compared, a Bonferroni correction will be applied to the alpha level to control family-wise error rate.
*   **Sample Size**: 500 tasks × 3 seeds = 1500 total paired observations.
    *   *Power Justification*: McNemar's test power depends on the number of **discordant pairs** (tasks where one strategy passed and the other failed).
    *   *Sensitivity Analysis*: The analysis script will calculate the count of discordant pairs. If the count is < 50, the result will be reported as **"Inconclusive: Insufficient discordant pairs for valid McNemar's test"** rather than forcing a p-value. This addresses the risk of high/low pass rates rendering the test underpowered.
*   **Causal Assumptions**: This is an experimental study (controlled prompting strategies). Randomization is achieved via the 3 independent random seeds. Claims will be framed as "strategy effectiveness" rather than causal effects on the model's internal state.
*   **Collinearity**: Not applicable (strategies are mutually exclusive conditions per run).
*   **Measurement Validity**: MBPP is a standard benchmark for code generation. Execution-based metrics (pass@k) are the gold standard (Constitution VII).

## 5. Resource Feasibility & Risk Mitigation

*   **Compute Budget**:
    *   **RAM**: Medium-scale model (FP32) ≈ 1.4GB. Tokenizer + Data + Overhead < 2GB. Safe margin for GB limit.
    *   **Runtime**: 500 tasks × 3 strategies × 3 seeds × k=10 samples = 45,000 inferences.
 * *Estimate*: [deferred] × 1.5s = 67,500s (18.75h).
        *   *Mitigation*: The spec mandates 3 seeds for all strategies. To ensure <6h, the implementation will:
            1.  Use efficient batching (batch size 1 to avoid OOM, but parallelize tasks if CPU cores allow).
            2.  If runtime exceeds 6h, the "Resource Constraint Warning" (SC-003) will be logged, but the job will continue to preserve statistical power.
            3.  Note: The 6h limit is a hard CI constraint; if the full run exceeds it, the job will be terminated by GitHub Actions. The plan prioritizes statistical validity (running as much as possible) and logs the warning.
*   **Risk**: Model OOM.
    *   *Mitigation*: Automatic FP16 fallback (FR-002).
*   **Risk**: Infinite loops in generated code.
    *   *Mitigation*: Strict 10s timeout (FR-004).

## 6. Decision Rationale

*   **Why McNemar's Test?**: The data is paired (same task evaluated under different strategies). McNemar's is the standard test for paired binary data.
*   **Why FP16 Fallback?**: Ensures the experiment completes on the free-tier runner without crashing, adhering to Constitution VI.
*   **Why k=10 for All?**: To ensure the binary outcome (Pass/Fail) is defined identically for Zero-shot and CoT, avoiding the tautology of comparing pass@1 to pass@10.
*   **Why 3 Seeds?**: Addresses reproducibility (Constitution I) and reduces variance in the baseline.