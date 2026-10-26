# Quickstart: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

## Prerequisites
- Python 3.11 (or newer)
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

The pipeline is orchestrated via the scripts in `code/`. Each script writes its output to `data/` or `results/` and updates the contract state.

### 0️⃣ Reference‑Validator Gates
```bash
python code/verify_references.py --stage dataset   # checks ds001734 URL (FR‑012‑1)
python code/verify_references.py --stage citations # checks bibliography (FR‑012‑3)
```

### 1️⃣ Data Acquisition
```bash
python code/download.py   # downloads OpenNeuro ds001734, verifies checksums, records hash (FR‑001, FR‑013)
```
*The script verifies that both “simple” and “complex” condition labels are present; if either is missing it aborts with a clear error (FR‑008).*

### 2️⃣ Preprocessing
```bash
python code/preprocess.py   # band‑pass, ICA, mastoid re‑reference, baseline correction, epoching (FR‑002‑FR‑003)
```

### 3️⃣ Analysis
```bash
python code/analysis.py
```
Performs:
- MMN amplitude/latency extraction (FR‑004)  
- Noise‑floor SNR validation (FR‑011, SC‑001)  
- Leave‑one‑out canonical topography generation (FR‑009)  
- Topographic consistency & validity checks (SC‑004)  
- Paired t‑tests with FDR (FR‑005, SC‑002)  
- Cohen’s d vs. benchmark (FR‑010, SC‑003)  
- Optional mixed‑effects robustness model (covariates)  

Outputs:
- `results/metrics.csv` (validated by `contracts/output.schema.yaml`)  
- `results/stats.json` (validated by `contracts/stats.schema.yaml`)  

### 4️⃣ Visualization
```bash
python code/visualize.py
```
Generates PNG/SVG files in `results/figures/`:
- ERP waveforms with MMN window highlighted  
- Scalp topography maps for the simple and complex conditions  
- Significance heatmaps  

### 5️⃣ Contract Tests (Verification)
```bash
pytest code/tests/
```
Tests verify:
- `data/raw/` metadata against `contracts/dataset.schema.yaml`  
- `results/metrics.csv` against `contracts/output.schema.yaml`  
- `results/stats.json` against `contracts/stats.schema.yaml`  
- Presence of required fields, correct data types, and logical constraints (e.g., `snr_ratio >= 3.0`).  

All tests must pass before the pipeline is considered research‑ready.

---


