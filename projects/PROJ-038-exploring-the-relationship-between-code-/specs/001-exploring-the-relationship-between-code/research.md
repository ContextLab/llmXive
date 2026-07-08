# Research: Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy

## Research Question
Which static code complexity metrics (Cyclomatic Complexity, Halstead Volume, Lines of Code) exhibit the strongest **unique** correlation with bug presence in Java projects, and can a model combining these metrics significantly outperform a model using only the single best metric (selected via nested cross-validation)?

## Dataset Strategy

The project relies on the **Defects4J** dataset (v2.0+), accessed via the official `defects4j` CLI tool to ensure ground-truth accuracy. The plan utilizes a subset of projects to ensure computational feasibility on CPU-only CI runners.

| Dataset Name | Source URL | Usage in Plan | Verification Status |
|:--- |:--- |:--- |:--- |
| **Defects4J (Official)** | ` | Primary source for project cloning, bug commit identification, and file-level bug mapping. Used to retrieve the exact list of files containing bugs at the time of the bug introduction. | Verified |
| **Defects4J (Projects List)** | ` | Metadata for project selection and versioning. | Verified |

*Note: The plan strictly uses the `defects4j` framework to checkout the specific buggy revision and retrieve the canonical list of buggy files. HuggingFace Parquet files are NOT used for labeling as they lack the necessary granular commit history and source code context.*

### Dataset Selection Rationale
- **Relevance**: Defects4J is the de facto standard for bug prediction research, providing ground-truth bug locations derived from real-world bug-fix commits.
- **Feasibility**: Selecting a small cohort of projects ensures the total source code size and metric extraction time fit within the available RAM and runtime limits.
- **Labeling**: The dataset provides explicit bug-fix commits. The plan uses the `defects4j` framework to map these to the specific files that *contained* the bug in the buggy revision, avoiding false positives from fix-commits that modify unrelated files.

## Methodology

### 1. Data Ingestion and Preprocessing (FR-001, FR-003)
- **Selection**: Randomly select a small set of projects from Defects4J v2.0+.
- **Ingestion**: Use `defects4j checkout -p <project> -v <bug_id> -f` to retrieve the **buggy revision** (the state *before* the fix).
- **Labeling (Ground Truth)**:
 - Retrieve the canonical list of files associated with the bug using `defects4j buginfo`.
 - **Crucial Distinction**: The `buginfo` command returns files modified in the *fix* commit. To avoid label leakage (where the fix changes the metrics), we cross-reference this list with the *buggy revision* state.
 - **Buggy Files**: Files that exist in the buggy revision AND are identified as part of the bug fix (via `buginfo` or a custom diff tool comparing buggy vs. fixed states) are labeled `is_buggy = 1`.
 - **Clean Files**: Files present in the buggy revision but *not* identified as part of the bug fix are labeled `is_buggy = 0`.
 - **Exclusion**: Files not present in the buggy revision (e.g., added later) are excluded. Generated code and non-Java files are excluded and logged.
 - **State Consistency**: Metrics are computed on the code state *at the time of the bug introduction* (the buggy revision), not the fix commit. This prevents circular validation where the fix changes the metrics.

### 2. Metric Extraction (FR-002)
- **Tools**: Use `tree-sitter-java` (for Halstead Volume and LOC) and a custom implementation of Cyclomatic Complexity (CC) based on the control flow graph, as PMD may have compatibility issues with older Java versions in Defects4J.
- **Process**:
 - Parse every `.java` file in the selected buggy revisions.
 - Compute:
 - **Cyclomatic Complexity (CC)**: Number of linearly independent paths.
 - **Halstead Volume (HV)**: Measure of program size based on operators and operands.
 - **Lines of Code (LOC)**: Physical lines of source code.
 - **Exclusion**: Generated code, non-Java files, and files with parsing errors are excluded and logged.

### 3. Correlation Analysis (FR-004)
- **Metrics**:
 - **Point-Biserial Correlation ($r_{pb}$)**: Measures the relationship between a continuous variable (metric) and a binary variable (bug label).
 - **Spearman Rank Correlation ($\rho$)**: Measures monotonic relationships, robust to non-normality.
- **Collinearity Check**: Calculate **Variance Inflation Factor (VIF)** for each metric. If VIF > 5, perform **Partial Correlation** analysis to isolate the unique contribution of each metric, addressing the interpretability concern regarding collinearity.
- **Output**: Coefficients, p-values, and VIF values for each metric. The research question is interpreted as "which metric has the strongest *unique* correlation" after controlling for others.

### 4. Baseline Modeling (FR-005)
- **Models**: Logistic Regression (LR) and Random Forest (RF).
- **Validation**: **Repeated 5-Fold Cross-Validation** (5 folds, 10 repeats, fixed seed).
- **Metrics**: Mean ROC-AUC and F1-score with standard deviation.
- **Class Imbalance**: Use stratified sampling to ensure each fold contains a representative proportion of buggy files. If a fold has only one class, report ROC-AUC as undefined for that fold.

### 5. Statistical Significance Testing (FR-006)
- **Comparison**: 'Full Metric Set' (LR/RF using all metrics) vs. 'Single Best Metric' model.
- **Selection Bias Mitigation (Nested CV)**: The 'Single Best Metric' is selected via **Nested Cross-Validation**.
 - **Outer Loop**: 5-Fold CV (10 repeats) for evaluation.
 - **Inner Loop**: Within each training set of the outer loop, a simple 5-fold CV is used to select the single best metric (based on ROC-AUC).
 - This ensures the 'best' metric is not selected based on the test data.
- **Test**: **Fold-Level Paired Permutation Test** on the aggregated predictions from the Repeated CV.
 - **Unit of Analysis**: The test operates on the **vector of 50 ROC-AUC scores** (one per fold) generated by the Repeated CV.
 - **Procedure**: For each of the 50 folds, we have a pair of ROC-AUC scores (Model A, Model B). We compute the difference $d_i = AUC_A - AUC_B$ for each fold $i$. We then permute the signs of these differences (or swap the labels A/B within each fold) to generate a null distribution of the mean difference.
 - **Rationale**: This preserves the hierarchical structure (files nested in projects nested in folds) and treats the 50 folds as the dependent samples, avoiding the invalidity of permuting thousands of individual predictions which would assume independence.
 - **Outcome**: P-value indicating if the performance difference is statistically significant ($p < 0.05$).

### 6. Feature Importance (FR-007)
- **Method**: Extract feature importance weights from the trained Random Forest model.
- **Output**: Ranked list of metrics by contribution to prediction accuracy.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: If multiple metrics are tested for correlation, a Bonferroni correction or False Discovery Rate (FDR) adjustment will be applied to the p-values to control family-wise error.
- **Power Analysis**: A **Post-Hoc Power Analysis** will be conducted to determine the **Minimum Detectable Effect Size (MDES)** given the expected class imbalance and sample size. If the MDES is unreasonably large (e.g., > 0.3), the study will explicitly state its power limitations and interpret non-significant results with caution.
- **Causal Inference**: This is an **observational** study. Claims will be framed as **associational** (e.g., "metrics are correlated with bugs") rather than causal.
- **Collinearity**: Metrics like LOC and CC are often correlated. The plan includes VIF analysis and partial correlation to disentangle these effects, avoiding claims of strict independence.
- **Measurement Validity**: Metrics are derived from standard static analysis tools (tree-sitter, custom CC) widely accepted in software engineering literature.
- **Constitution VI Override (Pending)**: The Constitution VI mandates 'Pearson' and 'McNemar's'. This plan uses Point-Biserial/Spearman and Paired Permutation Tests as mandated by the **Spec (FR-004, FR-006)**, which are scientifically more appropriate for binary targets and ROC-AUC comparisons. **This constitutes a formal amendment request (AMEND-001-STATS)**. Execution is blocked until this is resolved.

## Compute Feasibility Plan

- **Hardware**: CPU-only (2 cores, 7 GB RAM).
- **Data Subset**: 5-10 projects (approx. 10k-50k files).
- **Memory Management**:
 - Stream data processing where possible.
 - Use `pandas` with `dtype` optimization (e.g., `category` for project names, `float32` for metrics).
 - Limit `n_jobs` in scikit-learn to 1 or 2 to prevent RAM overflow.
- **Runtime**:
 - Metric extraction is the most CPU-intensive step. Parallelize file processing with a process pool limited to a constrained number of workers.
 - Model training (LR/RF) on 50 folds is fast for small datasets.
 - Total estimated runtime: < 4 hours.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Parsing Errors** | High (loss of data) | Use robust parsers (tree-sitter); log and exclude failing files; fallback to regex for simple metrics if needed. |
| **Class Imbalance** | Medium (invalid ROC-AUC) | Stratified K-Fold; report precision/recall if ROC-AUC is undefined; skip projects with 0 bugs. |
| **Memory Overflow** | High (CI failure) | Process files in batches; drop unnecessary columns; use `float32`. |
| **Dataset Incompatibility** | High (pipeline failure) | Validate Defects4J structure at start; fail fast with clear error message. |
| **Selection Bias** | High (invalid p-value) | Use Nested CV for metric selection. |
| **Constitutional Block** | Critical (Project Halt) | Formal amendment request (AMEND-001-STATS) submitted. Project paused until resolution. |