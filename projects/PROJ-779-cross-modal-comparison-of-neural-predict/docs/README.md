# Cross-Modal Comparison of Neural Prediction Error Signals

## Project Overview

This project implements an automated pipeline for comparing neural prediction error signals across auditory and visual modalities. The pipeline downloads real neurophysiological data from OpenNeuro, preprocesses it, extracts prediction error metrics, performs source localization, and conducts statistical comparisons.

## Real Data Assumption

**CRITICAL**: This project operates under a strict "Real Data Only" policy.

- **All data must originate from OpenNeuro datasets** (specifically `ds000246` for auditory and `ds000117` for visual modalities).
- **No synthetic data generation is permitted** at any stage of the pipeline.
- **No placeholder or simulated datasets** are allowed for testing or development.
- **No fabrication of results** is permitted; all metrics must be computed from actual measured neural signals.

This policy is enforced by:
1. **Data validation checks** in `code/config.py` that verify data origin and integrity.
2. **Runtime validation** in `code/data/download.py` that halts execution if data cannot be verified as originating from the specified OpenNeuro sources.
3. **Checksum verification** against a manifest (`data/manifest.json`) to ensure data integrity throughout the pipeline.

Violating this assumption will result in immediate pipeline failure with explicit error codes.

## Installation

See `docs/quickstart.md` for detailed installation and setup instructions.

## Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`

## Data Sources

- **Auditory Oddball**: OpenNeuro ds000246
- **Visual Oddball**: OpenNeuro ds000117 (via Hugging Face snapshot)

## License

[Project License]
