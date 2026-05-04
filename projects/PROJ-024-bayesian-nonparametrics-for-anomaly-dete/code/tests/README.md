# Test Documentation

## Overview

This directory contains the complete test suite for the Bayesian Nonparametrics Anomaly Detection project. All tests are required per spec.md and Constitution Principle I for task isolation and reproducibility.

## Test Structure

```
code/tests/
├── __init__.py
├── README.md                    # This file
├── contract/                    # Contract tests for schemas
│   ├── test_dp_gmm_schema.py    # Validates anomaly_score.schema.yaml
│   ├── test_metrics_schema.py   # Validates evaluation_metrics.schema.yaml
│   ├── test_threshold_calibrator_schema.py
│   └── test_anomaly_detector_schema.py
├── unit/                        # Unit tests for individual components
│   ├── test_memory_profile.py
│   └── ...
├── integration/                 # Integration tests for workflows
│   ├── test_streaming_update.py
│   ├── test_baseline_comparison.py
│   └── test_threshold_calibration.py
└── test_report.md               # Generated test report
```

## Test Coverage Requirements

Per Constitution Principle I and spec.md requirements:

- **≥80% line coverage** for all public APIs (enforced via pytest-cov)
- **Contract tests** for all schema validations (specs/contracts/*.yaml)
- **Integration tests** for all user stories (US1, US2, US3)
- **Unit tests** for edge cases and numerical stability

### Schema-Test Mapping

| Schema File | Contract Test |
|-------------|---------------|
| `specs/contracts/dataset.schema.yaml` | `tests/contract/test_dataset_schema.py` |
| `specs/contracts/anomaly_score.schema.yaml` | `tests/contract/test_dp_gmm_schema.py` |
| `specs/contracts/evaluation_metrics.schema.yaml` | `tests/contract/test_metrics_schema.py` |
| `specs/contracts/threshold_calibrator.schema.yaml` | `tests/contract/test_threshold_calibrator_schema.py` |
| `specs/contracts/anomaly_detector.schema.yaml` | `tests/contract/test_anomaly_detector_schema.py` |

## Running Tests

```bash
# Run all tests
cd code
pytest

# Run with coverage (enforces ≥80% threshold)
pytest --cov=src --cov-report=html --cov-fail-under=80

# Run specific test category
pytest tests/contract/
pytest tests/unit/
pytest tests/integration/

# Run with verbose output and timing
pytest -v --durations=10
```

## Test Execution Order

Tests MUST be run in this order to respect dependencies:

1. **Contract tests** - Verify schema compliance (no dependencies)
2. **Unit tests** - Verify individual components (may depend on contract tests)
3. **Integration tests** - Verify end-to-end workflows (depend on unit tests)

### Parallel Execution Safety

Tasks marked [P] in tasks.md are parallel-safe if they:
- Write to different files (no file conflicts)
- Have no shared mutable state
- Use independent test fixtures

Verification: Run `code/scripts/verify_parallel_safety.py` before parallel execution.

## Constitution Principle I Compliance

Each task must satisfy:

- [ ] Task writes to unique file paths (no cross-task file conflicts)
- [ ] Task has independent test coverage (contract + integration + unit)
- [ ] Task does not modify tasks.md (Tasker-only writer)
- [ ] Task artifacts are reproducible (pinned dependencies, fixed seeds)
- [ ] Task passes all verification scripts (coverage, checksums, parallel safety)

### Verification Checklist

Before marking any task complete:

1. Run contract tests: `pytest tests/contract/ -v`
2. Run unit tests: `pytest tests/unit/ -v`
3. Run integration tests: `pytest tests/integration/ -v`
4. Verify coverage: `pytest --cov=src --cov-report=term --cov-fail-under=80`
5. Verify parallel safety: `python code/scripts/verify_parallel_safety.py`
6. Verify dependency order: `python code/scripts/verify_dependency_order.py`

## Failed Test Resolution

Any test failures MUST be documented and resolved before:

- Task completion (mark [X] in tasks.md)
- Code merge (PR review)
- Project acceptance (research_complete stage)

### Common Failure Patterns

| Error | Resolution |
|-------|------------|
| `ModuleNotFoundError` | Check import paths match API surface in task input |
| `AssertionError` in contract test | Fix schema implementation to match YAML definition |
| Coverage <80% | Add missing unit tests for uncovered public functions |
| Integration test timeout | Increase timeout_s or optimize algorithm complexity |

## Test Report Generation

After each test run, generate a summary report:

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Generate JSON test results
pytest --json-report --json-report-file=tests/test_report.json

# Generate Markdown summary
python code/scripts/generate_summary_report.py
```

Results are saved to `data/processed/results/test_report.md`.

## Integration with CI Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`) runs:

1. Contract tests (parallel-safe)
2. Unit tests (parallel-safe)
3. Integration tests (sequential, with timeouts)
4. Coverage verification (enforces ≥80% threshold)

See `.github/workflows/ci.yml` for full pipeline configuration.

## User Story Test Mapping

| User Story | Contract Test | Integration Test | Unit Test |
|------------|---------------|------------------|-----------|
| US1 (DPGMM) | test_dp_gmm_schema.py | test_streaming_update.py | test_memory_profile.py |
| US2 (Baselines) | test_metrics_schema.py | test_baseline_comparison.py | test_baselines.py |
| US3 (Threshold) | test_threshold_calibrator_schema.py | test_threshold_calibration.py | test_threshold.py |

## Additional Resources

- Constitution Principles: `specs/001-bayesian-nonparametrics-anomaly-detection/constitution_check.md`
- Test Coverage Requirements: `specs/contracts/` schema definitions
- API Surface: See task input `# Existing project API surface` block
- Verification Scripts: `code/scripts/verify_*.py`
