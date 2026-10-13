# Quick‑Start Guide

## Prerequisites

- **Python 3.11+** (the pipeline has been tested with Python 3.11 [UNRESOLVED-CLAIM: c_aac6e33b — status=not_enough_info])
- Git (to clone the repository)
- A working internet connection (required for downloading the Schaefer atlas)

## Installation

```bash
# Clone the repository
git clone <REPO_URL>
cd PROJ-056-the-impact-of-musical-training-on-functi

# Create a virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Pipeline

### Verification Mode (synthetic data)

This mode runs the full pipeline on generated synthetic data. It validates code paths, memory limits, and output generation without requiring any real neuroimaging files.

```bash
python -m code.main --mode verification
```

Expected outputs (written under `data/processed/`):
- `subjects_cleaned.csv`
- `connectivity_matrices.npy`
- `connectivity_results.csv`
- `nbs_results.csv`
- `correlation_results.csv`
- `sensitivity_analysis.csv`

### Analysis Mode (real data)

When you have a verified dataset (e.g., ABCD or HCP‑Adolescents) that includes resting‑state fMRI NIfTI files and behavioural metadata, run:

```bash
python -m code.main --mode analysis --data-path /path/to/real/data
```

The script will:
1. Load and validate the real data.
2. Perform preprocessing, confound matching, and regression.
3. Compute functional connectivity matrices.
4. Run statistical tests, NBS, correlation with years of training, and sensitivity analyses.
5. Write all results to `data/processed/` and figures to `figures/`.

**Important:** If the real dataset does not contain at least 50 subjects per group, the pipeline will abort with a clear `DataAccessError('Insufficient Data for Power')`.

## Testing

After installation, run the full test suite to ensure everything is working:

```bash
pytest tests/
```

The unit test `tests/unit/test_quickstart.py` checks that this quick‑start guide contains the required command (`python -m code.main --mode verification`) and that the top‑level folders are listed in `README.md`.

## Troubleshooting

- **Missing `networkx`**: Install it via `pip install networkx` (added to `requirements.txt` automatically by the pipeline).
- **Memory limit exceeded**: Reduce the number of subjects or use verification mode with fewer synthetic subjects (`--n-subjects` argument can be added to the script if needed).
- **Atlas download failures**: Ensure you have internet access; the atlas is fetched from the Nilearn dataset repository.