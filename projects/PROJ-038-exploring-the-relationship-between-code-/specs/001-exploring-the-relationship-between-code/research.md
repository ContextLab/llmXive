# Research: Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy

## Dataset Strategy

### Primary Dataset: Defects4J
The project relies on the **Defects4J** dataset, a widely used benchmark for bug prediction research containing real-world bugs from open-source Java projects.

* **Source**: Defects4J is accessed via its canonical GitHub repository (`).
* **Access Method**: The `ingest.py` script will clone the repository and use the `defects4j` CLI tool (or direct file parsing) to extract the source code for specific versions of projects.
* **Verification**: The dataset is verified as a canonical, open-source resource. The "Verified datasets" block lists specific Parquet files derived from Defects4J context, but for *this* project, the requirement to analyze *source code* metrics (Halstead, Cyclomatic) necessitates accessing the raw source files. The Parquet files listed in the verified block appear to be pre-processed prompt-context datasets which may not contain the raw source code required for metric extraction. Therefore, the plan uses the **raw Defects4J GitHub repository** as the primary source, which is the standard method for this research domain.
* **Subset Selection**: To meet the 7 GB RAM constraint (Constitution Principle VII), the pipeline will:
 1. Query the list of available projects in Defects4J.
 2. Select 5-10 projects based on a heuristic (e.g., number of commits, file count) that ensures the total source code size is manageable.
 3. Log the selection criteria and the resulting project list in `data/processed/selection_log.md`.

### Alternative/Supplementary Data
* **LOC Dataset**: The "Verified datasets" block lists `LoC-PD-Books` and others. These are **not** suitable for this project as they do not contain Java source code with bug labels. They are ignored in favor of Defects4J.
* **ROC-AUC**: No verified source exists for "ROC-AUC" as a dataset; it is a metric calculated during analysis.

### Data Availability & Feasibility
* **Download**: Defects4J is a Git repository, fully downloadable via `git clone` on CI.
* **Size Management**: The raw Defects4J repository is large. The plan explicitly limits the *active* subset to 5-10 projects. The `ingest.py` script will perform a "dry run" to estimate the disk/memory footprint of a candidate subset before fully extracting it.
* **Streaming**: For metrics extraction, the pipeline will process files one-by-one or in small batches, appending results to a CSV, rather than loading all source files into memory simultaneously.

## Statistical Methodology

### Correlation Analysis (FR-004)
* **Method**: Point-Biserial correlation ($r_{pb}$) and Spearman rank correlation ($\rho$).
* **Rationale**: The target variable (`is_buggy`) is binary (0/1). Point-Biserial is the specific case of Pearson correlation for a binary and a continuous variable. Spearman is used as a non-parametric alternative to handle potential non-linearities or outliers in metric distributions (e.g., extremely high LOC).
* **Decision Rule**: If Point-Biserial and Spearman results diverge significantly (p-value difference > 0.05 or coefficient sign flip), the report will default to **Spearman** (non-parametric) and flag the result as "Non-Normal Distribution Detected".
* **Significance**: P-values will be calculated to determine if the correlation is statistically different from zero (alpha = 0.05).

### Baseline Modeling (FR-005)
* **Models**: Logistic Regression (LR) and Random Forest (RF).
* **Validation Strategy**: **Repeated 5-Fold Cross-Validation** (10 repeats, fixed seed).
 * *Why Repeated?* To reduce the variance of the performance estimate and ensure that the test sets are identical across different model comparisons, enabling valid paired tests later.
 * *Why 5-Fold?* A balance between computational cost and robustness.
* **Metrics**: ROC-AUC (primary), F1-score (secondary).

### Statistical Significance of Model Difference (FR-006)
* **Method**: **Sign-Flip Paired Permutation Test** (Randomization Test).
* **Procedure**:
 1. Generate predictions for the 'Full Metric Set' model and the 'Single Best Metric' model on the *same* 50 test folds (from the Repeated 5-Fold CV).
 2. Calculate the performance metric (e.g., ROC-AUC) for each fold for both models.
 3. Compute the observed difference in performance for each fold: $d_i = \text{Score}_{Full, i} - \text{Score}_{Single, i}$.
 4. **Null Hypothesis**: The models are equivalent, meaning the sign of the difference $d_i$ is random.
 5. Randomly flip the sign of $d_i$ for each fold (multiply by -1 with probability 0.5) thousands of times to build a null distribution of the mean difference.
 6. Calculate the p-value as the proportion of permuted mean differences that are as extreme or more extreme than the observed mean difference.
* **Rationale**: This method correctly accounts for the paired nature of the CV folds and makes no distributional assumptions. It replaces the invalid "label permutation" approach.

### Handling Class Imbalance (Edge Case)
* **Strategy**:
 1. **Stratified Split**: Use Stratified K-Fold to ensure each fold has a representative proportion of buggy files.
 2. **Fallback**: If a fold still has zero buggy files (extreme imbalance), the pipeline will **not** skip the fold. Instead, it will aggregate predictions across all folds (Micro-averaging) and calculate a single ROC-AUC for the entire dataset, rather than averaging fold-level AUCs. This prevents selection bias.
 3. **Logging**: Projects with zero buggy files will be skipped with a warning logged to `exclusions.log`.

## Compute Feasibility & GPU Strategy

* **CPU-First**: All proposed methods (PMD execution, Java parsing, Logistic Regression, Random Forest, Sign-Flip Permutation Test) are computationally feasible on a standard 2-core CPU within 6 hours for a subset of 5-10 projects.
 * *Memory*: Streaming file processing ensures RAM usage stays under a manageable threshold.
 * *Time*: Static analysis of a large volume of files is the bottleneck. Parallelizing the metric extraction across 2 cores (using `multiprocessing`) will be employed to stay within the 6-hour limit.
* **GPU Escape Hatch**: **Not Required**. No deep learning models (Transformers, CNNs) are planned. The Random Forest and Logistic Regression models are CPU-optimized. The GPU escape hatch (Kaggle) is not needed for this specific feature.

## References
* Defects4J: `
* Statistical Hypothesis Testing: ` (Alpha = 0.05)
