# Quickstart: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

## Prerequisites
- Python 3.11+
- Git
- Internet access (to download NIST and journal supplement files)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-393-predicting-the-influence-of-composition-/code

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Data Preparation
1. **Automatic download (recommended)**  
   ```bash
   python -m src.ingestion.fetch_nist   # pulls NIST CSV from the verified HuggingFace URL
   python -m src.ingestion.fetch_journal   # pulls the journal supplement CSV (you must provide the DOI in `config.yaml`)
   ```
   The scripts place files under `data/raw/` and record SHA‑256 checksums.

2. **Manual addition (if automatic fails)**  
   - Place any downloaded CSV/Excel files into `data/raw/`.  
   - Ensure filenames contain `nist`, `journal`, or `manual` to be recognized by the pipeline.

## Running the Full Pipeline

```bash
python main.py
```

`main.py` orchestrates the stages:
1. Ingestion → `data/raw/`  
2. Preprocessing (unit conversion, **mean imputation**, DFT filtering) → `data/processed/alloys_clean.csv`  
3. Feature engineering → `data/processed/alloys_features.csv`  
4. Model training + hyperparameter tuning → `models/`  
5. Statistical validation (F‑test, bootstrapping, PDP) → `docs/reports/`  
6. Final report assembly → `docs/reports/final_report.md`

## Expected Outputs
- `data/processed/alloys_features.csv` – dataset used for modeling.  
- `models/linear_regression.pkl` & `models/random_forest.pkl` – trained model artifacts.  
- `docs/reports/metrics.json` – R², MAE, F‑statistic, p‑value, bootstrap CI.  
- `docs/reports/pdp_coercivity.png` & `pdp_saturation.png` – partial dependence plots.  
- `docs/reports/final_report.md` – complete narrative with all mandatory sections (data scarcity warning, statistical limitations, microstructure note).  
- `docs/reports/imputation_report.json` – shows the imputation rate (must be < 15 %).  

## Troubleshooting
- **Missing elemental property file** – Ensure `data/raw/elemental_properties.csv` exists; it is shipped with the repository.  
- **Imputation rate > 15 %** – Check source files for excessive missing columns; consider adding more data or revising the source list.  
- **Dataset size < 50** – The pipeline will still run but will generate `data_scarcity_warning.md` and flag reduced statistical power.  

---
