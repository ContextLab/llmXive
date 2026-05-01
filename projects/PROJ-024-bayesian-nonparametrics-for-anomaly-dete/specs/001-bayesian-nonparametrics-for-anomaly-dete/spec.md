# Feature Specification: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Feature Branch**: `001-bayesian-nonparametrics-anomaly-detection`  
**Created**: 2024-01-15  
**Status**: Ready for Review  
**Input**: User description: "Can a Dirichlet process Gaussian mixture model (DPGMM), updated incrementally with each new observation, effectively detect anomalies in univariate time series without assuming a fixed number of latent states?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core DPGMM Implementation with Streaming Updates (Priority: P1)

As a computational statistics researcher, I want to implement an incremental DPGMM that processes time series observations one at a time, so that I can detect anomalies in streaming data without assuming a fixed number of latent states.

**Why this priority**: This is the foundational capability without which the entire research question cannot be answered. The incremental update mechanism is the core innovation distinguishing this approach from batch methods.

**Independent Test**: Can be fully tested by processing a synthetic time series with known anomaly points and verifying that the model produces anomaly scores without requiring batch retraining.

**Acceptance Scenarios**:

1. **Given** a univariate time series dataset with labeled anomalies, **When** the DPGMM processes observations sequentially using stick-breaking construction, **Then** it produces anomaly scores for each point without batch retraining
2. **Given** the model is configured with ADVI variational inference, **When** memory usage is profiled during processing of 1000 observations, **Then** memory consumption stays under 7GB RAM limit
3. **Given** a new observation arrives, **When** the posterior mixture weights are updated, **Then** the model maintains probabilistic uncertainty estimates for anomaly scoring

---

### User Story 2 - Baseline Comparison and Performance Evaluation (Priority: P2)

As a computational statistics researcher, I want to compare the DPGMM detector against ARIMA, moving average, and LSTM Autoencoder baselines on public benchmarks, so that I can validate whether the Bayesian nonparametric approach achieves comparable or superior F1-scores with fewer hyperparameters.

**Why this priority**: Validation against established baselines is required to demonstrate the value of the proposed approach. Without comparison, the research contribution cannot be assessed.

**Independent Test**: Can be fully tested by running all three models on a single UCI dataset and generating precision-recall curves with F1-score measurements.

**Acceptance Scenarios**:

1. **Given** a UCI time series dataset (e.g., Electricity, Traffic, or Synthetic Control Chart), **When** ARIMA, moving average with z-score, LSTM Autoencoder, and DPGMM are all trained and evaluated, **Then** F1-scores are computed for each method using the same test split
2. **Given** multiple datasets have been evaluated, **When** paired t-tests are performed on F1-scores across datasets, **Then** Bonferroni correction is applied for multiple comparisons
3. **Given** the DPGMM produces anomaly scores, **When** ROC and PR curves are generated, **Then** figures are saved as PNG files for reproducibility

---

### User Story 3 - Anomaly Score Threshold Calibration (Priority: P3)

As a computational statistics researcher, I want to calibrate the posterior probability threshold for anomaly flagging without labeled data, so that the method can be deployed in real-world streaming scenarios where ground truth is unavailable.

**Why this priority**: This enables practical deployment but is secondary to demonstrating the core detection capability. The research can proceed without this, though it adds significant practical value.

**Independent Test**: Can be fully tested by running the model on unlabeled data and verifying that the adaptive threshold produces reasonable anomaly rates based on statistical properties of the scores.

**Acceptance Scenarios**:

1. **Given** anomaly scores from the DPGMM on unlabeled data, **When** an adaptive threshold is computed based on score distribution, **Then** the flagged anomaly rate is within expected bounds for the dataset
2. **Given** a configured threshold, **When** the model flags points as anomalies, **Then** the decision boundary is documented in config.yaml for replication
3. **Given** different datasets, **When** threshold calibration is attempted, **Then** the method requires no labeled data to produce reasonable thresholds

---

## Edge Cases

- What happens when a time series has extremely low variance (near-constant values) that could cause numerical instability in the Gaussian mixture components?
- How does the system handle missing values in the time series that break the streaming update assumption? **System must skip missing values and log warning; streaming update continues with next valid observation.**
- What happens when the Dirichlet process concentration parameter results in too many or too few mixture components for the data complexity?
- How does the system handle datasets where anomalies occur in clusters rather than as isolated points?
- What happens when runtime exceeds the 30-minute target per dataset on GitHub Actions? **System must log timeout warning, save partial results, and trigger GitHub Actions retry with exponential backoff.**
- **How does the system prevent temporal data leakage via explicit time-ordered train/test splits for streaming time series data?**

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement a Dirichlet process Gaussian mixture model with stick-breaking construction for univariate time series
- **FR-002**: System MUST update the DPGMM posterior incrementally after each new observation in streaming mode
- **FR-003**: System MUST compute anomaly scores as negative log posterior probability for each test point
- **FR-004**: System MUST flag observations as anomalies when scores exceed an adaptive threshold
- **FR-005**: System MUST maintain memory usage under 7GB during processing using variational inference (ADVI)
- **FR-006**: System MUST generate confusion matrices, ROC curves, and PR curves for evaluation
- **FR-007**: Users MUST be able to download 3-5 univariate time series datasets from UCI Machine Learning Repository using wget/curl
- **FR-008**: System MUST enforce type safety via mypy strict mode with zero type errors for all public APIs
- **FR-009**: config.yaml size MUST remain under 2KB. **Validation: config.yaml size must be verified via `os.path.getsize()` before each run; if size exceeds 2048 bytes, system must exit with error code 1 and log violation. Initial config.yaml creation must ensure size stays under 2KB; derived statistics must be stored in state files, not config.yaml.**

## Key Entities

- **TimeSeries**: Represents a univariate time series with observations, timestamps, and optional anomaly labels
- **DPGMMModel**: Represents the Dirichlet process Gaussian mixture model with mixture weights, component parameters, and concentration parameter
- **AnomalyScore**: Represents the negative log posterior probability computed for each observation
- **EvaluationMetrics**: Contains F1-scores, precision, recall, and AUC values for model comparison

## Service Interfaces *(mandatory for T086/T087)*

### anomaly_detector.py Interface

**Class**: `AnomalyDetectorService`

**Methods**:
- `__init__(config: Dict, model_path: str)`: Initialize with configuration and model checkpoint path
- `load_model() -> DPGMMModel`: Load DPGMM model from checkpoint
- `process_stream(observations: List[float]) -> List[AnomalyScore]`: Process observations sequentially, return anomaly scores
- `update_model(observation: float) -> None`: Incrementally update model posterior with single observation
- `compute_score(observation: float) -> AnomalyScore`: Compute anomaly score for single observation
- `get_uncertainty(observation: float) -> Dict[str, float]`: Return probabilistic uncertainty estimates
- `save_checkpoint(path: str) -> None`: Save current model state to checkpoint

**Dependencies**: `DPGMMModel` from `models/dpgmm.py`, `AnomalyScore` from `models/anomaly_score.py`

**Interface Verification**: All 7 methods MUST be implemented and verified via contract tests in `code/tests/contract/test_anomaly_detector_schema.py`

### threshold_calibrator.py Interface

**Class**: `ThresholdCalibratorService`

**Methods**:
- `__init__(config: Dict, threshold_method: str = "percentile_95")`: Initialize with configuration and calibration method
- `calibrate(scores: List[float]) -> float`: Compute adaptive threshold from score distribution
- `validate_threshold(threshold: float, scores: List[float]) -> Dict[str, float]`: Validate threshold produces expected anomaly rates
- `get_decision_boundary() -> float`: Return current threshold value
- `update_decision_boundary(new_threshold: float) -> None`: Update threshold in config
- `compute_expected_bounds(dataset_name: str) -> Tuple[float, float]`: Return expected anomaly rate bounds for dataset

**Dependencies**: `config.yaml` for threshold method configuration, `data-dictionary.md` for expected bounds

**Interface Verification**: All 6 methods MUST be implemented and verified via contract tests in `code/tests/contract/test_threshold_calibrator_schema.py`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: DPGMM achieves F1-score within 5% of baseline methods (ARIMA, moving average, LSTM-AE) on at least 3 UCI datasets
- **SC-002**: Memory usage remains under 7GB when processing 1000 observations per dataset
- **SC-003**: Runtime per dataset does not exceed 30 minutes on GitHub Actions infrastructure
- **SC-004**: Model requires fewer hyperparameters than baseline methods (at least 30% reduction in tunable parameters). **Definition: Tunable parameters include learning rate, concentration parameter, number of initial components, and prior hyperparameters. Baseline methods count ARIMA order parameters (p,d,q) and LSTM hidden layer sizes.**
- **SC-005**: Precision-recall curves are generated and saved for all evaluated datasets

## Assumptions

- UCI Machine Learning Repository datasets are accessible and contain labeled anomalies for evaluation
- PyMC or Stan with ADVI variational inference provides sufficient accuracy within memory constraints
- GitHub Actions infrastructure supports Python environment with required dependencies (pymc, statsmodels, scikit-learn, torch)
- Time series datasets are univariate; multivariate extensions are out of scope for this feature
- Labeled anomaly data is available for at least 3 of the selected UCI datasets for F1-score calculation
- Network connectivity is available for downloading datasets via wget/curl
- **Prioritize UCI Electricity, Traffic, and Synthetic Control Chart datasets for real-world benchmarks, all three being from UCI Machine Learning Repository to satisfy SC-001 requirement for at least 3 UCI datasets.**
- **UCI Electricity dataset URL: https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014**
- **UCI Traffic dataset URL: https://archive.ics.uci.edu/ml/datasets/PEMS-Traffic**
- **UCI Synthetic Control Chart dataset URL: https://archive.ics.uci.edu/ml/datasets/Synthetic+Control+Chart+Time+Series**
- **LSTM Autoencoder baseline was added during Phase 6 creativity review (T090) to ensure modern baseline comparison per research-stage feedback**
- **config.yaml size MUST remain under 2KB per FR-009 from initial creation; derived statistics must be stored in state files**
- **code/scripts/ directory will contain executable validation and utility scripts**
- **logs/elbo/ directory will store ELBO convergence logs for ADVI variational inference**
- Comparable performance is defined as F1-score within 5% of baseline methods, as specified in Success Criterion SC-001.
- **Adaptive threshold shall be computed using the 95th percentile of the anomaly score distribution on a validation split, a common practice for unsupervised anomaly scoring. Expected bounds for anomaly rates: 1-5% for normal datasets, 5-15% for anomaly-heavy datasets, as documented in data-dictionary.md.**
- **LICENSE: MIT License (MIT) selected per open-source research library best practices.**
- **PII scanning: System uses `bandit` for code PII patterns and `trufflehog` for credential scanning in data files, as required by Constitution Principle III.**
- **ELBO convergence criteria: Model training stops when ELBO improvement <0.001 for 50 consecutive iterations or after 500 maximum iterations, per Constitution Principle VI.**
- **Dataset selection criteria: Synthetic Control Chart replaced PEMS-SF because PEMS-SF is from PEMS project (not UCI Machine Learning Repository), violating SC-001 requirement for UCI datasets. Selection documented in data-dictionary.md.**
- **Data license documentation: All UCI dataset licenses MUST be documented in data-dictionary.md with exact license text, attribution requirements, and usage restrictions per Constitution Principle III.**
- **Test coverage requirement: All public APIs must have ≥80% line coverage as documented in code/tests/README.md and verified by coverage reports in CI pipeline.**
- **Parallel execution verification: Each [P] task must have corresponding `verify_parallel_safety.py` script in code/scripts/ that confirms no file conflicts between parallel tasks.**
- **Service interface contract tests: All service interfaces (AnomalyDetectorService, ThresholdCalibratorService) MUST have dedicated contract tests per spec.md Service Interfaces section.**