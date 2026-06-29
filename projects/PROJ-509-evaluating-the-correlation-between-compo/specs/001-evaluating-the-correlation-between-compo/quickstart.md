# Quickstart: Evaluating the Correlation Between Compositional Features

## Prerequisites

- Python 3.10+
- Git
- Access to the Materials Project Zenodo mirror (DOI: 10.5281/zenodo.4053859).

## Installation

1. **Clone and Setup Environment**
   ```bash
   cd projects/PROJ-509-evaluating-the-correlation-between-compo/code
   pip install -r requirements.txt
   ```

2. **Verify Dependencies**
   ```bash
   python -c "import pymatgen; import sklearn; print('OK')"
   ```

## Running the Pipeline

### Step 1: Ingest Data
Download, filter, and sample (if necessary) the MP-2020.12.1 dataset.
```bash
python ingest.py
# Output: data/processed/compounds_clean.csv
# Note: If >60k rows, a stratified sample to 50k is taken.
```

### Step 2: Compute Descriptors
Calculate mean/variance of elemental properties.
```bash
python descriptors.py
# Output: data/processed/compounds_descriptors.csv
```

### Step 3: Train & Evaluate
Train RF and GB models, compute metrics, and run null model baseline.
```bash
python train.py
python evaluate.py
# Output: data/evaluation/model_metrics.json (SSoT)
```

### Step 4: Analyze & Plot
Extract feature importance (with VIF check) and generate PDPs.
```bash
python importance.py
python plots.py
# Output: data/evaluation/pdp_data.json, figures/
```

## Validation

Run the contract tests to ensure data integrity:
```bash
pytest tests/contract/
```

## Troubleshooting

- **Memory Error**: The script automatically samples data if RAM > 6GB. Check logs for "Sampling enabled".
- **Zenodo Unreachable**: Check network or verify the Zenodo URL in `config.yaml`.
- **Missing Properties**: Rare elements may lack data. Check `data/logs/excluded_rows.log`.
