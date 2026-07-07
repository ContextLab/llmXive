# Feature Specification: Assessing the Stability of Statistical Model Performance Across Data Subsets

**Feature Branch**: `001-assess-model-stability`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Assessing the Stability of Statistical Model Performance Across Data Subsets"

## User Scenarios & Testing

### User Story 1 - Repeated Cross-Validation Execution (Priority: P1)

The system MUST execute a repeated k-fold cross-validation protocol (10 folds, 10 repeats = 100 evaluations) for three standard models (Logistic Regression, Random Forest, Linear SVM) across 15 binary classification datasets from UCI/OpenML, recording accuracy and F1-scores for every evaluation.

**Why this priority**: This is the core data generation engine. Without the full distribution of performance metrics (not just the mean), the subsequent analysis of variance and stability is impossible. It delivers the raw empirical evidence required to answer the research question.

**Independent Test**: The system can be tested by running the pipeline on a single small dataset (e.g., Iris or a subset of a larger one) and verifying that exactly 100 performance records are generated per model, with non-zero variance in the recorded metrics.

**Acceptance Scenarios**:

1. **Given** a valid dataset URL and model configuration, **When** the evaluation loop completes 100 iterations, **Then** the system outputs a structured dataset containing 300 rows (100 per model) with columns for `model_name`, `fold_id`, `repeat_id`, `accuracy`, and `f1_score`.
2. **Given** a dataset with missing values, **When** the preprocessing step runs, **Then** the system applies a standard imputation strategy (e.g., median for numeric, mode for categorical) consistent across all folds to prevent data leakage, and proceeds with evaluation.

---

### User Story 2 - Variance Quantification and Correlation Analysis (Priority: P2)

The system MUST calculate the Coefficient of Variation (CV = std/mean) of accuracy and F1-scores for each model-dataset pair and compute Pearson correlations between these CV metrics and dataset properties (sample size, feature count).

**Why this priority**: This transforms raw performance logs into the specific metric of interest: "stability." It directly addresses the research question by quantifying the relationship between dataset characteristics and performance noise, while normalizing for the mean performance to avoid trivial correlations with sample size.

**Independent Test**: The system can be tested by feeding it a synthetic dataset where the variance is manually set to zero (deterministic model) and verifying the calculated Coefficient of Variation is 0, or by checking the correlation coefficient against a known synthetic relationship.

**Acceptance Scenarios**:

1. **Given** the output of the repeated cross-validation, **When** the aggregation script runs, **Then** it produces a summary table where each row represents a unique (dataset, model) pair with columns for `mean_accuracy`, `cv_accuracy`, `mean_f1`, `cv_f1`, `n_samples`, and `n_features`.
2. **Given** the summary table, **When** the correlation analysis runs, **Then** it outputs a matrix of Pearson correlation coefficients and p-values linking `cv_accuracy` and `cv_f1` to `n_samples` and `n_features`.

---

### User Story 3 - Statistical Significance of Variance Differences (Priority: P3)

The system MUST apply a Permutation Test on the absolute differences of squared deviations to compare the variance distributions of performance metrics across the three different models for each dataset to determine if any algorithm is inherently more stable.

**Why this priority**: This adds a layer of inferential rigor, moving beyond descriptive statistics to test the hypothesis that specific algorithms are more robust to sampling noise than others. It answers the "which model" aspect of the research question using a method valid for paired data.

**Independent Test**: The system can be tested by generating two groups of performance scores with known, different variances and verifying that the Permutation Test correctly rejects the null hypothesis of equal variances.

**Acceptance Scenarios**:

1. **Given** the distribution of accuracy scores for Logistic Regression, Random Forest, and Linear SVM on a specific dataset, **When** the Permutation Test is executed, **Then** the system records the test statistic and p-value in the results summary.
2. **Given** a p-value < 0.05 from the Permutation Test, **When** the report is generated, **Then** the system flags that dataset as having "Significant Variance Differences" between models.

### Edge Cases

- **Dataset Size Limit**: What happens if a dataset has fewer than 100 samples, making 10-fold cross-validation (with 10 repeats) computationally unstable or impossible? The system must detect this and skip the dataset, logging a warning. It MUST NOT reduce the fold count. (See FR-001)
- **Zero Variance**: How does the system handle a scenario where a model achieves [deferred] accuracy on every fold (std=0)? The correlation calculation must handle zero-variance predictors without crashing (e.g., by excluding them from the correlation matrix or treating them as a specific data point).
- **Network Failure**: If a UCI dataset download fails due to network issues, the system must log the error, skip that specific dataset, and continue with the remaining datasets, rather than halting the entire 6-hour job.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess multiple binary classification datasets from UCI/OpenML covering a range of sample sizes (100 to [deferred]) and feature dimensions, ensuring no data leakage during preprocessing. (See US-1)
- **FR-002**: System MUST execute repeated k-fold cross-validation evaluations for Logistic Regression, Random Forest, and Linear SVM on each dataset, recording accuracy and F1-scores for every iteration. (See US-1)
- **FR-003**: System MUST calculate the Coefficient of Variation (CV = standard deviation / mean) of accuracy and F1-scores for each (dataset, model) pair to quantify performance stability. (See US-2)
- **FR-004**: System MUST compute Pearson correlation coefficients between the calculated performance Coefficient of Variation (CV) and dataset metadata (sample size, feature count) to assess the relationship between data properties and stability. (See US-2)
- **FR-005**: System MUST apply a Permutation Test on the absolute differences of squared deviations to compare variance distributions across the three models for each dataset to identify inherent stability differences. (See US-3)
- **FR-006**: System MUST execute all computations on the GitHub Actions ubuntu-latest runner (CPU-only) using the standard Python data science stack (pandas, numpy, scikit-learn) without requiring GPU acceleration or large-model training. (See US-1)
- **FR-007**: System MUST implement a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) for the set of hypothesis tests (correlations and Permutation Tests) performed across the datasets to control the family-wise error rate. (See US-2, US-3)

### Key Entities

- **Dataset**: A binary classification dataset from UCI/OpenML, characterized by attributes `n_samples`, `n_features`, and `source_url`.
- **EvaluationRun**: A single instance of model training and testing within a specific fold and repeat, characterized by `model_name`, `accuracy`, and `f1_score`.
- **StabilityMetric**: An aggregated record for a (dataset, model) pair, characterized by `mean_accuracy`, `cv_accuracy`, `mean_f1`, and `cv_f1`.
- **CorrelationResult**: A statistical summary linking `StabilityMetric` variance to `Dataset` properties, characterized by `correlation_coefficient`, `p_value`, and `dataset_property`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Coefficient of Variation (CV) of accuracy scores across 100 repeats is measured against the sample size of the dataset to quantify the noise floor. (See US-2)
- **SC-002**: The Pearson correlation coefficient between performance CV and dataset properties (sample size, feature count) is measured against the null hypothesis of zero correlation. (See US-2)
- **SC-003**: The p-values from Permutation Tests comparing model variances are measured against the significance threshold (adjusted for multiplicity) to determine if variance differences are statistically significant. (See US-3)
- **SC-004**: The total runtime of the full pipeline (multiple datasets × multiple models × 100 repeats) is measured against the 6-hour GitHub Actions free-tier limit to ensure feasibility. (See US-1)
- **SC-005**: The family-wise error rate (FWER) for the set of correlation and variance tests is measured against the target alpha level (e.g., 0.05) after applying the specified multiple-comparison correction. (See FR-007)

## Assumptions

- **Dataset Availability**: The UCI Machine Learning Repository and OpenML will remain accessible via standard HTTP requests during the execution window, and the 15 selected datasets will be available in a format compatible with `pandas`/`scikit-learn` without extensive manual cleaning.
- **Compute Constraints**: The total memory footprint of loading a representative set of datasets (including the largest ones) simultaneously or sequentially will remain within the free-tier runner's RAM limit., provided that large datasets (>10k samples) are processed with efficient chunking or sampling if necessary.
- **Model Complexity**: Logistic Regression, Random Forest (with default `n_estimators=100`), and Linear SVM (with `LinearSVC`) will train within the 6-hour total time budget even with the 100-repetition requirement, assuming no datasets exceed 100,000 samples significantly or require complex hyperparameter tuning.
- **Statistical Validity**: Pearson correlation tests the relationship between two variables and requires normality of the residuals, not the variables themselves. Levene's test is robust to non-normality, and the distribution of variances across the 15 datasets does not need to be normal for the Permutation Test to be valid. A sufficient number of repeats will be conducted to provide a distribution for the Permutation Test to approximate the null distribution accurately.
- **Threshold Justification**: The significance threshold for Permutation Tests and correlation p-values is set to α = 0.05, adjusted for multiplicity using the Benjamini-Hochberg procedure, which is a community-standard approach for exploratory statistical analysis.
- **Data Integrity**: The datasets selected contain no target leakage or inherent data quality issues that would artificially inflate or deflate performance variance beyond what is attributable to sampling noise.