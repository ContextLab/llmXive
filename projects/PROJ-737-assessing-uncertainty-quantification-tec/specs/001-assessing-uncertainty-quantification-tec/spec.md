# Feature Specification: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

**Feature Branch**: `001-assessing-uq-techniques`  
**Created**: 2026-06-19  
**Status**: Draft  
**Input**: User description: "How do Gaussian‑process regression, Monte‑Carlo dropout, deep ensembles, and conformal prediction differ in calibration error and prediction‑interval sharpness when applied to machine‑learning models that predict materials properties such as elastic modulus, band gap, and thermal conductivity?"

## User Scenarios & Testing

### User Story 1 - Reproducible UQ Pipeline Execution (Priority: P1)

**Journey**: A researcher initiates the analysis workflow to evaluate four distinct uncertainty quantification (UQ) methods (GPR, MC Dropout, Deep Ensembles, Conformal Prediction) against three materials property datasets (Elastic Modulus, Band Gap, Thermal Conductivity) using a single orchestrated script.

**Why this priority**: Without a functioning pipeline that ingests data, trains baseline models, applies UQ techniques, and generates metrics, no comparison is possible. This is the foundational capability.

**Independent Test**: The system can be tested by running the orchestration script on a subset of the data; if it completes without error and outputs the required metric files (Calibration Error, interval width), the story is complete.

**Acceptance Scenarios**:

1. **Given** the three materials datasets (Materials Project, OQMD, AFLOW) are accessible and pre-processed, **When** the orchestration script is executed on a CPU-only runner (2 CPU, ≤2 GB RAM), **Then** the script must complete all training, inference, and evaluation steps within 1 hour and output a summary CSV containing Calibration Error and interval width for all method-dataset combinations.
2. **Given** the script is executed, **When** any of the four UQ methods fails to converge or crashes, **Then** the system must log the specific error, skip the failed method for that dataset, and continue processing the remaining methods to ensure partial results are available.

### User Story 2 - Calibration and Sharpness Metric Calculation (Priority: P2)

**Journey**: A data scientist analyzes the output to determine which UQ method provides the best trade-off between calibration error (reliability) and prediction interval sharpness (precision) for specific property classes.

**Why this priority**: The core research question hinges on the ability to quantify and compare these two specific metrics. Without accurate calculation, the scientific comparison is invalid.

**Independent Test**: The system can be tested by feeding synthetic data with known ground-truth intervals and verifying that the calculated Calibration Error and average interval width match theoretical expectations.

**Acceptance Scenarios**:

1. **Given** a set of test predictions with associated prediction intervals and ground-truth values, **When** the evaluation module calculates the Calibration Error, **Then** it must compute the absolute deviation of the observed coverage from the nominal coverage (e.g., |Observed Coverage - Nominal Level|) for each nominal level, reporting this as a scalar value.
2. **Given** the same test predictions, **When** the evaluation module calculates sharpness, **Then** it must compute the mean width of the prediction intervals across the test set, reporting this as a scalar value in the same units as the predicted property.

### User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Journey**: A researcher validates that observed differences between UQ methods are statistically significant and robust to threshold choices, ensuring the findings are not due to random noise or arbitrary cutoffs.

**Why this priority**: This addresses methodological soundness (multiplicity, power, threshold justification) required for the research to be publishable and defensible.

**Independent Test**: The system can be tested by running the statistical analysis module on the generated metrics; it must output p-values for pairwise comparisons and a sensitivity report showing how metrics vary across a swept threshold.

**Acceptance Scenarios**:

1. **Given** the Calibration Error and sharpness metrics for all four methods across the three datasets, **When** the statistical analysis module runs, **Then** it must perform independent-sample statistical significance testing (Welch's t-test or Mann-Whitney U test) between all method pairs *within each dataset*, reporting a p-value at α=0.05. This test is appropriate because the methods are trained independently with distinct architectures, producing independent samples. Additionally, the system must report the range and standard deviation of the metrics across the three datasets to assess consistency, as an ANOVA F-test is statistically invalid with only N=3 data points.
2. **Given** the conformal prediction method uses a specific nominal coverage level, **When** the sensitivity analysis runs, **Then** it must re-calculate the prediction intervals for representative coverage levels, and report the resulting change in average interval width and observed coverage error for each level.

### Edge Cases

- **Data Scarcity**: What happens if a specific materials property dataset (e.g., Thermal Conductivity) has a limited number of samples after splitting? The system must either downsample the other datasets to match or flag the comparison as statistically underpowered.
- **Convergence Failure**: How does the system handle Gaussian Process Regression failing to converge on a high-dimensional feature set? The system must catch the exception, log the feature dimensionality, and substitute a kernel approximation or skip the method for that specific dataset.
- **Memory Overflow**: How does the system handle Deep Ensembles (multiple models) exceeding the 2 GB RAM limit on the GitHub runner? The system must implement a fallback to process datasets in smaller batches or reduce the ensemble size to a minimal subset of models, recording this deviation in the assumptions log.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess composition/structure features from Materials Project (elastic modulus), OQMD (band gap), and AFLOW (thermal conductivity) using `matminer` featurizers, ensuring a stratified train/validation/test split by property range. (See US-1)
- **FR-002**: System MUST implement four distinct UQ methods: (1) GPR as a standalone model replacing the baseline, (2) MC Dropout with multiple stochastic passes applied to the baseline model, (3) Deep Ensembles with multiple models applied to the baseline model, and (4) Split-Conformal Prediction applied to the baseline model. The baseline model must be XGBoost or CGCNN (≤2M parameters). (See US-1)
- **FR-003**: System MUST calculate Calibration Error (absolute deviation of observed coverage from nominal coverage) and average prediction interval width (sharpness) for all test predictions generated by the four UQ methods. (See US-2)
- **FR-004**: System MUST perform independent-sample statistical significance testing (Welch's t-test or Mann-Whitney U test) on Calibration Error and sharpness metrics *within each dataset*, applying α=0.05. This test is mandated because the UQ methods are trained independently with different architectures, resulting in independent samples. The system must NOT use paired tests (e.g., Wilcoxon signed-rank) for cross-method comparisons. (See US-3)
- **FR-005**: System MUST execute a sensitivity analysis sweeping the conformal prediction nominal coverage threshold across a range of high-confidence levels and report the resulting variation in interval width and coverage error. (See US-3)

### Key Entities

- **MaterialsDataset**: Represents a specific property dataset (e.g., Elastic Modulus) containing features, ground-truth values, and split indices.
- **UQMethod**: Represents an uncertainty quantification technique (GPR, MC Dropout, etc.) with its specific hyperparameters and execution state.
- **EvaluationMetric**: A record containing the dataset name, UQ method, metric type (Calibration Error, Width), and the calculated scalar value.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The difference in Calibration Error between the best and worst performing UQ methods is measured against the statistical significance threshold (α = 0.05) using an independent-sample test (Welch's t-test or Mann-Whitney U) to test for differences. (See US-3)
- **SC-002**: The average prediction interval width (sharpness) for each UQ method is measured against the nominal coverage target to assess the efficiency of the intervals (i.e., are they unnecessarily wide?). (See US-2)
- **SC-003**: The computational cost (training + inference time) of each UQ method is measured against a fixed execution limit of the GitHub Actions runner to verify CPU-only feasibility. (See US-1)
- **SC-004**: The sensitivity of the conformal prediction intervals to threshold changes is measured by calculating the percentage change in interval width when the coverage target is swept across a representative range. (See US-3)
- **SC-005**: The consistency of results across the three distinct materials datasets (Elastic Modulus, Band Gap, Thermal Conductivity) is measured by reporting the range and standard deviation of the metrics, as an ANOVA F-test is statistically invalid with N=3. (See US-3)

## Assumptions

- The `matminer` library and the specific datasets (Materials Project, OQMD, AFLOW) are accessible via public APIs or direct downloads without requiring paid institutional credentials during the CI run.
- The baseline Graph Neural Network (CGCNN) or Gradient Boosting model (XGBoost) can be trained on the available ~2 GB RAM by limiting the dataset size to ≤10,000 samples if necessary, as the original idea implies a "sampled dataset" for CPU feasibility.
- The "small" GNN (≤2M parameters) and the Ensemble modeling

The research question remains: How can an ensemble of multiple models improve predictive robustness compared to individual models? The method involves aggregating predictions from a diverse set of models to reduce variance and bias, as detailed in Breiman (1996) and Wolpert (1992). can fit within the memory constraints of a standard GitHub Actions runner (CPU, moderate RAM) without requiring GPU acceleration or 8-bit quantization.
- The datasets provided by the sources contain the necessary composition and structure descriptors to compute the required features; if a specific variable (e.g., specific crystal structure metadata) is missing, the system will use the nearest available proxy descriptor.
- The statistical power is sufficient to detect medium effect sizes with the available sample sizes; if a dataset is too small (<100 test samples), the statistical significance test will be flagged as inconclusive rather than failing.
- The conformal prediction sensitivity analysis will sweep the threshold by absolute steps of a small increment (e.g., a series of closely spaced values) as a computationally trivial approximation to justify the choice of the target.