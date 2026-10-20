# Quickstart: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

## Prerequisites
- Python 3.11 or newer  
- Git  
- Access to a GitHub Actions runner (or a local Unix‑like environment)  

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-367-the-influence-of-algorithmic-recommendat

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

```bash
# 0️⃣ Download and validate the dataset
python code/data_fetcher.py

# 1️⃣ Preprocess: merge categories, compute entropy, build baseline vectors
python code/preprocessing.py

# 2️⃣ Modeling: GPSW + weighted regression (or GLS fallback)
python code/modeling.py

# 3️⃣ Robustness: permutation test + sensitivity sweep
python code/robustness.py

# 4️⃣ Orchestrate end‑to‑end (runs all steps and creates the report)
python code/main.py
```

## Individual Step Commands
| Step | Command | Key Output |
|------|---------|------------|
| Data fetch | `python code/data_fetcher.py` | `data/raw/validated_dataset.parquet` |
| Preprocess | `python code/preprocessing.py` | `data/processed/cleaned_data.parquet`, `diversity_scores.json`, `baseline_vectors.parquet` |
| Modeling | `python code/modeling.py` | `model_results.csv` |
| Robustness | `python code/robustness.py` | `permutation_test_results.json`, `sensitivity_analysis.csv` |
| Full run | `python code/main.py` | `docs/reports/analysis_report.md` |

## Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Integration test (pipeline sanity check)
pytest tests/integration/ -v

# Contract (schema) tests
pytest tests/contract/ -v
```

## Expected Files

- `data/processed/diversity_scores.json` – entropy scores per session.  
- `data/processed/model_results.csv` – regression coefficients, weights, VIF, convergence flag.  
- `data/processed/permutation_test_results.json` – null distribution and p‑value.  
- `data/processed/sensitivity_analysis.csv` – coefficient & p‑value for each semantic‑threshold.  
- `docs/reports/analysis_report.md` – final markdown report (associational language only).  

## Troubleshooting

- **`DataSchemaError`**: Raised if the downloaded parquet does not contain mappable columns. Verify the dataset URL or contact the project lead.  
- **Extreme Weights**: If any GPSW weight > 10 × median, a warning appears in the logs and the effective sample size is reported.  
- **GLS Activation**: If unique users < 30, the log will indicate a switch to GLS; check `model_results.csv` for `convergence_status = false`.  
- **Runtime Exceeds 6 h**: The pipeline measures total wall‑clock time; if it approaches the limit, reduce the permutation iterations or process a random seed‑fixed subset (documented in the report).

---
