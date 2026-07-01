# Research: Evaluating the Impact of LLM-Generated Code on Memory Usage

## Dataset Strategy

The research relies on standard algorithmic benchmarks containing code solutions and test inputs.

| Dataset Name | Description | Source / Loader | Verified Status |
| :--- | :--- | :--- | :--- |
| **HumanEval** | 164 Python programming problems with unit tests. | `datasets.load_dataset("openai_humaneval")` | **Verified** (HuggingFace) |
| **MBPP** | Mostly Basic Python Problems. | `datasets.load_dataset("mbpp")` | **Verified** (HuggingFace) |

*Note: As per the "Verified datasets" block, no external raw URLs are cited. The datasets are accessed via the HuggingFace `datasets` library which points to the canonical repositories.*

**Selection Rationale**: HumanEval is selected as the primary dataset due to its widespread use in LLM code generation benchmarks and the availability of reference solutions for direct comparison. **MBPP serves as a mandatory fallback**: if HumanEval yields fewer than 50 valid paired observations (after filtering for syntax errors and timeouts), the pipeline will automatically switch to MBPP to meet the N=50 target.

## LLM Generation Strategy

**Model Selection**:
-   **Primary**: `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (1.1B parameters).
    -   *Rationale*: Fits within 7 GB RAM on CPU in float16 (~2.2 GB), leaving sufficient headroom for the execution sandbox.
-   **Quantization**: The system will **attempt** `load_in_8bit=True` first as required by FR-002. If the backend fails (common on CPU-only runners), it will gracefully fall back to float16.
-   **Excluded**: Phi-2 (2.7B) and CodeLlama-7B.
    -   *Rationale*: Phi-2 float16 requires ~5.4 GB RAM, leaving <1.6 GB for the OS and execution sandbox, creating a high risk of OOM. CodeLlama-7B is infeasible without GPU.

**Generation Parameters**:
-   `max_new_tokens`: 512
-   `temperature`: 0.2 (deterministic-ish)
-   `do_sample`: False (greedy search preferred for reproducibility)
-   `stop_sequences`: `["\nclass", "\ndef", "\nif", "```"]` (to prevent multi-function generation)

## Statistical Analysis Plan

### 1. Primary Comparison (Memory Usage)
-   **Hypothesis**: $H_0$: The distribution of memory usage for LLM code is identical to Human code.
-   **Method**:
    -   **Primary**: **Kaplan-Meier Estimator** to handle right-censored data (timeouts/OOMs at 7 GB). This estimates the survival function of memory usage, directly addressing FR-004's requirement for a censored-data method.
    -   **Secondary**: Wilcoxon Signed-Rank Test on the subset of successful executions (uncensored).
-   **Correction**: If multiple metrics (Peak, Steady, Efficiency) are tested, apply Holm-Bonferroni correction.
-   **Effect Size**: Calculate **Rank-Biserial Correlation** (for Wilcoxon) or **Log-Rank Statistic** (for KM).
-   **Interpretation**: The calculated effect size will be explicitly compared against Cohen's benchmarks (0.2=small, 0.5=medium, 0.8=large) and reported with the magnitude category in the final output (SC-004).

### 2. Feature Correlation Analysis (Size Control)
-   **Method**: **Two-Stage Residualization**.
    1.  Regress `Peak Memory` on `Lines of Code` (and `Complexity`, `Imports` if needed) to obtain residuals.
    2.  Compare the residuals between LLM and Human groups using a t-test or Wilcoxon test.
-   **Rationale**: This isolates the "LLM effect" from the "code size effect," addressing collinearity concerns (LOC vs Complexity) and preventing spurious correlations.
-   **Diagnostics**: Variance Inflation Factor (VIF) calculated for all predictors (LOC, Complexity, Imports). VIF > 5 flagged.
-   **Circularity Prevention**: `memory_per_loc` is calculated as a descriptive metric (FR-006) but **explicitly excluded** from any regression or modeling steps.

### 3. Robustness Checks
-   **Stability**: Use **Interquartile Range (IQR)** of the 3 runs. If IQR > 15% of the median, the sample is re-run or excluded (more robust than CV for heavy-tailed data).
-   **Sensitivity**: Analysis repeated excluding outliers (memory > 90th percentile) to check stability of significance.

## Computational Constraints & Mitigations

| Constraint | Mitigation Strategy |
| :--- | :--- |
| **7 GB RAM Limit** | Use TinyLlama-1.1B (1.1B) in float16 (~2.2 GB). Stream data. No large batch processing. |
| **No GPU** | Avoid CUDA-dependent libraries. Use CPU-optimized `transformers` pipelines. |
| **6 Hour Time Budget** | Limit N to a manageable size appropriate for the study's scope. Enforce a timeout per code execution. Skip re-runs if IQR is stable. |
| **Censored Data** | Use Kaplan-Meier estimator (primary) for timeouts/OOMs. Wilcoxon for uncensored subset. |

## Ethical & Safety Considerations

-   **Associational Claims**: The study explicitly avoids causal language. Differences are attributed to "generation artifacts" rather than "causation by LLM".
-   **Bias**: HumanEval may favor styles common in training data. The analysis controls for code length and complexity to mitigate style bias.