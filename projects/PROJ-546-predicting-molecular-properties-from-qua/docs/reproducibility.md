# Reproducibility Guide

## Data Sources
- **Experimental Dataset**: Zenodo ID [INSERT_ID], Version [INSERT_VERSION].
- **Checksums**: See `data/checksums.txt` for SHA-256 hashes of all raw and processed artifacts.

## Environment
- **Python**: 3.11+
- **Dependencies**: `code/requirements.txt` (pinned versions)
- **Quantum Software**: DFTB+ and Psi4 must be installed and available in PATH.

## Execution
1. Run `python code/download_data.py` to fetch raw data.
2. Run `python code/generate_descriptors.py` for semi-empirical results.
3. Run `python code/train_models.py` and `code/evaluate_models.py` for modeling.
4. Verify results against `reports/evaluation.json`.

## Physical Constraints
- Ensure `HOMO < LUMO` for all generated descriptors.
- Verify geometry alignment between DFTB+ and Psi4 runs.