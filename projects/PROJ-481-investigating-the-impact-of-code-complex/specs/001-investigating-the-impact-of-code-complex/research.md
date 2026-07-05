# Research: Investigating the Impact of Code Complexity on LLM Code Understanding

## 1. Research Question & Hypothesis

**Primary Question**: How does static code complexity (Cyclomatic, Halstead, Cognitive) **associate** with the accuracy of LLMs on code understanding tasks, and at what complexity threshold does performance degrade significantly?

**Hypotheses**:
- **H1**: There is a statistically significant negative **association** between static complexity metrics and LLM accuracy (Spearman/Pearson r < 0, p < 0.05).
- **H2**: A specific complexity threshold exists (detected via segmented regression) where the rate of accuracy decline accelerates.
- **H3**: The association strength varies by task type (Reconstruction vs. Summarization).

**Causal Disclaimer**: This study is **observational**. Observed correlations are interpreted as associations within the static code domain. Causal claims are not made due to potential confounding variables (e.g., developer experience, code age) which are not controlled for in the dataset.

## 2. Dataset Strategy

The plan relies **only** on verified datasets provided in the specification.

| Dataset Role | Source Name | Verified URL | Rationale |
|:--- |:--- |:--- |:--- |
| **Code Corpus (Summarization)** | CodeSearchNet (Python) | ` | Contains Python functions with natural language summaries (ground truth for summarization). |
| **Code Corpus (Completion)** | CodeSearchNet (Python) | ` | Used for "Reconstruction" tasks (code -> code) where ground truth is the original source. |
| **Bug Detection** | **Excluded** | N/A | No verified dataset with "buggy vs. clean" labels for Python functions is available in the verified block. This task is removed from the primary analysis to avoid hallucination. |
| **Model Reference** | CodeLlama / StarCoder | (Model weights hosted on HuggingFace Hub, not a dataset URL) | Models will be loaded via `transformers`/`llama.cpp` using quantized versions available on the Hub. |

**Dataset Fit Analysis**:
- **CodeSearchNet**: Provides `code` and `docstring`. Perfect for **Summarization** task. Also supports **Reconstruction** (code -> code) where ground truth is the input itself (with caution regarding circularity).
- **BigCodeBench**: Excluded from primary analysis for "Bug Detection" as it lacks specific bug labels and is designed for generation from instructions, not analysis of existing code.
- **Gap Handling**: The "Bug Detection" task is **removed** from the primary hypothesis testing due to the lack of a verified ground truth dataset. The study focuses on **Summarization** and **Reconstruction** (fidelity) only.

**Sampling Strategy**:
- To meet the **7 GB RAM** and **6 hour** constraint, the full datasets cannot be processed with LLM inference.
- **Strategy**: Random stratified sampling of **N = 1,000** functions.
- **Rationale**: N=1,000 is a conservative estimate to ensure the 6-hour runtime limit on CPU is met, even with slower inference times.
- **Stratification**: Ensure a distribution of complexity levels (if pre-computed) or random selection to avoid bias.

## 3. Methodology

### Phase 1: Static Metric Computation (FR-001)
- **Tool**: `radon` (pinned version in `requirements.txt`).
- **Metrics**:
 - **Cyclomatic Complexity (CC)**: `radon cc -s` (sum of branches).
 - **Halstead Volume**: `radon halstead` (operators/operands).
 - **Cognitive Complexity**: `radon cc --show-cognitive`.
- **Edge Cases**:
 - Syntax errors: `radon` will raise exceptions. The script will `try/except` and log to `errors.csv`, skipping the function.
 - Zero complexity: Handled as a valid numeric value (0).

### Phase 2: LLM Inference (FR-002, FR-003)
- **Models**:
 - **StarCoder-1B** or **StarCoder-3B** via `llama-cpp-python` (GGUF quantized).
 - **CodeLlama-7B** (Quantized to 4-bit GGUF) via `llama-cpp-python` (only if memory permits, otherwise fallback to 1B).
 - *Rationale*: Small-scale models fit within the 7GB limit with data buffering.
- **Tasks**:
 1. **Summarization**: Input `code` -> Output `summary`. Ground Truth: `docstring` (CodeSearchNet).
 2. **Reconstruction**: Input `code` -> Output `code`. Ground Truth: `source_code` (CodeSearchNet). *Note: This measures reconstruction fidelity, not semantic understanding, and is treated with caution.*
- **Metrics**:
 - **Summarization**: ROUGE-L, BLEU.
 - **Reconstruction**: ROUGE-L (treated as a fidelity metric).
- **Failure Handling**:
 - Timeout/Memory: Catch `TimeoutError` or `OOM`. Set `accuracy = 0`, `hallucination_flag = true` (if output is garbage).
 - Hallucination: If output contains non-code tokens or is empty, flag and score 0.
 - **Timeout Strategy**: Strict timeout per sample. If exceeded, sample is skipped and logged.

### Phase 3: Statistical Analysis (FR-004, FR-005)
- **Collinearity Handling**:
 - Perform **Principal Component Analysis (PCA)** on complexity metrics to create a single "Complexity Index".
 - Report correlations for individual metrics and the composite index.
 - Use **Ridge Regression** for multivariate models to mitigate multicollinearity.
- **Dataset Confound Control**:
 - Include `dataset_source` as a **fixed effect** (covariate) in all regression models.
 - Stratify analysis by dataset source to verify robustness.
- **Correlation**: Spearman's rank correlation (robust to non-linearities) between complexity metrics and accuracy.
 - **Significance**: p-value < 0.05.
 - **Correction**: Bonferroni correction for multiple comparisons.
 - **Confidence**: Bootstrap (sufficient resamples) to generate 95% CI for correlation coefficients.
- **Threshold Detection (Change-Point)**:
 - **Method**: **Segmented Beta Regression** (to handle bounded [0,1] accuracy) or **Generalized Additive Models (GAM)** with a smooth term for complexity.
 - **Robustness Check**: Compare Segmented Regression results against a GAM and polynomial regression. If the non-linear fit is significantly better, the "threshold" is reported as a range or non-monotonic pattern.
 - **Optimization**: Grid search or `scipy.optimize` to find the `threshold` that minimizes residual deviance.
 - **Confidence**: Bootstrap (1000 resamples) to generate 95% CI for the threshold values (satisfying Constitution Principle VII).
- **Assumptions**:
 - Observational study: Correlation does not imply causation.
 - Collinearity: CC, Halstead, and Cognitive complexity are highly correlated. The plan uses PCA to isolate the "complexity" effect.

## 4. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free (limited CPU, 7 GB RAM).
- **Memory Management**:
 - Dataframes loaded in chunks.
 - LLM inference runs in batches of 1.
 - Models loaded in `int4` (GGUF) to fit.
- **Time Management**:
 - **Target Sample Size**: N = 1,000.
 - **Runtime Budget**: 6 hours.
 - **Mitigation**: If runtime exceeds 4 hours at [deferred] completion, the pipeline will automatically reduce the remaining batch size or skip samples to ensure completion.
 - **Fail-Fast**: A timeout is applied per inference.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| Dataset lacks ground truth for specific tasks | High | Removed "Bug Detection" task. Focused on Summarization and Reconstruction (CodeSearchNet). |
| LLM inference too slow on CPU | High | Reduced N to [deferred]. Used smaller models (1B-3B). Added strict timeout. |
| High collinearity between metrics | Medium | Used PCA for composite index and Ridge regression. |
| Memory overflow during analysis | Medium | Process in chunks; use `pandas` with `dtype` optimization. |
| Circular validation in Reconstruction | Medium | Treated Reconstruction as a "fidelity" metric only; prioritized Summarization for "understanding" analysis. |