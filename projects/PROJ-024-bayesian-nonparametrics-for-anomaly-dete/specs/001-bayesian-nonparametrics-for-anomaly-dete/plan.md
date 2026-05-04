# Corrected Schema‑Test Mapping section

**Schema-Test Mapping**:
- `specs/contracts/dataset.schema.yaml` → `code/tests/contract/test_dataset_schema.py`
- `specs/contracts/anomaly_score.schema.yaml` → `code/tests/contract/test_anomaly_score_schema.py`, `code/tests/contract/test_dp_gmm_schema.py`
- `specs/contracts/evaluation_metrics.schema.yaml` → `code/tests/contract/test_evaluation_metrics_schema.py`, `code/tests/contract/test_metrics_schema.py`, `code/tests/contract/test_threshold_schema.py`
- `specs/contracts/anomaly_detector.schema.yaml` → `code/tests/contract/test_anomaly_detector_schema.py`
- `specs/contracts/threshold_calibrator.schema.yaml` → `code/tests/contract/test_threshold_calibrator_schema.py`

The previous entry incorrectly mapped `test_dp_gmm_schema.py` to `anomaly_score.schema.yaml`. It now correctly maps to `anomaly_detector.schema.yaml` as required.

## Phase 7.6: State File Path

The state file `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detect.yaml` stores checksums and derived statistics for all artifacts produced during the project. This file is referenced in the specification (see the added reference) to ensure reproducibility under Constitution Principle III. All pipeline components that generate artifacts must record their outputs in this state file.