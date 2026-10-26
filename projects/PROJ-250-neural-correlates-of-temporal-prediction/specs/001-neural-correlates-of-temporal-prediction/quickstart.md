# Quickstart: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

## Prerequisites
- Python 3.11 (or newer)
- Git
- Access to a Linux environment with at least 7 GB RAM (GitHub Actions free tier works out‑of‑the‑box)

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-250-neural-correlates-of-temporal-prediction
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

## Running the Full Pipeline

The pipeline is orchestrated via the scripts in `code/`. Each script writes its output to the `data/` or `results/` folder and updates the contract state.

### 0️⃣ Reference‑Validator Gates
```bash
python code/verify_references.py --stage dataset
python code/verify_references.py --stage citations
```

### 1️⃣ Data Acquisition
```bash
python code/download.py --subjects <N>
```

*If the dataset lacks the required “complex” condition the script aborts with the FR‑008 error message.*

### 2️⃣ Preprocessing
```bash
python code/preprocess.py
```

### 3️⃣ Analysis
```bash
python code/analysis.py
```

### 4️⃣ Visualization
```bash
python code/visualize.py
```

### 5️⃣ Contract Tests (Verification)
```bash
pytest code/tests/
```

All tests must pass before the pipeline is considered research‑ready.
