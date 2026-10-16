# Quickstart: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Prerequisites

- Python 3.11+  
- 2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk (GitHub Actions free‑tier)  
- Internet access (no credentials required)

## Installation

```bash
# Clone the repository
git clone <repo‑url>
cd projects/PROJ-078-predicting-polymer-degradation-pathways-/

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Data Setup

```bash
# 1. Download verified CSV sources and attempt API fetches
python code/ingest.py --source verified_csv

# 2. Verify integrity and view summary
python code/utils.py --check-data
```

The ingestion script will:

- Pull the two verified CSVs (NIST, WebBook).  
- Filter for polyesters (ester SMARTS `C(=O)O`).  
- Apply synthetic degradation labels where missing and flag them.  
- Impute missing temperature/pH/UV with defaults.  
- Save raw data to `data/raw/` and processed records to `data/processed/`.

## Augmentation (if needed)

```bash
python code/augment.py --expand 2x
```

- Performs edge dropout (p = 0.1) and subgraph sampling to double the dataset.  
- Runtime is logged; must complete within 30 min.

## Model Training

```bash
# 5‑fold cross‑validation (or LOO if n < 150)
python code/train.py --cv 5 --epochs 100
```

- Trains the lightweight GNN (≤ 3 layers, hidden ≤ 128).  
- Saves the best checkpoint to `code/models/model.pt`.  
- Logs macro‑F1 and loss convergence; ensures |Δloss|/loss < 0.05 over the last 5 epochs.

## Feature Attribution & Validation

```bash
# Compute Integrated Gradients
python code/attribution.py --method integrated_gradients

# Perform χ² statistical validation (≥1000 null iterations)
python code/validate.py --chi2-iterations 1000
```

- Generates motif importance scores.  
- Checks that ester bonds rank in the top attribution scores for ≥ 90 % of hydrolysis cases.  
- Produces `docs/reports/final_report.md`.

## Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests (full pipeline)
pytest tests/integration/

# Contract tests (schema validation)
pytest tests/contract/
```

All tests must pass before committing.

## Troubleshooting

- **API rate limits** – The ingestion script implements exponential backoff (max 3 retries). Check `logs/ingest.log` for backoff details.  
- **Invalid SMILES** – Skipped records are logged; processing continues.  
- **Small dataset** – If *n* < 150, power analysis warning appears and LOO validation is automatically selected.  
- **Memory errors** – The script will subsample the dataset to stay under 7 GB RAM; see `logs/memory.log`.

---
