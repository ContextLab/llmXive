# Implementation Plan: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Branch**: `001-bayesian-nonparametrics-anomaly-detection` | **Date**: 2024-01-15 | **Spec**: specs/001-bayesian-nonparametrics-anomaly-detection/spec.md

**Input**: Feature specification from `specs/001-bayesian-nonparametrics-anomaly-detection/spec.md`

## Summary

Implement an incremental Dirichlet Process Gaussian Mixture Model (DPGMM) for streaming anomaly detection in univariate time series. The core innovation is the stick-breaking construction with ADVI variational inference, enabling anomaly scoring without batch retraining. The system compares against ARIMA, moving average, and LSTM Autoencoder baselines on UCI benchmark datasets, with adaptive threshold calibration for unlabeled deployment scenarios.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyMC 5.9.0, NumPy 1.24.0, pandas 2.0.0, scikit-learn 1.3.0, statsmodels 0.14.0, ucimlrepo 0.0.7, torch 2.0.0  
**Storage**: Local filesystem (data/raw, data/processed, data/processed/results), config.yaml for hyperparameters, state/projects/ for artifact hashes  
**Testing**: pytest 7.4.0 with contract tests against YAML schemas  
**Target Platform**: Linux server (GitHub Actions runners)  
**Project Type**: computational research library  
**Performance Goals**: <30 minutes per dataset on CI, <7GB RAM during processing  
**Constraints**: Univariate time series only, no multivariate extensions, streaming update after each observation  
**Scale/Scope**: 3-5 UCI datasets, 1000+ observations per dataset, F1-score within 5% of baselines

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design and Phase 6 completion.*

| Principle | Compliance Status | Implementation Notes |
|-----------|-------------------|---------------------|
| I. Reproducibility (NON-NEGOTIABLE) | COMPLIANT | Random seeds pinned in config.yaml. External datasets fetched via wget/curl from canonical UCI sources on every run. requirements.txt pins all dependencies. config.yaml size kept under 2KB per FR-009. |
| II. Verified Accuracy | COMPLIANT | All citations in research.md and paper artifacts will be verified by Reference-Validator Agent before review points are awarded. Title-token-overlap threshold ≥ 0.7 enforced. |
| III. Data Hygiene | COMPLIANT | Every file under data/ is checksummed in state artifact_hashes map. Raw data preserved unchanged; derivations written to new filenames. PII scan enforced using `bandit` and `trufflehog` tools. data-dictionary.md documents all dataset provenance. |
| IV. Single Source of Truth | COMPLIANT | Every figure, statistic, or interpretation in paper traces to exactly one row in data/ and one block in code/. Derived numbers NOT hand-typed. |
| V. Versioning Discipline | COMPLIANT | Every artifact carries content hash. State updated_at timestamp refreshed on artifact changes. All file paths in tasks.md match actual filesystem structure. |
| VI. Numerical Stability & Convergence | COMPLIANT | ADVI convergence diagnostics (ELBO convergence) reported in logs/elbo/. Models failing convergence within 500 iterations or ELBO improvement <0.001 for 50 consecutive iterations marked invalid for review. |
| VII. Prior Sensitivity Analysis | COMPLIANT | Dirichlet process concentration parameter varied in sensitivity analysis. Results claimed as robust hold across reasonable prior specifications documented in paper/. |

**Note**: Constitution Check timing corrected: Initial check in Phase 0 (T003), re-check after Phase 1 design completion (T016-Phase1), and final verification in Phase 6 (T066). All principles show COMPLIANT status as design requirements are met; Phase 6 tasks verify implementation correctness.

## Project Structure

### Documentation (this feature)

```
specs/001-bayesian-nonparametrics-anomaly-detection/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── data-dictionary.md   # Phase 6 output - dataset provenance documentation
├── constitution_check.md # Phase 6 output - final constitution compliance verification
├── contracts/           # Phase 1 output (/speckit-plan command) - SCHEMA DEFINITIONS
│   ├── dataset.schema.yaml
│   ├── anomaly_score.schema.yaml
│   ├── evaluation_metrics.schema.yaml
│   ├── anomaly_detector.schema.yaml
│   └── threshold_calibrator.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── code/
│   ├── requirements.txt
│   ├── config.yaml              # MUST remain under 2KB per FR-009
│   ├── mypy.ini                 # mypy strict mode configuration
│   ├── scripts/                 # Executable validation and utility scripts
│   │   ├── validate_quickstart_artifacts.py
│   │   ├── download_synthetic_control.py
│   │   ├── generate_data_checksums.py
│   │   ├── verify_test_files.py
│   │   ├── verify_threshold_tests.py
│   │   ├── run_all_contract_tests.py
│   │   ├── verify_spec_files.py
│   │   ├── verify_config_compliance.py
│   │   ├── compute_anomaly_uncertainty.py
│   │   ├── verify_parallel_safety.py
│   │   └── verify_dependency_order.py
│   ├── src/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── dpgmm.py
│   │   │   ├── time_series.py
│   │   │   └── anomaly_score.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── anomaly_detector.py
│   │   │   └── threshold_calibrator.py
│   │   ├── baselines/
│   │   │   ├── __init__.py
│   │   │   ├── arima.py
│   │   │   ├── moving_average.py
│   │   │   └── lstm_ae.py
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── download_datasets.py
│   │   │   └── synthetic_generator.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── streaming.py
│   │   │   ├── time_split.py
│   │   │   ├── threshold.py
│   │   │   ├── memory_profiler.py
│   │   │   ├── runtime_monitor.py
│   │   │   └── hyperparameter_counter.py
│   │   └── evaluation/
│   │       ├── __init__.py
│   │       ├── metrics.py
│   │       ├── plots.py
│   │       └── statistical_tests.py
│   └── tests/
│       ├── contract/              # CONTRACT TESTS - validates against schemas in specs/contracts/
│       │   ├── test_dataset_schema.py          # → specs/contracts/dataset.schema.yaml
│       │   ├── test_anomaly_score_schema.py    # → specs/contracts/anomaly_score.schema.yaml
│       │   ├── test_evaluation_metrics_schema.py # → specs/contracts/evaluation_metrics.schema.yaml
│       │   ├── test_dp_gmm_schema.py           # → specs/contracts/anomaly_score.schema.yaml
│       │   ├── test_metrics_schema.py          # → specs/contracts/evaluation_metrics.schema.yaml
│       │   ├── test_threshold_schema.py        # → specs/contracts/evaluation_metrics.schema.yaml
│       │   ├── test_anomaly_detector_schema.py # → specs/contracts/anomaly_detector.schema.yaml
│       │   └── test_threshold_calibrator_schema.py # → specs/contracts/threshold_calibrator.schema.yaml
│       ├── unit/
│       │   ├── test_dpgmm.py
│       │   ├── test_threshold_calibrator.py
│       │   ├── test_memory_profile.py
│       │   └── test_edge_cases.py
│       └── integration/
│           ├── test_full_pipeline.py
│           ├── test_streaming_update.py
│           ├── test_baseline_comparison.py
│           └── test_threshold_calibration.py
├── data/
│   ├── raw/
│   │   ├── electricity/
│   │   ├── traffic/
│   │   └── synthetic_control/
│   └── processed/
│       └── [dataset_name]_processed.csv
│       └── results/                     # Added for evaluation outputs
├── logs/
│   └── elbo/                    # ELBO convergence logs for ADVI variational inference
├── state/
│   └── projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
├── code/tests/test_report.md    # Final test execution report with pass/fail status per task
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── README.md
└── LICENSE
```

**Schema-Test Mapping**:
- `specs/contracts/dataset.schema.yaml` → `code/tests/contract/test_dataset_schema.py`
- `specs/contracts/anomaly_score.schema.yaml` → `code/tests/contract/test_anomaly_score_schema.py`, `code/tests/contract/test_dp_gmm_schema.py`
- `specs/contracts/evaluation_metrics.schema.yaml` → `code/tests/contract/test_evaluation_metrics_schema.py`, `code/tests/contract/test_metrics_schema.py`, `code/tests/contract/test_threshold_schema.py`
- `specs/contracts/anomaly_detector.schema.yaml` → `code/tests/contract/test_anomaly_detector_schema.py`
- `specs/contracts/threshold_calibrator.schema.yaml` → `code/tests/contract/test_threshold_calibrator_schema.py`

**Structure Decision**: Single project structure (Option 1) selected because this is a computational research library with no frontend/backend separation. All code under `code/src/` follows standard Python package layout with clear separation between models, services, baselines, data, utils, and evaluation. Tests organized by type (contract, unit, integration) to support the contract validation requirements. code/scripts/ directory contains executable validation and utility scripts for CI/CD and manual verification tasks.

**Schema Creation Tasks**: Schema YAML files in specs/contracts/ must be created in Phase 1 (Foundational) before contract tests can be implemented. Each schema defines the expected structure for its corresponding data entity and must be validated before any test can run.

**Constitution Check Phase 1**: Constitution Principles I-VII compliance check MUST be performed in Phase 1 design to ensure schema and structure align with principles before implementation begins.

**__init__.py Phase**: All `__init__.py` files for subpackages must be created in Phase 1 Setup to ensure proper Python package structure from the start.