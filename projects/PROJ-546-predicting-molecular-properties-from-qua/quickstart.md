# Quick Start Guide

## Prerequisites

- Python 3.11+
- DFTB+ installed and in PATH
- Psi4 installed and in PATH
- Required Python packages (see `requirements.txt`)

## Installation

```bash
# Create virtual environment
python -m venv code/.venv
source code/.venv/bin/activate # On Windows: code\.venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Running the Pipeline

The main entry point is `code/main.py`. It orchestrates the entire workflow:

```bash
# Run the full pipeline
python code/main.py
```

### Selective Execution

You can skip specific steps if already completed:

```bash
# Skip data fetching
python code/main.py --skip-fetch

# Skip confound analysis
python code/main.py --skip-confounds

# Skip semi-empirical descriptor generation
python code/main.py --skip-semi

# Skip DFT descriptor generation
python code/main.py --skip-dft

# Skip model training
python code/main.py --skip-train

# Skip model evaluation
python code/main.py --skip-eval

# Combine multiple skips
python code/main.py --skip-fetch --skip-confounds
```

## Output Artifacts

After successful execution, the following files will be generated:

- `data/raw/barrier_dataset.csv` - Raw experimental data
- `data/confounds.csv` - Molecular properties and functional groups
- `data/descriptors_semi.csv` - Semi-empirical descriptors (DFTB+)
- `data/descriptors_dft.csv` - DFT descriptors (Psi4) for subset
- `data/optimized_geometries/*.xyz` - Optimized geometries
- `reports/evaluation.json` - Model evaluation results
- `reports/sensitivity.csv` - Feature importance and sensitivity analysis
- `reports/summary_report.md` - Comprehensive summary report

## Troubleshooting

### Missing Dependencies

If you encounter import errors, ensure all packages are installed:

```bash
pip install -r code/requirements.txt
```

### DFTB+ or Psi4 Not Found

Ensure DFTB+ and Psi4 are installed and available in your PATH:

```bash
which dftb+
which psi4
```

### Convergence Failures

If DFTB+ or Psi4 calculations fail to converge, check the logs:

- `logs/convergence_failures.log`
- `logs/dft_execution.log`
- `logs/structural_failures.log`

### Memory Issues

If you encounter out-of-memory errors, reduce the subset size or increase available memory. Logs are written to `logs/oom_failures.log`.

## Verification

To verify the pipeline ran correctly:

```bash
# Check that all expected output files exist
ls -la data/raw/barrier_dataset.csv
ls -la data/confounds.csv
ls -la data/descriptors_semi.csv
ls -la data/descriptors_dft.csv
ls -la reports/evaluation.json
```

## Next Steps

- Review `reports/evaluation.json` for model performance metrics
- Examine `reports/sensitivity.csv` for feature importance insights
- Read `reports/summary_report.md` for a comprehensive overview
- Check `docs/reproducibility.md` for experimental details and checksums
