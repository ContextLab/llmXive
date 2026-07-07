# Feature Specification: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

**Feature Branch**: `001-assess-uncertainty-quantification`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Model Training and UQ Application (Priority: P1)

The researcher needs to train a baseline feed-forward neural network on a subset of the Materials Project dataset and apply three distinct lightweight uncertainty quantification (UQ) techniques (Deep Ensembles, Monte-Carlo Dropout, and Sparse Gaussian Process) to generate predictive means and variance estimates for material properties.

**Why this priority**: This is the foundational step. Without generating the uncertainty estimates from the three methods, no calibration or downstream screening analysis can occur. It establishes the core data pipeline.

**Independent Test**: The system can be tested by verifying that the pipeline successfully ingests the Materials Project subset, trains the baseline model, runs the three UQ inference passes, and outputs a structured dataset containing (prediction, lower_bound, upper_bound, variance) for each test sample without runtime errors on a CPU-only environment.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset of [deferred] inorganic compounds with compositional and structural features, **When** the training pipeline executes, **Then** a baseline model (2 hidden layers, ≤10k parameters) is trained on [deferred] of the data using a stratified random split with seed=42, and three UQ variants (5-ensemble, MC-dropout p=0.2, sparse GP with 500 inducing points) are fitted on the training split.
2. **Given** the trained models and a held-out [deferred] test set, **When** inference is performed, **Then** the system outputs a CSV containing predictions and uncertainty intervals (50% and 90% confidence levels) for every test sample, with a total wall-clock time for training and inference ≤ 5 hours on a 2-core CPU runner.

---

### User Story 2 - Calibration and Reliability Evaluation (Priority: P2)

The researcher needs to evaluate how well the predicted uncertainty intervals match the empirical error distribution using reliability diagrams, Expected Calibration Error (ECE), and proper interval scores to rank the three methods.

**Why this priority**: This directly answers the primary research question ("How accurately do... methods capture predictive uncertainty?"). It transforms raw predictions into a comparative ranking of method performance.

**Independent Test**: The system can be tested by calculating calibration metrics (ECE, Interval Score, Sharpness) for each method and verifying that the outputs align with theoretical expectations (e.g., a perfectly calibrated [deferred] interval covers [deferred] of true values), producing a ranked list of methods based on ECE.

**Acceptance Scenarios**:

1. **Given** the UQ predictions and ground-truth values from User Story 1, **When** the evaluation module runs, **Then** it generates reliability diagrams and computes the Expected Calibration Error (ECE) for 50% and 90% confidence intervals for all three methods.
2. **Given** the computed metrics, **When** the ranking logic executes, **Then** the method with the lowest ECE and best interval score is identified as the "best-performing" technique, and the results are reported with a clear distinction between aleatoric and epistemic uncertainty (output column 'uncertainty_type') where applicable.

---

### User Story 3 - Downstream Screening Case Study (Priority: P3)

The researcher needs to demonstrate the practical utility of the best-performing UQ method by applying it to a downstream screening task (e.g., selecting stable perovskites) and comparing selection precision against a baseline that uses only point predictions.

**Why this priority**: This validates the "Motivation" of the project—showing that reliable UQ actually improves decision-making in high-throughput screening, moving beyond abstract metrics to domain-relevant utility.

**Independent Test**: The system can be tested by simulating a screening workflow where candidates are filtered based on high-confidence intervals and verifying that the precision of selected candidates is higher (or recall is maintained at higher precision) compared to a point-prediction-only baseline.

**Acceptance Scenarios**:

1. **Given** the ranked UQ methods and a target property (e.g., formation energy) with a stability threshold, **When** a screening filter is applied using the "best-performing" UQ method (filtering for narrow confidence intervals), **Then** the precision of selected candidates is calculated and compared to the precision of the same selection made using only point predictions.
2. **Given** a fixed recall target (e.g., [deferred] of stable materials), **When** the screening process is run, **Then** the UQ-enhanced method yields a precision at least 5% higher than the point-prediction baseline (or a p-value < 0.05 from McNemar's test), demonstrating the value of uncertainty filtering.

---

### Edge Cases

- What happens when the Materials Project dataset download fails or the file is corrupted? (System must retry up to 3 times with exponential backoff, then fail gracefully with a clear error code).
- How does the system handle materials with missing structural descriptors (e.g., undefined packing fraction)? (Rows with missing critical features are excluded from training/test sets, and a JSON log 'validation_report.json' is generated with the count of excluded samples).
- How does the system behave if the Gaussian Process optimization fails to converge on the sparse inducing points? (The system falls back to a standard GP with full inducing points or logs a warning and proceeds with the Deep Ensemble/MC-Dropout results only).
- What if the total runtime exceeds the 6-hour GitHub Actions limit during the Deep Ensemble training? (The system must enforce a hard time budget of 5 hours for the entire pipeline (training + eval) to ensure a 45-minute safety buffer for CI overhead, failing with a clear timeout error if exceeded).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the Materials Project bulk dataset ([deferred] compounds) to extract compositional features and structural descriptors, ensuring all required variables (formation energy, bulk modulus, band gap) are present (See US-1).
- **FR-002**: System MUST implement a baseline feed-forward neural network with exactly 2 hidden layers and ≤10,000 parameters, trained on an 80/10/10 split of the data (See US-1).
- **FR-003**: System MUST implement Deep Ensemble averaging by training 5 independently initialized copies of the baseline model and aggregating predictions to estimate mean and variance (See US-1).
- **FR-004**: System MUST implement Monte-Carlo Dropout by enabling dropout (p=0.2) during inference and drawing 30 stochastic forward passes per sample to estimate predictive variance (See US-1).
- **FR-005**: System MUST implement Sparse Gaussian Process regression using GPyTorch with 500 inducing points on the same feature set, AFTER applying PCA to reduce features to 20 components, to provide a third UQ baseline (See US-1).
- **FR-006**: System MUST compute Expected Calibration Error (ECE), proper interval scores, and mean interval width (sharpness) for 50% and 90% confidence intervals for all three methods to enable comparative ranking (See US-2).
- **FR-007**: System MUST perform a downstream screening case study comparing selection precision of stable candidates using UQ-based filtering versus point-prediction-only filtering (See US-3).
- **FR-008**: System MUST separate aleatoric and epistemic uncertainty components where the method allows: for Deep Ensembles and MC-Dropout, Epistemic variance = variance of means across samples, Aleatoric variance = mean of predicted variances; for Sparse GP, report total variance as a proxy (See US-2).
- **FR-009**: System MUST enforce a hard runtime limit of 5 hours for the entire pipeline (training + evaluation) on a CPU-only runner, failing with a clear timeout error if exceeded (See US-1, US-2).
- **FR-010**: System MUST handle dataset variable gaps by excluding rows with missing critical features and generating a JSON log file 'validation_report.json' containing the count of excluded rows and a list of missing variable names (See US-1).

### Key Entities

- **MaterialSample**: Represents a single inorganic compound; attributes include composition (element fractions), structural descriptors (radius, packing), and target properties (energy, modulus).
- **UQPrediction**: Represents the output of a UQ method; attributes include point prediction, predictive mean, predictive variance, lower bound ([deferred]/90%), upper bound ([deferred]/90%), and method identifier.
- **CalibrationMetric**: Represents evaluation results; attributes include method name, ECE score, interval score, sharpness (mean width), and coverage percentage for specific confidence levels.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Calibration accuracy is measured by the Expected Calibration Error (ECE) and mean interval width (sharpness) of the [deferred] and [deferred] prediction intervals against the empirical coverage rate on the held-out test set (See US-2).
- **SC-002**: Computational efficiency is measured by the total wall-clock time of the training and inference pipeline against the 5-hour limit on a 2-core CPU runner (See US-1).
- **SC-003**: Screening utility is measured by the precision of candidate selection at a fixed recall level (e.g., [deferred]) when using the best UQ method versus the point-prediction baseline (See US-3).
- **SC-004**: Methodological robustness is measured by the consistency of uncertainty estimates across different random seeds (for ensembles) or inducing point initializations (for GP) to ensure results are not artifacts of specific initialization, defined as the coefficient of variation (CV) of ECE scores across 3 seeds must be ≤ 0.05 (See US-2).
- **SC-005**: Data validity is measured by the percentage of rows with null values in target columns extracted from the Materials Project dataset (See US-1).

## Assumptions

- The Materials Project bulk download URL (`https://materialsproject.org/open`) remains accessible and provides a static snapshot of [deferred] compounds containing the necessary compositional and structural features without requiring an API key for the subset used.
- The "lightweight" definition of the neural network (2 hidden layers, ≤10k parameters) is sufficient to model the non-linear relationships in the [deferred]-sample dataset without overfitting, given the regularization provided by dropout and early stopping.
- The sparse Gaussian Process implementation with 500 inducing points provides a sufficient approximation of the full GP to capture the uncertainty landscape within the 5-hour compute budget on CPU, provided PCA is applied for dimensionality reduction.
- The 2-core CPU, 7GB RAM environment of the GitHub Actions free tier is adequate to hold the feature matrix (a moderate number of rows × ~20 features) and the intermediate model states in memory without swapping.
- The 2022 paper on aleatoric/epistemic separation provides a valid, computationally tract metric for decomposing uncertainty that can be applied to the neural network outputs without requiring full Bayesian inference.
- The downstream screening task (perovskite stability) can be approximated using the available formation energy and band gap data without requiring additional, unlisted crystallographic constraints.
- The 5-hour runtime limit is a necessary relaxation from the idea's implied 30/20 min targets to accommodate the full 3-method comparison and evaluation on a CPU, ensuring scientific rigor while remaining within CI limits.