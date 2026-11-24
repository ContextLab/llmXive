# Quickstart Guide

## 1. Prerequisites
- **Python 3.11+**
- Git
- An active internet connection (required for downloading the Schaefer atlas)

## 2. Installation
```bash
# Clone the repository
git clone <REPO_URL>
cd PROJ-056-the-impact-of-musical-training-on-functi

# Create a virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 3. Running the Pipeline

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
When you have a verified dataset (e.g., ABCD or HCP-Adolescents) that includes resting-state fMRI NIfTI files and behavioural metadata, run:

```bash
python -m code.main --mode analysis --data-path /path/to/real/data
```

The script will load and validate the real data, perform preprocessing, confound matching, and execute the full statistical analysis.

**Important:** If the real dataset does not contain at least 50 subjects per group, the pipeline will abort with a clear `DataAccessError('Insufficient Data for Power')`.

## 4. Testing
After installation, run the full test suite to ensure everything is working:
```bash
pytest tests/
```
The unit test `tests/unit/test_quickstart.py` specifically verifies that this guide and the README are up-to-date.
