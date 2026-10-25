# Quickstart: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Prerequisites
- Python 3.11 or newer  
- `git` and internet access (to download the Materials Project data via `matminer`)  

## Installation
```bash
# Clone the repository
git clone 
cd PROJ-420-predicting-the-effect-of-alloying-on-the

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Running the Full Pipeline
```bash
python code/main.py
```
`main.py` executes the steps in the exact order required by the implementation plan:
1. **Download** raw data (`code/data/download.py`).  
2. **Clean & filter** (`code/data/clean.py`), producing `data/processed/alloys_clean.parquet`.  
3. **Compute VIF** and **ILR transform** (`code/data/transform.py`), producing `alloys_ilr.parquet`.  
4. **Train & validate** the Random Forest (`code/analysis/train.py`).  
5. **Interpret** feature importance (`code/analysis/interpret.py`).  
6. **Assemble** the final markdown report (`results/final_report.md`).  

## Expected Outputs
- `data/processed/alloys_clean.parquet` – cleaned dataset.  
- `data/processed/alloys_ilr.parquet` – ILR‑augmented dataset.  
- `results/model_metrics.json` – CV MAE, test MAE, sample counts.  
- `results/feature_importance.json` – back‑transformed importance scores and ranking.  
- `results/collinearity_diagnostic.json` – VIF values and flag.  
- `results/final_report.md` – associational narrative with tables/figures.  
- `data/logs/app.log` – RotatingFileHandler log (max 5 MB, 3 backups).  
- `data/logs/exclusion_log.txt` – CSV of all excluded records with reason.  

## Validation
```bash
pytest tests/test_contracts.py
```
The test suite validates each JSON artifact against the corresponding YAML schema in `contracts/`.

## Troubleshooting
- **No data downloaded**: Check `app.log` for network errors; the pipeline will abort with a clear message if the Materials Project download fails (see Spec Amendment AMP‑001).  
- **VIF flagged**: High VIF is expected for raw fractions; the model still uses ILR features.  
- **MAE > 0.05**: The report will contain a methodological‑concern flag; no failure occurs.  

---
