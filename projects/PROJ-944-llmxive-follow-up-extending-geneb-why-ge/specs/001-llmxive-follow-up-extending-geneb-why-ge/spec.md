# Feature Specification: llmXive follow-up: extending "GENEB: Why Genomic Models Are Hard to Compare"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-20  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'GENEB: Why Genomic Models Are Hard to Compare'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sequence Feature Extraction and Benchmark Loading (Priority: P1)

The researcher needs to automatically download the raw sequence data for the GENEB benchmark tasks and compute a standardized set of low-dimensional sequence statistics (e.g., k-mer entropy, GC-content variance) for each task using only CPU resources.

**Why this priority**: This is the foundational data layer. Without the feature matrix derived from raw sequences, no predictive modeling can occur. It validates the feasibility of extracting the required variables within the strict 7GB RAM and 6-hour CPU constraints.

**Independent Test**: The pipeline can be fully tested by running the extraction script on a representative subset of tasks and verifying the output CSV contains the expected numeric columns with no null values and completes within a reasonable timeframe on a standard 2-core CPU.

**Acceptance Scenarios**:

1. **Given** the GENEB benchmark repository is accessible, **When** the extraction script runs on a 2-core CPU with 7GB RAM, **Then** it must successfully compute a set of sequence features for a representative set of tasks and output a single CSV file without memory errors.
2. **Given** a specific task sequence is provided, **When** the script calculates nucleotide entropy, **Then** the result must be a single float value between and 2.0 (bits) consistent with standard information theory definitions.
3. **Given** the dataset is large, **When** the script processes tasks sequentially or in small batches, **Then** the total wall-clock time for feature extraction must remain within a practical, bounded duration to ensure efficient processing. (a strict sub-component budget to ensure sufficient time remains for modeling and analysis within the 6-hour total pipeline limit).

### User Story 2 - Sparse Regression Model Training and Validation (Priority: P2)

The researcher needs to train sparse regression models (Lasso/Elastic Net) and a small decision tree ensemble to predict the macro-MCC scores of genomic foundation models using only the extracted sequence features, and validate this prediction via 5-fold cross-validation.

**Why this priority**: This implements the core scientific hypothesis: that sequence statistics predict model performance. It transforms the data from Story 1 into the predictive capability required to identify "architectural niches."

**Independent Test**: The model training can be tested independently by running the training loop on a representative subset of tasks and verifying that the 5-fold cross-validation produces a Pearson correlation coefficient ($\rho$) and a Spearman rank correlation coefficient ($\rho_s$) and Mean Absolute Error (MAE) in the output logs.

**Acceptance Scenarios**:

1. **Given** the feature matrix and ground truth scores are loaded, **When** the Lasso regression model is trained with 5-fold cross-validation, **Then** the system must output a Pearson correlation coefficient ($\rho$), a Spearman rank correlation coefficient ($\rho_s$), and a Mean Absolute Error (MAE) for the held-out folds.
2. **Given** the training process runs, **When** the model converges, **Then** the total training time for the ensemble must not exceed 2 hours on a 2-core CPU.
3. **Given** a held-out task, **When** the trained model predicts its performance score, **Then** the predicted value must be a float within the range of valid MCC scores [-1, 1].

### User Story 3 - Architectural Niche Identification and Sensitivity Analysis (Priority: P3)

The researcher needs to analyze feature importance to identify which sequence properties correlate with specific architectures and perform a sensitivity analysis on the prediction threshold to ensure robustness.

**Why this priority**: This delivers the final scientific insight ("architectural niches") and satisfies the methodological requirement for threshold justification and sensitivity analysis, ensuring the findings are not artifacts of arbitrary cutoffs.

**Independent Test**: The analysis can be tested by generating a report that lists the top 3 predictive features for each architecture class and includes a table showing how prediction accuracy varies when the decision threshold is swept across a defined range.

**Acceptance Scenarios**:

1. **Given** the trained model coefficients, **When** the feature importance analysis runs, **Then** it must output a ranked list of the top 5 sequence features that most strongly predict performance for Transformer vs. Mamba architectures.
2. **Given** a decision threshold for "high performance" (e.g., predicted MCC > 0.6), **When** the sensitivity analysis sweeps the threshold over the set {0.5, 0.55, 0.6, 0.65, 0.7}, **Then** the system must report the variation in false-positive and false-negative rates for each threshold value, where the "true" label is derived from the actual macro-MCC score (thresholded at > 0.6).
3. **Given** the correlation results, **When** a permutation test is run with a sufficient number of iterations to ensure statistical robustness, **Then** the p-value must be calculated to verify if the observed correlation exceeds random chance.

### Edge Cases

- What happens if the GENEB benchmark repository is temporarily unavailable or the specific Zenodo accession numbers are missing? (System must retry with exponential backoff, then fail gracefully with a clear error log).
- How does the system handle tasks with extremely low sequence complexity (e.g., mononucleotide repeats) where entropy calculation might result in 0 or NaN? (System must substitute a floor value of a small positive constant to prevent division errors and flag the task in a diagnostic report).
- What happens if the cross-validation fold results in a model with near-zero variance in the target variable? (System must detect this condition and skip the permutation test for that specific fold to avoid infinite loops or division by zero).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download raw sequence data for the GENEB benchmark tasks and compute 15 specific sequence features (including nucleotide entropy, dinucleotide skew, and GC-content variance) for each task. (See US-1)
- **FR-002**: System MUST train at least two distinct regression models (Lasso/Elastic Net and a shallow Random Forest) to predict macro-MCC scores using only the computed sequence features. (See US-2)
- **FR-003**: System MUST perform 5-fold cross-validation to evaluate model performance and output Pearson correlation coefficients ($\rho$), Spearman rank correlation coefficients ($\rho_s$), and Mean Absolute Error (MAE) for each fold. (See US-2)
- **FR-004**: System MUST execute a permutation test (minimum 1,000 iterations) on the final correlation coefficient to determine statistical significance against a null hypothesis. (See US-3)
- **FR-005**: System MUST perform a sensitivity analysis on any decision threshold used to classify "architectural niches" by sweeping the threshold over a range of plausible values and reporting the resulting variation in error rates. (See US-3)
- **FR-006**: System MUST ensure the entire pipeline (extraction, training, validation, analysis) completes within 6 hours on a 2-core CPU with 7GB RAM, utilizing no GPU acceleration. (See US-1)

### Key Entities

- **TaskDefinition**: Represents a single biological task in the GENEB benchmark, containing the raw sequence data and the ground truth macro-MCC scores for all evaluated models.
- **SequenceFeatureSet**: A vector of 15 numeric values derived from a TaskDefinition, representing low-dimensional descriptors like k-mer entropy and repeat density.
- **PerformancePrediction**: The output of the regression model, representing the predicted macro-MCC score for a specific model architecture on a given task.
- **SensitivityReport**: A data structure containing the error rates (false-positive/false-negative) calculated at each step of the threshold sweep.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Pearson correlation coefficient ($\rho$) and Spearman rank correlation coefficient ($\rho_s$) between predicted and actual model performance are measured against the hypothesis of $\rho > 0.6$ (or $\rho_s > 0.6$) on held-out tasks, with the understanding that small sample sizes may yield high variance in these estimates. (See US-2)
- **SC-002**: The computational feasibility is measured against the constraint of a limited total wall-clock time on a 2-core CPU with 7GB RAM; the system passes if the total time is ≤ 6 hours. (See US-1)
- **SC-003**: The statistical significance of the predictive power is measured against a p-value threshold of < 0.05 derived from the permutation test. (See US-3)
- **SC-004**: The robustness of the architectural niche identification is measured against the variation in false-positive and false-negative rates across the threshold sweep {0.5, 0.55, 0.6, 0.65, 0.7}; the system passes if the maximum variation in error rates across this sweep is ≤ 10%. (See US-3)
- **SC-005**: The methodological validity is measured by the successful execution of a permutation test to rule out overfitting on the small dataset. (See US-3)

## Assumptions

- **Assumption about data availability**: The GENEB benchmark repository (or the associated Zenodo/NCBI accession numbers) remains accessible via public HTTP/HTTPS endpoints, and the raw sequence data for all tasks can be downloaded within the 6-hour time budget.
- **Assumption about computational constraints**: A set of tasks and the resulting feature matrix will comfortably fit within the 7GB RAM limit, and the sparse regression models will train within the allocated time on a standard 2-core CPU without requiring GPU acceleration.
- **Assumption about methodological framing**: Since the study is observational (no random assignment of sequences to models), all findings regarding the relationship between sequence statistics and model performance will be framed as associational rather than causal.
- **Assumption about threshold justification**: The decision threshold for classifying "high performance" (e.g., MCC > 0.6) is based on community standards for genomic model evaluation, and the sensitivity analysis will be sufficient to demonstrate that minor variations in this threshold do not alter the primary conclusions about architectural niches.
- **Assumption about variable fit**: A set of selected sequence features (k-mer entropy, GC-content, etc.) is sufficient to capture the "difficulty profile" of the tasks as described in the GENEB paper; if the dataset lacks a specific variable required for a specific architectural class, this will be flagged as a limitation rather than a failure of the pipeline.
- **Assumption about ground truth independence**: The ground truth macro-MCC scores are calculated on held-out sequences independent of the input sequence features used for prediction, ensuring the correlation is not a trivial mathematical artifact (e.g., if MCC is calculated on a fixed-length window and features are global, independence is maintained).
- **Assumption about sensitivity analysis scope**: The sensitivity analysis tests the stability of the *prediction model's* thresholding behavior (how predicted labels change with threshold) rather than the biological validity of the niche, using the actual MCC score as the ground truth for classification.
- **Assumption about small sample variance**: The use of both Pearson and Spearman correlation coefficients is intended to mitigate the high variance expected from the small sample size (a limited set of tasks), and the results will be interpreted with this limitation in mind.