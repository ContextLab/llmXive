# Quickstart: Predicting Molecular Descriptors

## Prerequisites

- Python 3.11+
- `pip`
- Git

## Installation

1. **Clone the repository** (or navigate to the project directory).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline is executed in four sequential stages. Ensure you have sufficient disk space and RAM.

### Step 1: Data Download & Verification
Downloads the QM9 dataset from the verified HuggingFace source and computes checksums.
```bash
python code/download.py
```
*Output*: `data/raw/qm9_full.parquet`

### Step 2: Feature Extraction
Generates 2D fingerprints and 3D graph features. Includes memory monitoring.
```bash
python code/extract.py
```
*Output*: `data/processed/2d_features.npy`, `data/processed/3d_graphs.pkl`, `data/processed/labels.npy`

### Step 3: Model Training & Cross-Validation
Trains Random Forest models with 5-fold CV.
```bash
python code/train.py
```
*Output*: `artifacts/models/*.pkl`, `artifacts/metrics/cv_results.json`

### Step 4: Analysis & Reporting
Computes relative error increase, generates parity plots, and checks stability.
```bash
python code/analyze.py
```
*Output*: `artifacts/metrics/comparison_table.csv`, `artifacts/plots/*.png`

## Verification

To verify the installation and pipeline integrity:
```bash
pytest tests/ -v
```
Ensure all tests pass, particularly `test_memory_monitor` and `test_feature_alignment`.

## Troubleshooting

- **Memory Error**: If the process is killed due to OOM, the `extract.py` script automatically downsamples the dataset. Check `data/processed/downsample_log.txt` for details.
- **Download Failure**: If the HuggingFace URL is unreachable, the script retries 3 times. If it fails, check your internet connection or proxy settings.
