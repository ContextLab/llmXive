# Feature Specification: Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy

**Feature Branch**: `001-code-complexity-bug-prediction`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Metric Extraction (Priority: P1)

The system must successfully ingest a subset of Java projects from the Defects4J dataset and compute static code complexity metrics (Cyclomatic Complexity, Halstead Volume, Lines of Code) for every source file, generating a labeled feature matrix where each row represents a file and the target variable indicates if the file contains a bug.

**Why this priority**: This is the foundational step. Without a clean, labeled dataset containing both the code metrics and the ground truth (buggy vs. clean), no analysis or modeling can occur. It directly enables the core research question.

**Independent Test**: The pipeline can be executed end-to-end on a local machine or CI runner, producing a CSV file where the number of rows equals the count of **successfully processed Java source files** (excluding generated code, non-Java files, and files with parsing errors), and the "target" column contains only binary values (0 or 1).

**Acceptance Scenarios**:

1. **Given** a valid Defects4J project subset (e.g., 5 projects) is cloned, **When** the metric extraction script runs, **Then** a `features.csv` file is generated containing columns for Cyclomatic Complexity, Halstead Volume, LOC, and a binary "is_buggy" label for every analyzed Java file.
2. **Given** a project file contains no syntax errors, **When** the metric extractor processes it, **Then** the resulting metric values are numeric and non-null.
3. **Given** a file is part of a commit identified as a bug-fix, **When** the labeling logic runs, **Then** the corresponding row in the feature matrix is marked with `is_buggy = 1`.
4. **Given** a file is generated code or non-Java, **When** the metric extractor runs, **Then** the file is excluded from the matrix and the exclusion count is logged.

### User Story 2 - Correlation Analysis and Baseline Modeling (Priority: P2)

The system must calculate Point-Biserial and Spearman correlation coefficients between each individual complexity metric and the bug label, and train baseline classification models (Logistic Regression, Random Forest) using **Repeated 5-Fold Cross-Validation** (10 repeats, fixed seed) to establish performance baselines (ROC-AUC, F1-score).

**Why this priority**: This addresses the "which metrics exhibit the strongest correlation" part of the research question and establishes the baseline performance against which improvements or specific metric contributions are measured. Using Repeated CV ensures valid paired comparisons later.

**Independent Test**: The analysis script produces a report listing correlation coefficients (Point-Biserial and Spearman) for each metric and cross-validated performance scores (ROC-AUC) for the baseline models, without requiring external API calls or GPU resources.

**Acceptance Scenarios**:

1. **Given** the `features.csv` dataset, **When** the correlation analysis runs, **Then** a table is output showing the Point-Biserial correlation coefficient (r_pb), Spearman rank correlation (rho), and p-values for Cyclomatic Complexity, Halstead Volume, and LOC against the bug label.
2. **Given** the dataset is split into 5 folds repeated 10 times with a fixed seed, **When** the Logistic Regression model trains, **Then** the system outputs the mean ROC-AUC and standard deviation across all 50 folds.
3. **Given** the dataset is split into 5 folds repeated 10 times with a fixed seed, **When** the Random Forest model trains, **Then** the system outputs the mean ROC-AUC and standard deviation across all 50 folds.

### User Story 3 - Feature Importance and Statistical Significance Testing (Priority: P3)

The system must identify the relative importance of metrics in the trained Random Forest model and perform a **Paired Permutation Test** on the aggregated predictions from the Repeated 5-Fold CV to determine if the performance difference between the 'Full Metric Set' model and the 'Single Best Metric' model is statistically significant.

**Why this priority**: This provides the depth of analysis required to answer "why" certain metrics perform better and validates whether observed differences are real or due to chance, fulfilling the "statistically significant increase" expectation. The paired test is valid because the Repeated CV ensures identical test sets for both models.

**Independent Test**: The final report includes a ranked list of feature importances and a p-value from the Paired Permutation Test comparing model performances.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** the feature importance extraction runs, **Then** the metrics are ranked from highest to lowest contribution to prediction accuracy.
2. **Given** predictions from the 'Full Metric Set' model and the 'Single Best Metric' model on the same aggregated test instances (from Repeated CV), **When** the Paired Permutation Test runs, **Then** a p-value is generated indicating the statistical significance of the difference in performance.
3. **Given** the final results, **When** the visualization script runs, **Then** a bar chart is generated showing the ROC-AUC of each model and a table of correlation coefficients.

### Edge Cases

- **What happens when a project has zero buggy files?** The system must detect this class imbalance and either skip the project with a warning or apply a specific handling strategy (e.g., reporting that ROC-AUC is undefined for that subset) rather than crashing.
- **How does the system handle files with no complexity data (e.g., generated code)?** The system must exclude these files from the feature matrix and log the count of excluded files to ensure data integrity.
- **What happens if the Defects4J dataset version is incompatible?** The system must validate the dataset structure upon ingestion and fail gracefully with a clear error message if the expected directory structure or label format is missing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the Defects4J dataset (v2.0+) and select a subset of 5-10 Java projects such that the total raw data size fits within 7 GB RAM during preprocessing (See US-1).
- **FR-002**: System MUST calculate Cyclomatic Complexity, Halstead Volume, and Lines of Code for every Java source file using a **Java-compatible static analysis toolchain (e.g., PMD for Cyclomatic Complexity combined with a JavaParser-based custom script for Halstead Volume)** and store results in a structured matrix (See US-1).
- **FR-003**: System MUST label each file as "buggy" (1) or "clean" (0) based on the Defects4J commit history, ensuring the label corresponds to the specific file state at the time of the bug introduction (See US-1).
- **FR-004**: System MUST compute **Point-Biserial Correlation** and **Spearman Rank Correlation** between each individual metric and the target variable, outputting both the coefficient and the p-value (See US-2).
- **FR-005**: System MUST train Logistic Regression and Random Forest classifiers using **Repeated 5-Fold Cross-Validation (10 repeats, fixed seed)** and report mean ROC-AUC and F1-score with standard deviation (See US-2).
- **FR-006**: System MUST perform a **Paired Permutation Test** (or Bootstrapped Difference of ROC-AUC) to compare the classification performance of the 'Full Metric Set' model vs the 'Single Best Metric' model and report the statistical significance of the difference (See US-3).
- **FR-007**: System MUST extract and rank feature importance weights from the Random Forest model to identify the most predictive metrics (See US-3).

### Key Entities

- **CodeFile**: Represents a single Java source file, containing attributes for path, metrics (Cyclomatic Complexity, Halstead Volume, LOC), and the binary bug label.
- **ProjectSubset**: Represents the collection of 5-10 selected Java projects from Defects4J, including metadata on the total number of files and bug density.
- **ModelPerformance**: Represents the evaluation results of a trained classifier, containing metrics like ROC-AUC, F1-score, and standard deviation across folds.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation strength between individual metrics and bug presence is measured against the **Point-Biserial correlation coefficient (r_pb) and Spearman rank correlation (rho)** derived from the Defects4J dataset (See US-2).
- **SC-002**: Model predictive performance is measured against the ROC-AUC and F1-score metrics obtained from **Repeated 5-Fold Cross-Validation** on the selected project subset (See US-2).
- **SC-003**: The statistical significance of performance differences between models is measured against the p-value generated by the **Paired Permutation Test** on aggregated predictions (See US-3).
- **SC-004**: Feature contribution is measured against the normalized feature importance weights extracted from the trained Random Forest model (See US-3).
- **SC-005**: Computational feasibility is measured against the execution time and memory usage on a standard CPU-only CI runner (≤6 hours, ≤7 GB RAM) (See US-1).

## Assumptions

- **Assumption about dataset availability**: The Defects4J dataset (v2.0+) is accessible via the provided GitHub repository and contains the necessary labeled commits for the selected 5-10 projects.
- **Assumption about tool compatibility**: The selected toolchain (PMD + JavaParser-based script) is compatible with the Java versions used in the selected Defects4J projects and can successfully parse the source code without syntax errors.
- **Assumption about computational limits**: The selected subset of 5-10 projects will fit within the 7 GB RAM and 14 GB disk constraints of the GitHub Actions free-tier runner; if a project is too large, it will be excluded from the subset.
- **Assumption about statistical validity**: The sample size of files within the selected projects is sufficient to perform meaningful correlation tests and the Paired Permutation Test (p < 0.05) without requiring power analysis adjustments that would exceed the compute budget.
- **Assumption about metric independence**: While metrics like LOC and Cyclomatic Complexity may be correlated, the Random Forest model can handle this collinearity, and the feature importance analysis will reflect the joint contribution rather than claiming strict independence.