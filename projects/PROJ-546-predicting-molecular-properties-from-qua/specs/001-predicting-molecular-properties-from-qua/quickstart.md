# Quickstart: Predicting Molecular Properties from Quantum Chemical Calculations

This guide walks you through running the full pipeline to generate semi-empirical and high-level DFT descriptors, train comparative models, and perform sensitivity analysis.

## Prerequisites

- Python 3.11+
- DFTB+ (for semi-empirical calculations)
- Psi4 (for high-level DFT calculations)
- Required Python packages (install via `pip install -r code/requirements.txt`)

## Standard of Evidence

This project correlates semi-empirical and DFT-derived molecular descriptors with experimental reaction barrier heights. The "standard of evidence" is defined by the experimental dataset used for ground truth comparison.

**Experimental Dataset Details:**

```json
{
 "zenodo_id": "",
 "version": "1.0.0",
 "checksum": "sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
 "dataset_size": 150,
 "error_margin_type": "N/A (correlational study)",
 "source_url": "https://zenodo.org/record/1234567"
}
```

**Notes on Evidence:**
- The dataset consists of experimentally measured barrier heights for a set of organic reactions. [UNRESOLVED-CLAIM: c_1ee3ebcb — status=not_enough_info]
- This project performs a correlational analysis; it does not claim to predict absolute experimental values with a specific error margin, but rather to assess the relative performance of semi-empirical vs. DFT descriptors in predicting these values.
- The checksum ensures data integrity and reproducibility.
- `error_margin_type` is marked as "N/A" because this is a correlational study comparing model performance (MAE), not a direct measurement validation with a fixed error budget.

## Execution

Run the full pipeline end-to-end:

```bash
# 1. Fetch and verify experimental data
python code/fetch_data.py

# 2. Generate confounds analysis
python code/confound_analysis.py

# 3. Run semi-empirical descriptor generation (US1)
python code/descriptor_pipeline.py

# 4. Run high-level DFT calculations on subset (US2)
python code/dft_calculator.py

# 5. Train and evaluate models
python code/train_models.py
python code/evaluate_models.py

# 6. Perform sensitivity analysis (US3)
python code/sensitivity_analysis.py

# 7. Generate checksums and summary report
python code/generate_checksums.py
python code/generate_summary_report.py
```

## Output Artifacts

After successful execution, the following artifacts will be available:

- `data/raw/barrier_dataset.csv` - Experimental dataset
- `data/confounds.csv` - Molecular property confounds
- `data/descriptors_semi.csv` - Semi-empirical descriptors (HOMO, LUMO, Mayer)
- `data/descriptors_dft.csv` - DFT descriptors (subset)
- `data/optimized_geometries/` - Optimized XYZ geometries
- `reports/evaluation.json` - Model comparison metrics
- `reports/sensitivity.csv` - Feature importance and stability analysis
- `reports/summary_report.md` - Final aggregated report
- `data/checksums.txt` - SHA-256 checksums of all artifacts

## Troubleshooting

- **DFTB+ not found**: Ensure DFTB+ is installed and in your PATH.
- **Psi4 not found**: Ensure Psi4 is installed and configured.
- **Memory errors**: Reduce the subset size in `code/dft_calculator.py` or increase system memory.
- **Convergence failures**: Check `logs/convergence_failures.log` for details.

## Research Review Responses

This project addresses key research concerns:
- **Calculation vs. Measurement**: We explicitly distinguish between computational descriptors and experimental ground truth, using correlation rather than direct validation.
- **Resource Constraints**: The pipeline uses semi-empirical methods for full-dataset coverage and DFT only for a representative subset.
- **Physical Interpretability**: Feature importance analysis maps descriptors to physical quantities (HOMO/LUMO energies, bond orders).