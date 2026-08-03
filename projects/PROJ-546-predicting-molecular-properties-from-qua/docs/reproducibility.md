# Reproducibility Guide

## Standard of Evidence
- **Dataset**: Experimental barrier heights from Zenodo (DOI: 10.xxxx/xxxxx).
- **Instruments**: DFTB+ (v22.1), Psi4 (v1.8).
- **Error Margins**: MAE calculated against experimental ground truth; threshold set at 2.0 kcal/mol.

## Environment Setup
1. **Python**: 3.11+
2. **Dependencies**: `pip install -r code/requirements.txt`
3. **External Tools**:
 - DFTB+ must be in PATH.
 - Psi4 must be in PATH.

## Data Integrity
- Checksums for all artifacts are stored in `data/checksums.txt`.
- Verify integrity before running: `python code/generate_checksums.py --verify`.

## Execution Steps
1. Download data: `python code/download_data.py`
2. Run full pipeline: `bash scripts/run_pipeline.sh` (if available) or execute scripts sequentially.
3. Validate results: `python code/evaluate_models.py`

## Known Limitations
- Semi-empirical approximations may miss solvent effects (Franklin Review).
- Basis set limitations in DFTB+ may affect accuracy (Feynman Review).
