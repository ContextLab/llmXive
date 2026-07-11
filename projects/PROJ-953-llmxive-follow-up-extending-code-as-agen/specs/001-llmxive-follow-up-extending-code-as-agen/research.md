# Research: llmXive follow-up: extending "Code as Agent Harness"

## Research Question

Is there a statistically significant correlation between code structural complexity (dependency depth, cyclomatic complexity, semantic complexity) and the necessity of dynamic verification (observed test suite failure in full-environment execution) for agent tasks? Can a static-analysis-only classifier achieve a false-negative rate (FNR) ≤ 0.1% while skipping a significant portion of dynamic executions?

**Validity Note**: "Verification necessity" is operationalized as **test suite failure**. We acknowledge that "Pass" does not guarantee safety (latent bugs may exist) and "Fail" may include environmental noise. The study explicitly frames results as correlations with *test failure*, not absolute safety.

## Dataset Strategy

The project relies on datasets that provide code and test instructions. Ground truth is **generated** via re-execution, not fetched.

| Dataset | Source URL | Usage | Variables Needed |
| :--- | :--- | :--- | :--- |
| **SWE-bench Verified** | `https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified` | Ground truth for Python-based software engineering tasks. | `problem_statement`, `repo`, `version`, `instance_id`, `patch` (code diff), `test_patch` (for execution). |
| **AgentBench (OS)** | `https://huggingface.co/datasets/iFurySt/AgentBench` | Ground truth for OS-level agent tasks. | `instruction`, `code`, `environment`, `expected_output`. |
| **Excluded** | `SWE-bench Lite (BM25)` | Removed: Lacks full test suites required for ground truth generation. | N/A |
| **Excluded** | `AgentBench MAS (User Mirror)` | Removed: Non-canonical source. MAS subset excluded due to CPU environment complexity. | N/A |

**Note**: The "ASSOCIATIONAL" dataset mentioned in the spec has **NO verified source** and is excluded from the plan.

### Data Loading Strategy
- Use `datasets.load_dataset` or direct `parquet` loading from the verified URLs.
- **Sampling**: To ensure CPU feasibility (≤ 7GB RAM), the initial run will sample a representative subset (e.g., 500 tasks) from each dataset.
- **Ground Truth Generation**: The pipeline MUST re-execute the code snippets in an isolated environment to generate the `dynamic_execution_outcome` label. The datasets do not provide pre-computed labels for all tasks.

## Methodology

### Phase 0: Pilot & Base-Rate Estimation (NEW)
1. **Objective**: Estimate the base failure rate of the dataset to assess statistical power for the [deferred] FNR constraint.
2.  **Action**: Run a small subset (N=100) of tasks through the ingestion and execution baseline.
3.  **Decision Gate**:
    - If base failure rate < 0.5%, the study acknowledges that estimating a 0.1% FNR with high confidence is statistically impossible with N=500. The study pivots to reporting the **minimum achievable FNR** and the **confidence interval**, framing the result as "Static analysis insufficient for 0.1% safety threshold with current data."
    - If base failure rate > 0.5%, proceed to Phase 1.

### Phase 1: Ground Truth Generation (FR-001, FR-003)
1.  **Ingestion**: Download and parse the verified datasets.
2.  **Execution Baseline**:
    - For each task, execute the code modification in an isolated virtual environment (Python `venv` or lightweight Docker if available).
    - **Timeout Handling**: If execution exceeds 600 seconds, record as "Timeout/Fail" (Conservative Safety).
    - **Outcome**: Binary label `dynamic_execution_outcome` (Pass/Fail).
    - **Bias Mitigation**: Tasks failing due to obvious environmental issues (e.g., missing dependency, timeout) are tagged as `failure_type="environmental"`. The model will be trained on the full set, but results will be stratified to distinguish between "code logic failure" and "environmental failure".

### Phase 2: Structural Feature Extraction (FR-002)
1.  **Parsing**: Use `tree-sitter` (Python bindings) to parse code diffs.
2.  **Graph Construction**: Build dependency graphs (function calls, variable assignments).
3.  **Metric Calculation**:
    - `dependency_depth`: Max depth in the call graph.
    - `cyclomatic_complexity`: Using `radon` or custom graph traversal.
    - `semantic_complexity`: Approximated via node type distribution and control flow density.
    - **Fallback**: If specific nodes are missing, use `lines_of_code`, `dependency_depth`, and `cyclomatic_complexity` only (per Edge Cases in Spec).
4.  **Error Handling**: Tasks with syntax errors are flagged as "Unparseable" and excluded from modeling but retained for baseline stats.

### Phase 3: Predictive Modeling & Thresholding (FR-004, FR-005)
1.  **Model Selection**: Logistic Regression (interpretable) and Random Forest (robustness).
   - **Hardware Constraint**: Both models are CPU-tractable. No deep learning.
2.  **Training**: Split data into training and test sets using a standard partition ratio. Pin random seeds.
3.  **Threshold Analysis**:
    - Sweep thresholds: {, 0.05, 0.1}.
    - **Metric**: False Negative Rate (FNR). FNR = (Static Approval + Dynamic Fail) / Total Dynamic Fail.
    - **Constraint**: If min FNR > 0.1%, the study reports the minimum achievable FNR and the model is flagged as "unsafe for static-only classification at 0.1% threshold".
4.  **Feasibility Study**: Generate an ROC curve and discuss the theoretical limits of static analysis for this task. If the AUC is low, the study concludes that structural complexity is a poor predictor of test failure.
5.  **Causal Framing**: All results framed as **associational** (Observational data, no randomization).

## Statistical Rigor & Limitations

- **Multiple Comparisons**: If multiple models or datasets are compared, apply Bonferroni or Holm correction to p-values.
- **Power Analysis**: A formal power analysis is replaced by the **Pilot Phase** (Phase 0) to estimate the base rate. If the base rate is too low, the study explicitly reports the limitation: "Sample size insufficient to reliably estimate [deferred] FNR; reporting best achievable rate."
- **Collinearity**: `dependency_depth` and `cyclomatic_complexity` may be correlated. Variance Inflation Factor (VIF) will be calculated. If VIF > 5, models will be re-run with reduced feature sets, and results reported descriptively.
- **Measurement Validity**: `tree-sitter` is a standard, validated parser. `radon` is a standard complexity metric tool.
- **Construct Validity**: We acknowledge that "test suite pass/fail" is a proxy for "safety". The study explicitly reports this limitation and distinguishes between "code logic errors" and "environmental failures" where possible.

## Compute Feasibility

- **Runtime**: Target < 6 hours. Sampling and chunked processing will be used if full dataset ingestion exceeds limits.
- **Memory**: Target < 7GB. Graphs will be serialized to disk rather than held in memory for large batches.
- **No GPU**: All libraries (`scikit-learn`, `pandas`, `tree-sitter`) have CPU wheels.

## Risk Mitigation

- **Risk**: Dynamic execution is too slow for 500 tasks.
  - **Mitigation**: Parallelize execution within CPU limits (e.g., a limited number of workers). If still too slow, reduce sample size to a manageable subset for a pilot study.
- **Risk**: `tree-sitter` fails on complex code.
  - **Mitigation**: Implement the fallback metric set (Lines of Code, Depth, Cyclomatic) as specified in FR-002.
- **Risk**: Model cannot achieve [deferred] FNR.
  - **Mitigation**: This is a valid outcome. The study will report the ROC curve, the minimum achievable FNR, and conclude that static analysis alone is insufficient for the stated safety threshold.