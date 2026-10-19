# Quickstart: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

## Prerequisites
- Python 3.11+
- Git
- Terminal (local or GitHub Actions)

## Installation

```bash
# Clone the repository and checkout the feature branch
git checkout 001-predict-tg-metallic-glasses
cd projects/PROJ-342-predicting-the-influence-of-alloying-on-/

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Data Setup

The pipeline creates its own synthetic dataset; no external download is required.

```bash
# Generate and validate the synthetic dataset
python code/generate_synthetic.py   # creates data/raw/synthetic_mg.csv
python code/ingest.py               # validates and produces cleaned_data.csv
```

## Running the Full Pipeline

```bash
python code/descriptors.py && \
python code/train.py && \
python code/analyze.py && \
python code/report.py
```

### Individual Commands
| Step | Command | Purpose |
|------|---------|---------|
| Synthetic generation | `python code/generate_synthetic.py` | Create reproducible composition‑Tg data (FR‑001). |
| Ingestion | `python code/ingest.py` | Validate against schema, drop invalid rows (FR‑001). |
| Descriptors | `python code/descriptors.py` | Compute atomic descriptors; log weighted mean radius (FR‑002). |
| Train | `python code/train.py` | LOFO CV + GBM training + hyper‑parameter grid (FR‑003). |
| Analyze | `python code/analyze.py` | VIF, Bonferroni correction, sensitivity sweep, bootstrap CIs (FR‑006‑009). |
| Report | `python code/report.py` | Produce `paper/report.md` with required plots and associational statement (FR‑004). |

## Testing

```bash
# Unit tests for descriptor logic and synthetic generator
pytest tests/unit/

# Integration test (runs full pipeline on a tiny subset)
pytest tests/integration/
```

## Expected Outputs
- `data/processed/descriptors.csv` – feature table.  
- `artifacts/models/best_model.pkl` – trained Gradient Boosting model.  
- `artifacts/metrics/stats.json` – performance metrics, VIF, corrected p‑values, sensitivity variance.  
- `paper/report.md` – complete scientific report ready for manuscript inclusion.  

---
