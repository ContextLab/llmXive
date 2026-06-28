# Quickstart: Predicting the Glass Forming Region of Multi-Component Alloys via Machine Learning

## Prerequisites

- Python 3.11+
- 7 GB+ available RAM
- 14 GB+ available disk space
- Git

## Installation

```bash
# Clone repository
git clone <repository-url>
cd projects/PROJ-544-predicting-the-glass-forming-region-of-m

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Data Setup

**Note**: No verified alloy composition datasets are currently available in the verified datasets block. For testing, use the synthetic data generator:

```bash
# Generate synthetic test data
python code/scripts/generate_synthetic_data.py --output data/raw/synthetic_alloys.csv --n_samples 1000
```

For production data, download from verified sources (once identified) and place in `data/raw/`:

```bash
# Place verified dataset in data/raw/
# Run checksum generation
python code/scripts/checksum_data.py --input data/raw/your_dataset.csv
```

## Running the Pipeline

### Step 0: Dataset acquisition & RAM‑constrained sampling
```bash
python code/scripts/download_and_verify.py   # fetches verified datasets (when URLs are added)
python code/scripts/sample_dataset.py --max_ram_gb 7 --input data/raw/your_dataset.csv --output data/samples/sample.csv
python code/scripts/filter_labels.py --input data/samples/sample.csv --output data/raw/filtered_alloys.csv
```

### Step 1: Compute Thermodynamic Descriptors
```bash
python code/descriptors/compute.py \
  --input data/raw/filtered_alloys.csv \
  --output data/derived/descriptors.csv
```

### Step 2: Class Imbalance Check
```bash
python code/descriptors/check_imbalance.py \
  --input data/derived/descriptors.csv \
  --output data/derived/imbalance_report.json
```

### Step 3: Collinearity Diagnostics & VIF Filtering (with PCA fallback)
```bash
python code/descriptors/vif_filter.py \
  --input data/derived/descriptors.csv \
  --output data/derived/descriptors_vif_filtered.csv
```

### Step 4: Model Training
```bash
python code/models/train.py \
  --input data/derived/descriptors_vif_filtered.csv \
  --output models/trained_models.pkl
```

### Step 5: Model Evaluation
```bash
python code/models/evaluate.py \
  --model models/trained_models.pkl \
  --input data/derived/descriptors_vif_filtered.csv \
  --output results/performance_metrics.json
```

### Step 6: Feature Importance & SHAP Visualizations
```bash
python code/models/importance.py \
  --model models/trained_models.pkl \
  --input data/derived/descriptors_vif_filtered.csv \
  --output results/shap_plots/
```

### Step 7: δ‑Threshold Sensitivity Analysis
```bash
python code/scripts/sensitivity_analysis.py \
  --model models/trained_models.pkl \
  --delta_values 0.01 0.05 0.1 \
  --output results/sensitivity_report.json
```

### Step 8: Reproducibility Check (3 independent runs)
```bash
python code/scripts/reproducibility_check.py \
  --pipeline_dir . \
  --runs 3 \
  --output results/reproducibility_summary.json
```

## Running Tests

```bash
# Contract tests
pytest tests/contract/

# Integration tests
pytest tests/integration/

# Unit tests
pytest tests/unit/
```

## CI Execution

```bash
# Run full pipeline on GitHub Actions
./code/scripts/run-ci.sh
```

## Output Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| Descriptors | `data/derived/descriptors.csv` | Computed thermodynamic features (or PCA components if VIF fallback) |
| Models | `models/trained_models.pkl` | Trained RF and GB classifiers |
| Performance | `results/performance_metrics.json` | ROC‑AUC, precision, recall, imbalance flag, power sufficiency |
| SHAP Plots | `results/shap_plots/` | Feature importance visualizations |
| Sensitivity | `results/sensitivity_report.json` | δ‑threshold robustness analysis |
| Reproducibility Summary | `results/reproducibility_summary.json` | Consistency of feature importance across runs |

## Known Limitations

1. **Dataset Availability**: Production deployment requires verified alloy composition datasets (Materials Project or NIST). Current pipeline uses synthetic data for CI.
2. **Causal Inference**: Model predicts associational propensity only; cooling‑rate and thermal‑history are missing confounds.
3. **Compute Constraints**: Pipeline designed for 2‑core CPU, 7 GB RAM. Larger datasets require sampling (Phase 0).
