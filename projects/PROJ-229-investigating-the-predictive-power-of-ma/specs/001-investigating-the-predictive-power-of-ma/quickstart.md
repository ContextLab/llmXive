# Quickstart: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to GitHub Actions (for CI) or a local Linux machine with 7 GB RAM.
- (Optional) Materials Project API Key (set as `MP_API_KEY` env var).

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd phase-change-predictive-power
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` pins all versions for reproducibility.*

## Running the Pipeline

### Step 1: Fetch Data
```bash
python code/data/fetch_materials.py
```
This downloads the Materials Project subset and NIST data to `data/raw/`.

### Step 2: Compute Descriptors
```bash
python code/data/compute_descriptors.py
```
Generates `data/processed/features.parquet`. Includes stability checks.

### Step 3: Train Models
```bash
python code/models/train_baselines.py
python code/models/train_symbolic.py
```
Outputs models and metrics to `data/results/`.

### Step 4: Validate & Analyze
```bash
python code/validate/validate_external.py
python code/validate/sensitivity_analysis.py
```
Generates the validation report and sensitivity analysis.

### Step 5: Generate Report
```bash
python code/main.py --generate-report
```
Creates `docs/research_report.md` with all findings.

## Testing

Run the full test suite:
```bash
pytest tests/ -v --cov=code
```

- **Contract Tests**: `tests/contract/` validates schemas against `contracts/`.
- **Integration Tests**: `tests/integration/` runs the full pipeline end-to-end.
- **Unit Tests**: `tests/unit/` checks individual functions.

## Troubleshooting

- **Memory Error**: Reduce the batch size in `compute_descriptors.py`.
- **API Rate Limit**: The script automatically switches to the `matbench` HuggingFace dataset.
- **PySR Timeout**: The script flags the limitation and falls back to SHAP analysis.
- **Missing Data**: Check `data/external/literature_pcms_raw.csv` for fetch errors.
