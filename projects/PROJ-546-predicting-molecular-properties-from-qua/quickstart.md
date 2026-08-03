# Quick Start Guide

## Prerequisites
- Python 3.11+
- DFTB+ (system installation required)
- Psi4 (system installation required)
- RDKit (pip install)

## Setup
```bash
pip install -r code/requirements.txt
```

## Execution
1. **Download Data**: Fetch experimental barrier dataset from Zenodo.
 ```bash
 python code/download_data.py
 ```
 Output: `data/raw/barrier_data.csv`

2. **Validate Data**: Ensure required columns exist.
 ```bash
 python code/validators/data_validator.py
 ```

3. **Generate Descriptors (Semi-Empirical)**: Run DFTB+ geometry optimization.
 ```bash
 python code/generate_descriptors.py --method dftb
 ```
 Output: `data/processed/descriptors_semi.csv`, `data/optimized_geometries/`

4. **Generate Descriptors (DFT)**: Run Psi4 on subset (uses exported geometries).
 ```bash
 python code/generate_descriptors.py --method psi4
 ```
 Output: `data/processed/descriptors_dft.csv`

5. **Train Models**: Train Random Forests on both datasets.
 ```bash
 python code/train_models.py
 ```

6. **Evaluate**: Compare models against experimental ground truth.
 ```bash
 python code/evaluate_models.py
 ```
 Output: `reports/evaluation.json`

7. **Sensitivity Analysis**: Sweep thresholds and report MAE degradation.
 ```bash
 python code/sensitivity_analysis.py
 ```
 Output: `reports/sensitivity.csv`

8. **Generate Summary**: Aggregate all metrics.
 ```bash
 python code/generate_summary_report.py
 ```
 Output: `data/reports/summary_report.md`

## Validation
- Runtime check: `python code/track_compute_resources.py` (must be < 6 hours)
- Checksums: `python code/generate_checksums.py`
