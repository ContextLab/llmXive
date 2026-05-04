# Contract Tests

## Purpose

Contract tests validate that all module outputs conform to their schema
definitions in `specs/contracts/`. These tests ensure API consistency
and prevent breaking changes across user story implementations.

## Coverage Requirements

Per Constitution Principle I and spec.md requirements:

- ≥80% line coverage for all public APIs
- Contract tests for all schema validations
- Integration tests for all user stories

## Schema-Test Mapping

| Schema File | Test File | Validates |
|-------------|-----------|-----------|
| `specs/contracts/dataset.schema.yaml` | `test_dataset_schema.py` | Dataset output structure |
| `specs/contracts/anomaly_score.schema.yaml` | `test_dp_gmm_schema.py` | DPGMM anomaly scores |
| `specs/contracts/evaluation_metrics.schema.yaml` | `test_metrics_schema.py` | Evaluation metrics |
| `specs/contracts/anomaly_detector.schema.yaml` | `test_anomaly_detector_schema.py` | AnomalyDetectorService |
| `specs/contracts/threshold_calibrator.schema.yaml` | `test_threshold_calibrator_schema.py` | ThresholdCalibratorService |

## Running Tests

```bash
# All contract tests
pytest code/tests/contract/ -v

# With coverage
pytest code/tests/contract/ --cov=code/src --cov-report=html

# Single test file
pytest code/tests/contract/test_dp_gmm_schema.py -v
```

## Test Structure

Each contract test file follows this pattern:

```python
def test_<component>_output_schema():
    # 1. Generate test input
    # 2. Call public API
    # 3. Validate output matches schema
    # 4. Assert required fields present
    # 5. Assert field types correct
```

## Integration with CI

Contract tests run as part of the CI pipeline (T063) with:
- Parallel execution across test files
- Coverage reporting (T074)
- Fail-fast on schema violations
