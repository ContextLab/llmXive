# Quick Start Guide

Get up and running with the pipeline in under 10 minutes.

---

## Prerequisites

- Python 3.11+
- pip
- Git

---

## Step 1: Clone and Install

```bash
git clone <repository-url>
cd <project-directory>
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 2: Initialize Directories

```bash
python code/setup_directories.py
python code/setup_subdirectories.py
```

---

## Step 3: Run the Pipeline

### Option A: Run All Steps

```bash
# Generate data
python code/data/simulation_mfq.py
python code/data/simulation_stories.py

# Process data
python code/data/ingest.py
python code/data/preprocess.py

# Run models
python code/models/bayesian.py
python code/models/regression.py

# Validate and report
python code/analysis/validation.py
python code/reports/generate_report.py
```

### Option B: Run Individual Steps

See [Usage Examples](usage_examples.md) for detailed commands.

---

## Step 4: Verify Results

```bash
# Check output files
ls data/processed/
ls state/
ls reports/

# View final report
cat reports/final_report.md
```

---

## Step 5: Run Tests

```bash
pytest code/tests/ -v
```

---

## Expected Outputs

After successful execution:

| File | Location | Description |
|------|----------|-------------|
| `synthetic_mfq.csv` | `data/raw/` | Generated MFQ data |
| `synthetic_stories.csv` | `data/raw/` | Generated moral stories |
| `synthetic_vr_logs.csv` | `data/raw/` | Generated VR logs |
| `merged.csv` | `data/processed/` | Merged dataset |
| `preprocessed.csv` | `data/processed/` | Preprocessed dataset |
| `bayesian_results.json` | `state/` | Bayesian model output |
| `regression_results.json` | `state/` | Regression model output |
| `validation_results.json` | `state/` | Validation metrics |
| `final_report.md` | `reports/` | Final analysis report |
| `pipeline_state.yaml` | `state/` | Checksums and metadata |

---

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `FileNotFoundError` | Run `setup_directories.py` and `setup_subdirectories.py` |
| `ValidationError` | Check input data format |
| `ConvergenceWarning` | Increase `n_samples` in config |

---

## Next Steps

- Read the full [README.md](../README.md) for detailed documentation
- Explore [Usage Examples](usage_examples.md) for advanced commands
- Review [Data Schema Reference](data_schema.md) for data structure details
- Run tests to verify your environment: `pytest code/tests/ -v`

---

## Support

For issues or questions:
- Open an issue on the repository
- Check the troubleshooting sections in this guide and the main README
