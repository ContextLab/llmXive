# Quickstart: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Prerequisites
- Python 3.11 or newer  
- Git  
- Access to a **verified** NIST SRD 150 dataset (or a pre‑cached copy in `data/raw/`).  

## Installation

1. **Clone the repository**  
   ```bash
   git clone <repo-url>
   cd projects/PROJ-415-predicting-the-impact-of-alloying-on-the
   ```

2. **Create and activate a virtual environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

## Data Setup

1. **Verify Data Availability**  
   Ensure `data/raw/nist_diffusion_raw.csv` (or the file referenced by `NIST_SRD150_URL`) exists.  
   *If the file is missing, the pipeline will abort with*  
   `"ERROR: No verified real dataset found. Synthetic data is not permitted for this research goal."`

2. **Run the Ingestion & Availability Check**  
   ```bash
   python code/data/streaming_loader.py
   ```
   This script:
   - Checks for at least one FCC self‑diffusion row **and** one FCC solute‑diffusion row.  
   - Writes `data/curated/baselines.csv`, `data/curated/filtered.csv`, and `data/curated/data_provenance.json`.  

## Running the Pipeline

### 1. Feature Engineering
```bash
python code/processing/feature_engineering.py
```
Generates atomic descriptors and `baseline_shift_eV`.

### 2. Model Training
```bash
# Random Forest
python code/models/train_rf.py

# Gradient Boosting
python code/models/train_gb.py

# Linear Regression (statistical inference)
python code/models/train_linear.py
```

### 3. Validation & Sensitivity Analysis
```bash
python code/validation/sensitivity_analysis.py
```
Creates `validation/stability_index_report.json` and associated plots.

## Verification
Run the test suite to ensure all components work:
```bash
pytest tests/ -v
```

## Expected Outputs
- `data/curated/filtered.csv` – curated training dataset.  
- `data/curated/baselines.csv` – pure‑host baseline energies.  
- `models/final_rf.pkl`, `models/final_gb.pkl`, `models/linear_coef.json` – trained model artifacts.  
- `validation/stability_index_report.json` – threshold sweep results and Stability Index.  
- `plots/` – figures for feature importance, threshold sensitivity, etc.

---
