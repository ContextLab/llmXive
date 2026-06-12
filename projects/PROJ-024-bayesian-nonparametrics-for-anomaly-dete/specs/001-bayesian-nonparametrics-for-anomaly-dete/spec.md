# Specification: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Project ID**: PROJ-024  
**Version**: 1.0.0  
**Status**: specified  
**Constitution**: Principles I-VIII apply

## User Scenarios & Testing

### User Story 1 - DPGMM Model Training and Streaming Inference (Priority: P1)

The system MUST train a Dirichlet Process Gaussian Mixture Model on historical time series data and process new observations incrementally to detect anomalies in real-time streaming scenarios.

**Why this priority**: Core research functionality; without model training and streaming inference, no anomaly detection is possible.

**Independent Test**: Can be fully tested by loading a synthetic dataset, training the model, and verifying anomaly scores are produced for each observation with ELBO convergence logged.

**Acceptance Scenarios**:

1. **Given** a synthetic time series dataset with ≥1000 observations, **When** the model trains for ≤500 iterations, **Then** ELBO converges with delta<0.01 for 10 consecutive iterations
2. **Given** a trained DPGMM model, **When** processing a new observation, **Then** an anomaly score is returned within 60 seconds
3. **Given** streaming mode enabled, **When** calling update_model(), **Then** posterior is updated incrementally without full retraining

---

### User Story 2 - Baseline Comparison and Evaluation Metrics (Priority: P2)

The system MUST compute evaluation metrics (F1, precision, recall, AUC-ROC) against baseline methods and compare performance across multiple datasets.

**Why this priority**: Required for scientific validation; enables quantitative comparison with existing methods.

**Independent Test**: Can be fully tested by running evaluation on Electricity, Traffic, and Synthetic Control datasets and verifying metrics are computed and stored.

**Acceptance Scenarios**:

1. **Given** labeled test data with ground truth anomalies, **When** computing F1/precision/recall, **Then** metrics are stored in EvaluationMetrics schema
2. **Given** multiple datasets, **When** comparing baselines, **Then** Wilcoxon signed-rank test is performed with bootstrap confidence intervals (n=10000 iterations)

---

### User Story 3 - Unsupervised Threshold Calibration (Priority: P3)

The system MUST calibrate anomaly detection thresholds using unsupervised criteria (score distribution percentiles) without requiring labeled data for threshold selection.

**Why this priority**: Enables deployment in unsupervised settings; labeled data is reserved for final evaluation only.

**Independent Test**: Can be fully tested by computing thresholds from score distributions and verifying thresholds are percentile-based (default 95th percentile).

**Acceptance Scenarios**:

1. **Given** a distribution of anomaly scores, **When** calling calibrate(), **Then** threshold is set at 95th percentile by default
2. **Given** adaptive mode enabled, **When** new scores arrive, **Then** threshold updates based on percentile without labeled data

---

### User Story 4 - Prior Sensitivity Analysis (Priority: P3)

The system MUST perform prior sensitivity analysis on Dirichlet process concentration parameters (alpha, gamma) to ensure model robustness across prior specifications.

**Why this priority**: Required per Constitution Principle VII to validate model stability; ensures results are not artifacts of specific prior choices.

**Independent Test**: Can be fully tested by running prior variation experiments and verifying models with ELBO variance>0.1 across prior variations are excluded from evaluation.

**Acceptance Scenarios**:

1. **Given** a trained DPGMM model, **When** running prior sensitivity analysis, **Then** alpha is tested at multiple values across [0.1, 1.0] and gamma at multiple values across [0.1, 5.0]
2. **Given** multiple prior configurations, **When** evaluating convergence, **Then** models with ELBO variance>0.1 across prior variations are excluded from final evaluation

---

### User Story 5 - Resource Constraints Validation (Priority: P3)

The system MUST validate memory and runtime constraints to ensure compatibility with GitHub Actions CI/CD environment.

**Why this priority**: Ensures reproducibility and CI/CD compatibility; prevents resource exhaustion in automated pipelines.

**Independent Test**: Can be fully tested by monitoring memory usage and runtime during dataset processing and verifying constraints are met.

**Acceptance Scenarios**:

1. **Given** a dataset being processed, **When** monitoring memory usage, **Then** peak RAM usage remains <7GB
2. **Given** a dataset being processed, **When** measuring runtime, **Then** total processing time remains <30 minutes

---

## Edge Cases

- What happens when a dataset has <1000 observations? → System MUST reject with validation error matching Dataset Schema minItems constraint
- How does system handle non-convergent models? → Models failing convergence criteria are excluded from evaluation per Convergence Criteria section
- What happens when streaming mode receives malformed observations? → System MUST return error with specific field validation message

## Requirements

### Functional Requirements

**FR-001**: System MUST load and parse time series datasets with a sufficient number of observations per series (matching Dataset Schema minItems constraint)

**FR-002**: System MUST train DPGMM model with convergence criteria: delta ELBO<0.01 for 10 consecutive iterations OR max 500 iterations

**FR-003**: System MUST compute anomaly scores for each observation using trained DPGMM posterior

**FR-004**: System MUST compute F1, precision, recall, and AUC-ROC metrics against ground truth labels (for evaluation only, not threshold selection)

**FR-005**: System MUST perform statistical comparison using Wilcoxon signed-rank test with bootstrap confidence intervals (n=10000 iterations) across datasets

**FR-006**: System MUST calibrate thresholds using unsupervised percentile-based method (default 95th percentile of score distribution)

**FR-007**: System MUST support adaptive threshold updates based on score distribution without labeled data

**FR-008**: AnomalyDetectorService.__init__() MUST initialize with config_path and load hyperparameters from config.yaml

**FR-009**: AnomalyDetectorService.load_model() MUST load DPGMM checkpoint and validate schema compliance

**FR-010**: AnomalyDetectorService.process_stream() MUST return AnomalyScore with score, timestamp, and uncertainty fields

**FR-011**: AnomalyDetectorService.update_model() MUST perform incremental posterior update in streaming mode without full retraining

**FR-012**: ThresholdCalibratorService.calibrate() MUST compute threshold from score distribution using percentile-based method

**FR-013**: ThresholdCalibratorService.validate_threshold() MUST verify threshold against constraints (0≤threshold≤1 for normalized scores)

**FR-014**: Dataset Schema MUST use 'timestamps' (plural, List[datetime]) field naming consistently across all contracts

**FR-015**: AnomalyScore Schema MUST include score (float), timestamp (datetime), and uncertainty (float, optional)

**FR-016**: EvaluationMetrics Schema MUST include f1_score, precision, recall (required) and auc_roc (optional)

**FR-017**: ThresholdCalibrator Schema MUST include threshold (float), percentile (float), and adaptive (boolean)

**FR-018**: AnomalyDetector Schema MUST include model_type (string), n_components (int, optional), and convergence_threshold (float)

**FR-019**: DPGMM Schema MUST include alpha (float), gamma (float), and concentration_prior (float)

**FR-020**: streaming_dpgmm.schema.yaml MUST define streaming-specific schema for incremental updates

**FR-021**: All schema files MUST have corresponding contract tests for validation

**FR-022**: config.yaml MUST be of a minimal size (only hyperparameters, seeds, base paths; derived stats in state file)

**FR-023**: All results MUST be stored in data/processed/results/ (no data/results/ directory permitted)

**FR-024**: Prior sensitivity analysis MUST test alpha∈[0.1,1.0] and gamma∈[0.1,5.0] at 5 values each

**FR-025**: Models with ELBO variance>0.1 across prior variations MUST be excluded from evaluation

### Key Entities

- **Dataset**: Time series data with series_id (string), values (List[float], ≥1000 items), timestamps (List[datetime], optional)
- **AnomalyScore**: Computed anomaly score with score (float), timestamp (datetime), uncertainty (float, optional)
- **EvaluationMetrics**: Performance metrics with f1_score, precision, recall (required), auc_roc (optional)
- **ThresholdCalibrator**: Threshold configuration with threshold (float), percentile (float), adaptive (boolean)
- **DPGMM**: Dirichlet Process Gaussian Mixture Model with alpha, gamma, concentration_prior parameters

## Service Interfaces

### AnomalyDetectorService
**File**: `code/src/services/anomaly_detector.py`  
**Methods **(7 total)
1. `__init__(self, config_path: str) -> None` - Initialize with config (FR-008)
2. `load_model(self, checkpoint_path: str) -> None` - Load DPGMM checkpoint (FR-009)
3. `process_stream(self, observation: Dict[str, float]) -> AnomalyScore` - Process single observation (FR-010)
4. `update_model(self, observations: List[Dict[str, float]]) -> None` - Streaming posterior update, incremental without full retraining (FR-011)
5. `compute_score(self, observation: Dict[str, float]) -> float` - Compute anomaly score
6. `get_uncertainty(self, observation: Dict[str, float]) -> float` - Return uncertainty estimate
7. `save_checkpoint(self, path: str) -> None` - Save model state

**Type Hints**: All public APIs use PEP 484 type hints (verified in T161)

### ThresholdCalibratorService
**File**: `code/src/services/threshold_calibrator.py`  
**Methods **(6 total)
1. `__init__(self, config_path: str) -> None` - Initialize with config
2. `calibrate(self, scores: List[float]) -> float` - Compute threshold from score distribution (percentile-based, FR-012)
3. `validate_threshold(self, threshold: float) -> bool` - Validate threshold against constraints (FR-013)
4. `get_decision_boundary(self) -> float` - Return current decision boundary
5. `update_decision_boundary(self, new_threshold: float) -> None` - Update boundary
6. `compute_expected_bounds(self) -> Tuple[float, float]` - Compute expected score bounds

**Type Hints**: All public APIs use PEP 484 type hints (verified in T161)

## Schema Definitions

### Dataset Schema (`specs/contracts/dataset.schema.yaml`)
- `series_id`: string (required)
- `values`: List[float] (required, min length 1000)
- `timestamps`: Optional[List[datetime]] (optional, plural form for consistency)

### AnomalyScore Schema (`specs/contracts/anomaly_score.schema.yaml`)
- `score`: float (required)
- `timestamp`: datetime (required)
- `uncertainty`: float (optional)

### EvaluationMetrics Schema (`specs/contracts/evaluation_metrics.schema.yaml`)
- `f1_score`: float (required)
- `precision`: float (required)
- `recall`: float (required)
- `auc_roc`: float (optional)

### ThresholdCalibrator Schema (`specs/contracts/threshold_calibrator.schema.yaml`)
- `threshold`: float (required)
- `percentile`: float (required)
- `adaptive`: boolean (required)

### AnomalyDetector Schema (`specs/contracts/anomaly_detector.schema.yaml`)
- `model_type`: string (required)
- `n_components`: int (optional)
- `convergence_threshold`: float (required)

### DPGMM Schema (`specs/contracts/dpgmm.schema.yaml`)
- `alpha`: float (required)
- `gamma`: float (required)
- `concentration_prior`: float (required)

### streaming_dpgmm Schema (`specs/contracts/streaming_dpgmm.schema.yaml`)
- `update_mode`: string (required, values: 'incremental', 'batch')
- `max_iterations`: int (required, default=500)
- `convergence_delta`: float (required, default=0.01)

### AnomalyDetectorService Schema (`specs/contracts/anomaly_detector_service.schema.yaml`)
- `service_name`: string (required)
- `method_count`: int (required, value=7)
- `type_hints_compliant`: boolean (required)

### ThresholdCalibratorService Schema (`specs/contracts/threshold_calibrator_service.schema.yaml`)
- `service_name`: string (required)
- `method_count`: int (required, value=6)
- `type_hints_compliant`: boolean (required)

## Data Directory Structure

**Required paths **(relative to project root)
- `data/raw/` - Raw dataset files (Electricity, Traffic, Synthetic Control Chart CSVs only)
- `data/processed/results/` - All evaluation artifacts, metrics, and analysis outputs
- `data/raw/raw/` - NO nested raw directories permitted (T241)
- `code/src/` - All Python source code (models/, services/, baselines/, data/, evaluation/, utils/)
- `code/tests/` - All test files (contract/, unit/, integration/)
- `state/projects/` - Project state files with checksums
- `logs/elbo/` - ELBO convergence logs per Constitution Principle VI
- `code/config.yaml` - Configuration file with hyperparameters, seeds, and base paths (<2048 bytes, FR-022)

**State File Path**: `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection.yaml`
- Contains SHA256 checksums for all data artifacts (T011, T157, T158, T232, T234, T245)
- Contains derived statistics (dataset stats, decision boundaries, computed metrics)
- Config.yaml must remain <2048 bytes (only hyperparameters, seeds, base paths) (T210, T211, T212, T243)

**Note on Legacy Directory**: The `data/results/` directory was created during early development and has been migrated to `data/processed/results/` per Phase 9 cleanup tasks (T214-T215). All code references have been updated to use the correct path (T242).

**Filesystem Verification Requirements **(Phase 9.5)
The following filesystem verification tasks require explicit command evidence in Phase 9.5:
- T240: PEMS-SF file deletion verification (ls -la data/raw/)
- T241: Nested raw directory verification (find data/raw/ -type d -name raw)
- T242: Legacy results directory verification (ls -la data/ | grep results)
- T243: Config.yaml size verification (stat -c%s code/config.yaml)
- T244: Source file location verification (find code/ -maxdepth 1 -name "*.py")
- T245: State file PEMS checksum verification (grep -E "pems|PEMS")

**Test Infrastructure Verification Requirements **(Phase 9.6)
The following test infrastructure verification tasks require explicit command evidence in Phase 9.6:
- T247: Contract test file listing verification (ls -la code/tests/contract/)
- T248: Contract test collection verification (pytest --collect-only)
- T249: Contract test coverage verification (pytest --cov)
- T250: Test infrastructure completeness documentation

## Test Requirements

### Contract Tests
**Location**: `code/tests/contract/`  
**Total Files**: 11 (9 schema tests + 2 service interface tests)  
**Coverage Requirement**: ≥80% line coverage (verified in T249 final gate, T163 preliminary check)

### Independent Test Scenarios
- US1: DPGMM converges on synthetic data, updates posterior incrementally (FR-001/002/003/011)
- US2: Baselines produce scores within expected ranges (F1, Precision, Recall) (FR-004/005)
- US3: Threshold adapts to score distribution without labeled data (FR-006/007)
- US4: Prior sensitivity analysis runs with 5x5 parameter grid (FR-024/025)
- US5: Resource constraints validated during processing (SC-007/SC-008)

**Traceability**:
- SC-004 (data hygiene) → US1 data processing requirements
- SC-005 (checksums) → US1 integrity verification
- SC-006 (config size) → US1 configuration management

## Methodology

### Statistical Comparison

Statistical comparison across multiple datasets uses Wilcoxon signed-rank test (non-parametric, valid for small sample sizes n<30) with bootstrap confidence intervals via bootstrap resampling (n=10000 iterations). Paired t-test is explicitly NOT used due to statistical underpowering at n=3-5.

### Prior Sensitivity Analysis

Per Constitution Principle VII, prior sensitivity analysis for Dirichlet process concentration parameters (alpha, gamma) is required:
- alpha tested at 5 values across [0.1, 1.0]
- gamma tested at 5 values across [0.1, 5.0]
- Models with ELBO variance>0.1 across prior variations are excluded from evaluation

### Convergence Criteria

Per Constitution Principle VI, Bayesian inference convergence diagnostics are required:
- ELBO convergence: delta ELBO<0.01 for 10 consecutive iterations
- Maximum iterations: 500
- Models failing convergence are excluded from evaluation
- **ADVI Note**: ADVI is used for variational inference with ELBO convergence monitoring. While ADVI convergence for DPGMM mixture models presents known challenges, the explicit 10-iteration consecutive delta threshold (delta<0.01) provides a robust stopping criterion. If convergence is not achieved within 500 iterations, the model is excluded from evaluation per the Convergence Criteria requirements.

### Resource Constraints

- Memory usage: <7GB RAM per dataset
- Runtime: <30 minutes per dataset (GHA compatibility)

## Success Criteria

| ID | Criterion | Verification Task |
|----|-----------|------------------|
| SC-001 | Univariate time series only (all series have exactly one numeric value column) | T139, T140, T141 |
| SC-002 | ≥1000 observations per dataset (matching Dataset Schema minItems constraint) | T173 |
| SC-003 | Multiple UCI datasets (Electricity, Traffic, Synthetic Control) | T155, T156, T170, T171, T172 |
| SC-004 | No PEMS-SF files in data/raw (data hygiene) | T155, T216, T217, T240 |
| SC-005 | SHA256 checksums for all data artifacts | T011, T157, T158, T232, T234, T245 |
| SC-006 | config.yaml < a limited size (derived stats in state file) | T210, T211, T212, T233, T243 |
| SC-007 | Memory usage <7GB RAM per dataset | T180, T181 |
| SC-008 | Runtime <30 minutes per dataset | T182, T183 |
| SC-009 | All 9 schema contracts validated (streaming_dpgmm included) | T163, T247, T248, T249 |
| SC-010 | Threshold calibration uses 95th percentile by default | T190, T191 |

## Assumptions

- Users have stable internet connectivity for dataset downloads
- Mobile support is out of scope for v1
- Existing authentication system will be reused (if applicable)
- Requires access to the existing user profile API (if applicable)
- Labels are generated via synthetic anomaly injection, not external CSV files
- ADVI is used for variational inference with ELBO convergence monitoring; convergence challenges for DPGMM mixture models are acknowledged and addressed via explicit convergence criteria (delta ELBO<0.01 for 10 iterations)
- **Power Analysis**: For low anomaly rates with sufficient observations, statistical power is adequate to detect anomalies at a standard confidence level. Sample size calculation: n≥1000 with p=0.01-0.05 anomaly rate provides sufficient observations (10-50 anomalies) for reliable F1/precision/recall metric computation. Power analysis formula: Power = 1 - β, where β is Type II error rate. At α=0.05, for a medium effect size, a sufficiently large sample size provides power >0.99.
- Streaming mode assumes observations arrive at a bounded rate.

## Quickstart

### Data Preparation

1. Download Electricity, Traffic, and Synthetic Control Chart datasets to `data/raw/`
2. Labels are generated via synthetic anomaly injection at a low rate (NOT from external CSV files like electricity_labels.csv)
3. Verify dataset compliance with Dataset Schema (series_id, values≥1000, timestamps optional)

### Model Training

1. Run `python code/src/data/download_datasets.py`
2. Train DPGMM model with config.yaml hyperparameters
3. Verify ELBO convergence in `logs/elbo/` directory

### Evaluation

1. Compute F1, precision, recall, AUC-ROC metrics
2. Perform Wilcoxon signed-rank test across datasets
3. Store results in `data/processed/results/`

## Status Tracking Mechanism

- `[X]` = Task completed successfully
- `[ ]` = Task pending
- **FAILED-IN-EXECUTION**: Task failed verification (must be resolved before T145)
- **T145 Final Acceptance **(Phase 10): Executes after ALL Phase 8 AND Phase 9 tasks complete, confirms no FAILED comments and all 10 success criteria (SC-001 through SC-010) are satisfied **and** requires external verification evidence from T222 (Phase 9 verification), T223 (final acceptance script), T226 (contract test execution), and T186 (schema-service interface validation) **and** verifies FAILED-IN-EXECUTION comments across all prior tasks using grep search
- **Phase Blocking Clarification**: Phase 7 (T163 preliminary coverage check) and Phase 8 (schema creation) are BLOCKING stage gates before `analyzed` stage. Phase 9 (critical resolution) and Phase 9.5/9.6 (verification enforcement) are also blocking before T145. T145 requires ALL Phase 7, Phase 8, AND Phase 9 completion. Phase 7 is a preliminary gate; Phase 9 is the final blocking gate before T145.