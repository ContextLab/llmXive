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

## Data Setup (Download Only)

```bash
# Attempt to download the official Metallic Glass Database (DOI 10.5281/zenodo.10043838)
# or the MatNVP subset (DOI 10.5281/zenodo.11023456).
# The script will abort with an error if both downloads fail.
python code/download_dataset.py   # creates data/raw/metalic_glass_raw.csv
```

## Full Analysis Pipeline

```bash
# Validate and clean the downloaded dataset
python code/ingest.py               # writes data/processed/cleaned_data.csv

# 1. Compute atomic descriptors
python code/descriptors.py

# 2. Train the Gradient Boosting model with LOFO CV
python code/train.py

# 3. Post‑hoc analyses (VIF flagging, sensitivity, correlation, FDR)
python code/analyze.py

# 4. Generate the final report (figures + markdown)
python code/report.py
```

### One‑liner (if you trust the order)

```bash
python code/descriptors.py && python code/train.py && python code/analyze.py && python code/report.py
```

## Testing

```bash
# Unit tests for descriptor logic, download handling, and validation
pytest tests/unit/

# Integration test (runs the full pipeline on a tiny subset)
pytest tests/integration/
```

## Expected Outputs
- `data/processed/descriptors.csv` – table of computed features.  
- `artifacts/models/best_model.pkl` – trained Gradient Boosting model.  
- `artifacts/metrics/stats.json` – performance metrics, VIF flags, sensitivity variance, FDR‑adjusted p‑values, `correlations`, and bootstrapped feature‑importance CIs.  
- `paper/report.md` – complete scientific report ready for manuscript inclusion, containing all required plots and the exact phrase “These findings are associational only”.  

---
