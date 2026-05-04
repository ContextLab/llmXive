# Specification: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Project ID**: PROJ-024  
**Version**: 1.0.0  
**Status**: planned  
**Constitution**: Principles I-VIII apply

## Service Interfaces

### AnomalyDetectorService
**File**: `code/src/services/anomaly_detector.py`  
**Methods **(7 total)
1. `__init__(self, config_path: str) -> None` - Initialize with config
2. `load_model(self, checkpoint_path: str) -> None` - Load DPGMM checkpoint
3. `process_stream(self, observation: Dict[str, float]) -> AnomalyScore` - Process single observation
4. `update_model(self, observations: List[Dict[str, float]]) -> None` - Streaming posterior update
5. `compute_score(self, observation: Dict[str, float]) -> float` - Compute anomaly score
6. `get_uncertainty(self, observation: Dict[str, float]) -> float` - Return uncertainty estimate
7. `save_checkpoint(self, path: str) -> None` - Save model state

**Type Hints**: All public APIs use PEP 484 type hints (verified in T161)

### ThresholdCalibratorService
**File**: `code/src/services/threshold_calibrator.py`  
**Methods **(6 total)
1. `__init__(self, config_path: str) -> None` - Initialize with config
2. `calibrate(self, scores: List[float]) -> float` - Compute threshold from score distribution
3. `validate_threshold(self, threshold: float) -> bool` - Validate threshold against constraints
4. `get_decision_boundary(self) -> float` - Return current decision boundary
5. `update_decision_boundary(self, new_threshold: float) -> None` - Update boundary
6. `compute_expected_bounds(self) -> Tuple[float, float]` - Compute expected score bounds

**Type Hints**: All public APIs use PEP 484 type hints (verified in T161)

## Schema Definitions

### Dataset Schema (`specs/contracts/dataset.schema.yaml`)
- `series_id`: string (required)
- `values`: List[float] (required, min length 1000)
- `timestamp`: Optional[List[datetime]] (optional)

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
- `data/processed/results/` - NO legacy `data/results/` directory permitted
- `data/raw/raw/` - NO nested raw directories permitted
- `code/src/` - All Python source code (models/, services/, baselines/, data/, evaluation/, utils/)
- `code/tests/` - All test files (contract/, unit/, integration/)
- `state/projects/` - Project state files with checksums
- `logs/elbo/` - ELBO convergence logs per Constitution Principle VI
- `code/config.yaml` - Configuration file with hyperparameters, seeds, and base paths (<2KB)

**State File Path**: `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection.yaml`
- Contains SHA256 checksums for all data artifacts
- Contains derived statistics (dataset stats, decision boundaries, computed metrics)
- Config.yaml must remain <2KB (only hyperparameters, seeds, base paths)

**Note on Legacy Directory**: The `data/results/` directory was created during early development and has been migrated to `data/processed/results/` per Phase 9 cleanup tasks (T214-T215). All code references have been updated to use the correct path.

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
**Total Files**: 8 (6 schema tests + 2 service interface tests)  
**Coverage Requirement**: ≥80% line coverage (verified in T249 final gate, T163 preliminary check)

### Independent Test Scenarios
- US1: DPGMM converges on synthetic data, updates posterior incrementally
- US2: Baselines produce scores within expected ranges (F1, Precision, Recall)
- US3: Threshold adapts to score distribution without labeled data

## Success Criteria

| ID | Criterion | Verification Task |
|----|-----------|------------------|
| SC-001 | Univariate time series only | T139, T140, T141 |
| SC-002 | ≥1000 observations per dataset | T173 |
| SC-003 | 3 UCI datasets (Electricity, Traffic, Synthetic Control) | T155, T156, T170, T171, T172 |
| SC-004 | No PEMS-SF files in data/raw | T155, T216, T217, T240 |
| SC-005 | SHA256 checksums for all data artifacts | T011, T157, T158, T232, T234, T245 |
| SC-006 | config.yaml <2KB, derived stats in state file | T210, T211, T212, T233, T243 |

## Status Tracking Mechanism

- `[X]` = Task completed successfully
- `[ ]` = Task pending
- **FAILED-IN-EXECUTION**: Task failed verification (must be resolved before T145)
- **T145 Final Acceptance **(Phase 10): Executes after ALL Phase 8 AND Phase 9 tasks complete, confirms no FAILED comments and all 6 success criteria (SC-001 through SC-006) are satisfied **and** requires external verification evidence from T222 (Phase 9 verification), T223 (final acceptance script), T226 (contract test execution), and T186 (schema-service interface validation) **and** verifies FAILED-IN-EXECUTION comments across all prior tasks using grep search
- **Phase Blocking Clarification**: Phase 7 (T163 preliminary coverage check) and Phase 8 (schema creation) are BLOCKING stage gates before `analyzed` stage. Phase 9 (critical resolution) and Phase 9.5/9.6 (verification enforcement) are also blocking before T145. T145 requires ALL Phase 7, Phase 8, AND Phase 9 completion. Phase 7 is a preliminary gate; Phase 9 is the final blocking gate before T145.