# Data Integrity & Reproducibility

This document outlines the protocols ensuring data integrity and reproducibility in the `llmXive` pipeline.

## 1. Real Data Enforcement

The pipeline strictly adheres to the "Real Data Only" principle:
- **No Synthetic Fallbacks**: If a real data source (OpenNeuro) is unavailable, the loader raises a `DataLoadError` and halts. It does **not** generate fake data.
- **Verified Sources**: Data is fetched from verified URLs or pip-installable packages.
- **Hash Verification**: Downloaded parcellation files (e.g., HCP-MMP) are verified against SHA-256 manifests fetched dynamically from the source.

## 2. Reproducibility

- **Seeding**: All stochastic processes (simulation, permutation tests) use seeds defined in `config.py` or logged in `simulation_metadata.json`.
- **Parameter Logging**:
 - Wilson-Cowan parameters and random seeds for every simulation run are saved to `data/processed/simulation_metadata.json` (Task T030).
 - This ensures that any result can be traced back to the exact generation parameters.
- **Version Control**: All code artifacts are versioned. Dependencies are pinned in `code/requirements.txt`.

## 3. Checksum Tracking

- `utils/data_setup.py` implements checksum computation and verification.
- A `checksums.json` file tracks the integrity of raw and processed data.
- Any modification to a source file invalidates the checksum, triggering a re-processing warning.

## 4. Validation Protocols

- **T029a (Correlation Path)**: Validates that if N >= 10, `correlation_report.csv` exists with correct row counts.
- **T029b (Null Result Path)**: Validates that if N < 10, `null_result_report.md` exists and `correlation_report.csv` is absent.
- **T032 (Associational Framing)**: A regex-based validator in `report.py` scans generated text for causal keywords ("causes", "drives") and raises `RuntimeError` if found.

## 5. Failure Modes

- **Data Unavailable**: Pipeline halts with clear error message.
- **Convergence Failure**: If power-law fitting fails, the subject is excluded and logged (T033).
- **QC Failure**: Subjects with >30% channel loss or disconnected graphs are excluded.
