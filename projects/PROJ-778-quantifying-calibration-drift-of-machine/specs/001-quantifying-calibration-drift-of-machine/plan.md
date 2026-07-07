# Implementation Plan: Quantifying Calibration Drift of Machine Learning Classifiers Over Time

**Branch**: `001-calibration-drift` | **Date**: 2026-06-25 | **Spec**: `specs/001-calibration-drift/spec.md`

## Summary
This project quantifies the temporal drift of machine learning classifier calibration. Due to the absence of native yearly snapshots in standard UCI Adult and Credit Card Default datasets, the approach pivots to using the **IPUMS Current Population Survey (CPS)** dataset (which has verified yearly extracts) or a **Synthetic Drift Generator** if real temporal data is unavailable. The system trains fixed probabilistic classifiers (Logistic Regression, Random Forest) on the earliest available snapshot and evaluates them on subsequent years. The system computes calibration metrics (ECE, Brier), covariate shift (PCA-based shift on high-dimensional data and Mean Shift on key features), and performs statistical trend analysis (Weighted Least Squares, BIC-based change-point detection) to determine if calibration degrades systematically over time.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `scipy`, `statsmodels`, `ruptures`, `requests`, `pyyaml`, `ipums` (or `synthetic_drift`)  
**Storage**: Local file system (`data/` for raw/processed data, `code/` for scripts)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, ~7GB RAM)  
**Project Type**: Data Analysis / Research Pipeline  
**Performance Goals**: Complete full pipeline (download/generate, train, evaluate, analyze) within 6 hours on CPU-only runner.  
**Constraints**: No GPU; no model retraining on test data; strict schema alignment; memory usage < 7GB.  
**Scale/Scope**: 1 dataset (IPUMS CPS or Synthetic), ~ years of data, model types, metric types.

> **Compute Feasibility Note**: The plan strictly adheres to CPU-only constraints. Covariate shift is computed via PCA projection (retaining a dominant proportion of variance) to avoid the curse of dimensionality. `ruptures` is used for change-point detection with a BIC penalty to automatically determine optimal block sizes, ensuring runtime fits within the 6-hour limit.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`. Data fetched from canonical sources (IPUMS) or generated with fixed seeds. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS | **Data Availability Gate (00_data_availability_gate.py)** halts execution if the required temporal dataset is not found. All method citations validated against `research.md` source list. |
| **III. Data Hygiene** | PASS | Raw data stored in `data/raw/` with checksums. Derived data in `data/processed/` with explicit derivation logs. No in-place modification. |
| **IV. Single Source of Truth** | PASS | All statistics in the final report are generated programmatically from `data/processed/` via `code/` scripts. No manual entry. |
| **V. Versioning Discipline** | PASS | Artifacts tracked via content hashes in `state/`. `updated_at` timestamps updated on change. |
| **VI. Temporal Distribution Shift Awareness** | PASS | Every calibration metric (ECE/Brier) is paired with a covariate shift metric (PCA Shift/Key Feature Shift). The `05_report_generation.py` script includes a logic check: if shift metrics are missing/invalid, the ECE trend is flagged or excluded. |
| **VII. Fixed-Model Evaluation Integrity** | PASS | Models are trained ONCE on the earliest snapshot. The evaluation loop strictly applies these frozen weights to all subsequent years. No retraining logic exists. |

## Project Structure

### Documentation (this feature)

```text
specs/001-calibration-drift/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset_schema.yaml
│   └── metric_record_schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── 00_data_availability_gate.py   # Checks for IPUMS CPS or generates synthetic data; halts if missing
├── 01_data_acquisition.py         # Downloads IPUMS yearly snapshots or generates synthetic drift
├── 02_model_training.py           # Trains fixed models on earliest snapshot
├── 03_evaluation.py               # Computes ECE (multiple bins), Brier, PCA Shift, Key Feature Shift
├── 04_statistical_analysis.py     # WLS, Durbin-Watson, BIC change-point detection
├── 05_report_generation.py        # Generates Markdown report and plots
├── utils/
│   ├── metrics.py                 # ECE, Brier, PCA Shift, Key Feature Shift implementations
│   ├── shift_detection.py         # BIC-based change-point logic
│   └── config.py                  # Path and parameter configuration
└── main.py                        # Orchestration script

data/
├── raw/                         # Downloaded CSV/JSON files (checksummed) or synthetic data
├── processed/                   # Splits, predictions, metric records
└── models/                      # Serialized sklearn models

tests/
├── unit/
│   ├── test_metrics.py
│   └── test_shift_detection.py
└── integration/
    └── test_pipeline.py
```

**Structure Decision**: Single-project structure selected to minimize overhead for a research pipeline. All scripts are sequential and data-driven, allowing for easy debugging and reproducibility on a single runner. **Schema Validation**: `01_data_acquisition.py` and `03_evaluation.py` explicitly validate outputs against `contracts/` schemas before writing to `data/processed/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **PCA-based Shift & Key Feature Shift** | Required to avoid curse of dimensionality (methodology-f8ca3bc0) and ensure consistent feature space across years (scientific_soundness-d2260ced). | Raw Wasserstein distance on high-dimensional features is statistically invalid and unstable. |
| **Weighted Least Squares (WLS)** | Required to control for sample size variance and autocorrelation (methodology-075eec90, scientific_soundness-e03f61c9). | Simple Linear Regression ignores heteroscedasticity and autocorrelation, leading to invalid p-values. |
| **BIC-based Change-Point Detection** | Required to avoid arbitrary block size selection (methodology-d03f5496). | Fixed block size (2 years) lacks statistical justification and may miss true drift patterns. |
| **Multiple binning strategies, including moderate and fine-grained configurations.** | Required by FR-010 for robustness verification. | Single binning strategy risks bias in ECE calculation; robustness check is mandated by SC-002. **Implementation Note**: `03_evaluation.py` MUST compute and store all three ECE values for every year. |

## Data Acquisition Logic Update

The pipeline now begins with `00_data_availability_gate.py`. This script:
1. Checks for the presence of the IPUMS CPS dataset (verified temporal source).
2. If not found, checks for a configuration to generate synthetic drift.
3. If neither is available, **halts execution** and logs a critical error, preventing the fabrication of time series data.
4. If data is available, it proceeds to `01_data_acquisition.py` to download/generate the yearly snapshots.

This gate ensures adherence to Constitution Principle II (Verified Accuracy) and prevents the fatal feasibility gap identified in data_resources-9afd94c2.