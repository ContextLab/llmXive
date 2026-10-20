# Quickstart: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Prerequisites
* Python 3.11 or newer  
* Git  
* Internet connection (to download the OpenNeuro dataset and the Schaefer atlas)

## 2. Installation
```bash
# Clone the repository
git clone <REPO_URL>
cd projects/PROJ-056-the-impact-of-musical-training-on-functi

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## 3. Running the Pipeline

### 3.1 Synthetic Verification Mode (default)
This mode runs the full pipeline on generated synthetic data. It validates code paths,
memory limits, and output generation without requiring any real neuroimaging files.

```bash
python code/main.py --mode synthetic --n-subjects 100 --seed 42
```

Expected outputs (written under `data/processed/`):
- `subjects.parquet`
- `subjects_cleaned.csv`
- `subjects_cleaned.parquet`
- `matching_balance_report.csv`
- `connectivity_matrices.npy`
- `connectivity_results.csv`
- `nbs_results.csv`
- `correlation_results.csv`
- `sensitivity_analysis.csv`

### 3.2 Real‑Data Mode (stub)
The real‑data stub simply reports that no verified dataset is configured.
It creates a status JSON at `data/logs/real_ingest_status.json`.

```bash
python code/main.py --mode real
```

### 3.3 Smoke Test
Verify that the synthetic pipeline produces all expected artefacts and that they
conform to the JSON/YAML contracts:

```bash
python code/run_quickstart_test.py
```

The script will exit with a success status and print “Quickstart validation passed” on success.

## 4. Verify the Test Suite
```bash
pytest tests/
```

This runs the full unit‑test suite (including contract validation).
