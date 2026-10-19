# Quickstart: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

## Prerequisites
- Python 3.10+
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

1. **Automatic download** (preferred):
   ```bash
   python code/ingest.py --download
   ```
   The script uses the Zenodo client to fetch DOI 10.5281/zenodo.10043838.  
   If the DOI is unreachable, the script aborts with a clear error; no fallback dataset is used.

2. **Manual placement** (if automatic download fails):
   - Download the CSV/ZIP yourself from the Zenodo landing page.
   - Place the file(s) inside `data/raw/`.
   - Verify checksums:
     ```bash
     python code/ingest.py --verify-only
     ```

## Running the Full Pipeline

```bash
python code/ingest.py && \
python code/descriptors.py && \
python code/train.py && \
python code/analyze.py && \
python code/report.py
```

### Individual Commands
| Step | Command | Purpose |
|------|---------|---------|
| Ingest | `python code/ingest.py` | Load, validate, and clean raw data (FR‑001). |
| Descriptors | `python code/descriptors.py` | Compute atomic descriptors (FR‑002). |
| Train | `python code/train.py` | LOFO CV + GBM training + hyper‑parameter grid (FR‑003). |
| Analyze | `python code/analyze.py` | VIF, Bonferroni correction, sensitivity sweep, bootstrapping (FR‑006‑009). |
| Report | `python code/report.py` | Produce `paper/report.md` with plots and the required associational statement (FR‑004). |

## Testing

```bash
# Unit tests for descriptor logic
pytest tests/unit/

# Integration test (requires data)
pytest tests/integration/
```

## Expected Outputs
- `data/processed/descriptors.csv` – feature table.  
- `artifacts/models/best_model.pkl` – trained GBM.  
- `artifacts/metrics/stats.json` – performance, VIF, p‑values, sensitivity variance.  
- `paper/report.md` – complete scientific report ready for inclusion in the manuscript.
