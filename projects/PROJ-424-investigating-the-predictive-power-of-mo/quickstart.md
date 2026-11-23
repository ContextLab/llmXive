# Quickstart Guide: MD Diffusion Predictive Power Investigation

## Prerequisites
- Python 3.11+
- GROMACS (optional, for full simulation)
- LAMMPS (optional, for full simulation)

## Setup
1. Install dependencies:
 ```bash
 cd code
 pip install -r requirements.txt
 ```

2. Initialize the project structure (if not done):
 ```bash
 python setup_project.py
 ```

## Data Generation (Critical First Step)
Before running the analysis, you must generate the curated experimental data files.
The `data/raw/nist_refs.json` file does not exist by default and must be created
to provide ground truth for the validation.

Run the following command to generate the NIST references and the manifest:
```bash
python data/raw/generate_nist_refs.py
```

This will create:
- `data/raw/nist_refs.json`: Curated experimental diffusion coefficients.
- `data/raw/manifest.json`: Hash manifest for artifact verification.

## Running the Pipeline
Once data is generated, you can run the analysis pipeline.

### Full Batch Execution
Run the full pipeline for all solvents and timescales:
```bash
python main.py --full-batch
```

### Single Solvent Execution
Run for a specific solvent and timescale:
```bash
python main.py --solvent water --timescale 1.0
```

### Sensitivity Analysis
Run sensitivity analysis on a specific trajectory:
```bash
python main.py --sensitivity --solvent ethanol --timescale 10.0
```

## Verification
After running, check the `data/processed/` and `figures/` directories for outputs:
- `data/processed/diffusion_results.json`
- `data/processed/bootstrap_stats.csv`
- `figures/timescale_accuracy.png`

## Troubleshooting
- **FileNotFoundError: nist_refs.json**: Ensure you ran `python data/raw/generate_nist_refs.py` before running the main pipeline.
- **DataValidationError**: Check the format of `data/raw/nist_refs.json`. It must contain a list of dictionaries with 'solvent', 'temperature', and 'value'.