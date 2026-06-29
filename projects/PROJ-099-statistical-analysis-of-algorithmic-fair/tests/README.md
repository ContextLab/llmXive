# Tests Directory

This directory contains all test suites for the project.

## Structure
```
tests/
├── unit/
│ ├── test_checksum.py
│ ├── test_variable_validation.py
│ ├── test_demographic_parity.py
│ ├── test_equalized_odds.py
│ ├── test_fdr_correction.py
│ └── test_bootstrap.py
├── contract/
│ ├── test_dataset_download.py
│ ├── test_model_training.py
│ ├── test_correlation_analysis.py
│ └── test_framing_verification.py
└── integration/
 ├── test_preprocessing.py
 ├── test_fairness_metrics.py
 └── test_regression_analysis.py
```

## Running Tests
```bash
pytest tests/
```

## FR-008 Disclaimer
Findings are associational only; no causal claims are made.