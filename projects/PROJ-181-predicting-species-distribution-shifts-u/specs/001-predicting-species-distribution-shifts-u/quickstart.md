# Quickstart: Predicting Species Distribution Shifts

## Prerequisites

- Python 3.11+
- `pip`
- Internet access (for GBIF and WorldClim downloads)
- ~14GB disk space (for climate rasters)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-181-predicting-species-distribution-shifts-u
    ```

2.  **Create virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Edit `code/config.py` to define:
- `SPECIES_LIST`: A list of scientific names (e.g., `["Turdus migratorius", "Zonotrichia albicollis"]`).
- `DATA_DIR`: Path to `data/`.
- `CLIMATE_DIR`: Path to `data/raw/climate/`.

## Running the Pipeline

### 1. Download Data
Fetch occurrence records and **subset** climate rasters.
```bash
python code/download.py
```
*Output*: `data/raw/occurrence_1970_2000.csv`, `data/raw/occurrence_2005_2020.csv`, and **subsetted** climate rasters.

### 2. Preprocess
Filter, thin, and check data sufficiency (dynamic threshold).
```bash
python code/preprocess.py
```
*Output*: `data/processed/thinned_*.csv`, `metrics/data_sufficiency.json`.

### 3. Train Models
Train Random Forest, Bioclim, and Target-Group Logistic Regression models with spatial CV.
```bash
python code/train.py
```
*Output*: `models/*.pkl`, `logs/gpu_check.log`.

### 4. Evaluate
Project to future climate, compute metrics, and run permutation tests.
```bash
python code/evaluate.py
```
*Output*: `metrics/model_metrics.json`, `figures/suitability_maps/`.

## Verification

- Check `logs/gpu_check.log` to ensure no CUDA errors occurred.
- Verify `metrics/data_sufficiency.json` contains `INSUFFICIENT_DATA` flags for rare species.
- Ensure `metrics/model_metrics.json` has AUC/TSS values for all trained models.
