# Quickstart: Predicting Rate Constants of SN1 Reactions from Molecular Structure

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or local environment with 2+ cores and 8GB RAM.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-373-predicting-rate-constants-of-sn1-reactio
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Setup

The data is fetched automatically during the first run. No manual download is required.
- **Source**: `Elzorro99/DTS-SN1-15-01-2024` (HuggingFace).
- **Cache**: Data is cached in `data/raw/`.

## Running the Pipeline

### 1. Full Pipeline (Ingest → Train → Analyze)
```bash
python code/main.py --config code/config.py
```
This script:
- Downloads and cleans data.
- Trains the MPNN with random search over multiple configurations.
- Evaluates against baselines.
- Runs SHAP, VIF, and sensitivity analysis.
- Saves artifacts to `artifacts/`.

### 2. Individual Steps

**Ingest & Featurize**:
```bash
python code/ingest.py
python code/featurize.py
```

**Train Model**:
```bash
python code/train.py --config code/config.py
```

**Evaluate & Analyze**:
```bash
python code/evaluate.py
python code/analyze.py
```

## Expected Outputs

- `artifacts/metrics.json`: Performance metrics.
- `artifacts/model_weights.pt`: Best model weights.
- `artifacts/reports/shap_summary.png`: Feature importance plot.
- `artifacts/reports/sensitivity_analysis.csv`: Robustness check results.
- `data/processed/exclusion_report.csv`: Rows removed and reasons.

## Troubleshooting

- **OOM Error**: Reduce `hidden_dim` in `code/config.py` (default: 64).
- **CUDA Error**: Ensure `torch` is installed with CPU support (`torch==2.2.0+cpu`). The pipeline is designed for CPU only.
- **Data Download Failed**: Check internet connection. The script uses `streaming=True` to avoid full downloads.