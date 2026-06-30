# Research: Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages

## Research Question
To what extent does Python performance serve as a proxy for "General Code Capability" across 12 programming languages, and which models exhibit significant "Python overfitting" (performance significantly exceeding the baseline expectation derived from cross-language capability)?

## Methodological Approach

### 1. Dataset Strategy
The project utilizes the **Multi-LCB** dataset, which extends LiveCodeBench to 12 programming languages.
*Source Verification*: The '12 languages' claim is verified against the Multi-LCB repository README and the associated paper (e.g., "LiveCodeBench: A Dynamic Benchmark...").
*Handling Multiple Sources*: If the dataset is split across multiple repositories, the `download.py` script will merge them into a unified structure. If the full multi-language dataset is not available via the verified URLs, the system will proceed with available languages and explicitly document the gap.

**Verified Sources (from input block):**
- LCB (parquet): ` (and related shards).
- *Note*: The implementation will verify if these shards contain the 12 languages. If the full 12-language dataset is not available via the verified URLs, the system will proceed with available languages and explicitly document the gap.

**Dataset Variables Required:**
- `task_id`: Unique identifier.
- `language`: One of the 12 target languages (C++, Java, Python, Rust, etc.).
- `problem_statement`: Natural language description.
- `test_cases`: Input/Output pairs (STDIN/STDOUT).
- `reference_solution`: Ground truth code.
- `release_date`: Date the task was released (for contamination check).
- `metadata`: Model training cutoffs (external reference).

**Handling Missing Variables & Language Count:**
- If `release_date` is missing, the task is excluded from contamination check (Constitution Principle VII) and logged.
- **Language Count Validation**: The system will count distinct languages. If < 5 languages are present, PCA will be skipped. Instead, 'General Code Capability' will be computed as a simple average of available non-Python languages, with a clear limitation note in the report.

### 2. Execution Pipeline (FR-001 to FR-004)
1. **Download & Verify**: Fetch dataset from HuggingFace. Compute checksum. Pin to commit hash.
2. **Preprocessing**:
 - Convert test cases to unified JSON format.
 - **Contamination Filter**: Compare `task.release_date` vs. `model.training_cutoff`. Exclude tasks where `release_date > cutoff`.
 - **Task**: Calculate and log the percentage of excluded tasks (SC-005).
3. **Sandboxed Execution**:
 - Use Docker containers for each language to ensure isolation and standardized I/O.
 - Execute LLM generations at varying temperatures across low, medium, and high settings.
 - Run multiple independent attempts per task.
 - **Timeout Handling**: Treat timeout as "fail" but record duration for bias analysis.
 - **Runtime Errors**: Log as "runtime failure" (distinct from logic fail) and exclude from Pass@k.
4. **Metric Calculation**:
 - Compute Pass@k for each Model-Language-Temperature triplet.
 - Store Mean and Standard Deviation.
 - **Raw Data Retention**: Retain raw binary pass/fail outcomes for each of multiple runs per task for GLMM analysis.

### 3. Statistical Analysis (FR-005, FR-007)

**A. General Code Capability (Leave-One-Out PCA)**
- **Input**: Pass@1 matrix (Models × Languages).
- **Validity Check**: Compute Kaiser-Meyer-Olkin (KMO) measure and generate scree plot.
 - *Criteria*: Proceed with PCA only if KMO ≥ 0.6 and PC1 explains > 50% of variance.
 - *Fallback*: If criteria fail, use simple average of non-Python languages.
- **Method**: Principal Component Analysis (PCA) on the correlation matrix of the **other 11 languages** (Leave-One-Out for Python) to derive PC1. This ensures the baseline is independent of Python performance.
 - *Note*: This addresses the circular validation risk where including Python in PC1 would guarantee a high correlation.
- **Output**: LOO_PC1 score for each model (representing "General Code Capability").

**B. Correlation Analysis**
- Compute Pearson correlation between `Python_Pass@1` and `LOO_PC1_Score`.
- **Null Hypothesis**: The population correlation coefficient is zero.
- **Baseline Comparison**: Calculate intra-model consistency (correlation between two independent runs of the same model) as an upper bound. Use Fisher's z-transformation to test if the Python-LOO_PC1 correlation is significantly *less* than this baseline (indicating Python is a noisy proxy) or significantly *greater* than zero. This satisfies SC-001.

**C. Generalized Linear Mixed Model (GLMM)**
- **Formula**: `Pass ~ Language + LOO_PC1 + (1|Task_ID)`.
 - *Fixed Effects*: `Language` (to test differences), `LOO_PC1` (to control for general capability).
 - *Random Effect*: `(1|Task_ID)` models the variance across the **10 independent runs** per task. The unit of observation is the individual run (binary pass/fail), not the aggregated task. This avoids the singular matrix error and correctly models task difficulty.
 - *Note*: The model operates on raw binary pass/fail data, not aggregated proportions.
- **Focus**: Interaction term `Language × Model` (if added as fixed effect) or main effects to assess ranking stability.
- **Multiple Comparison Correction**:
 - First, perform a global test of the `Language × Model` interaction (one p-value).
 - If significant, perform post-hoc pairwise comparisons (up to 288 comparisons) with Bonferroni correction to control family-wise error rate (FWER ≤ 0.05).
 - **Secondary Requirement**: Perform paired t-tests or Wilcoxon signed-rank tests (with Bonferroni correction) for pairwise language comparisons to strictly satisfy Constitution Principle VI.
- *Statistical Rigor*: Explicitly acknowledge if the dataset size is insufficient for robust GLMM convergence; if so, use non-parametric alternatives or bootstrapping.

**D. Python Overfitting Detection**
- **Definition**: Residual = `Python_Pass@1` - `Predicted_from_LOO_PC1`.
- **Threshold**: Define as residual > k * Standard Error (SE) of the prediction, where k is a multiplier (e.g., 1.5, 2.0, 2.5).
- **Threshold Sweep**: Sensitivity analysis will sweep over the multiplier of SE (e.g., 1.5, 2.0, 2.5) rather than fixed values, ensuring the claim is statistically significant and not an artifact of arbitrary thresholds.

### 4. Sensitivity Analysis (FR-007, US-3)
- **Temperature Sensitivity**: Re-run correlation and ranking on subsets (0.2, 0.6, 1.0) to check stability (SC-003).
- **Threshold Sensitivity**: Sweep overfitting multipliers (k).
- **Contamination Sensitivity**: Re-run analysis with/without filtered tasks to quantify impact of contamination.

### 5. Compute Feasibility & Limitations
- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM) for Stage 1 (Sampled); Larger Runner for Stage 2 (Full).
- **Strategy**:
 - **Sampling**: Stage uses a representative set of tasks per language to fit the CI window.
 - **Full Run**: Stage 2 uses ALL tasks on larger runner.
 - **Inference**: Use CPU-optimized models (e.g., 7B-13B quantized for CPU if available, or API calls). No GPU training.
 - **Runtime**: Target <6 hours for Stage 1.
- **Limitations**:
 - GLMM convergence may be unstable on small samples; results will be reported with confidence intervals.
 - CPU-only inference limits model size; results may not reflect SOTA 70B+ model performance.
 - If the "Multi-LCB" 12-language dataset is not fully available, analysis restricted to available languages (with fallback methodology).