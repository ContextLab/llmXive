# Quickstart: Quantify Dataset Sparsity Impact

## Prerequisites
- Python 3.11+
- Materials Project API Key (set as `MP_API_KEY` environment variable)
- Sufficient RAM (for full dataset processing)

## Installation

1.  **Clone the repository** and navigate to the project root.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins specific versions of `pymatgen`, `matminer`, `scikit-learn`, and `gpytorch`.*

## Running the Pipeline

### 1. Data Ingestion
Download and process the Materials Project data:
```bash
python code/data_ingestion.py
```
*Output*: `data/processed/full_pool_final.csv` and `data/metadata/ingestion_log.json`.

### 2. Test Set Partitioning
Create a fixed holdout set (a representative portion of the full pool):
```bash
python code/test_split.py
```
*Output*: `data/processed/test_set.csv` and `data/metadata/test_set_metadata.json`.

### 3. Sparsity Subsampling
Generate the nested stratified subsets across a range of sampling fractions from low to full coverage.:
```bash
python code/sparsity_sampling.py --levels 5 10 20 30 40 50 100 --seeds 42 123 456
```
*Output*: `data/metadata/sparsity_<level>_<seed>.json` and subset CSVs.

### 4. Model Training
Train GPR (FITC) and RF models:
```bash
python code/model_training.py
```
*Output*: Model artifacts in `data/results/models/` and metrics in `data/results/metrics.csv`.

### 5. Analysis
Generate plots, LMM results, and calibration reports:
```bash
python code/analysis.py
```
*Output*: Learning curves in `data/results/plots/`, ANOVA summary in `data/results/statistics.json`, and `data/results/calibration_report.json`.

## Verification
To verify the pipeline:
```bash
pytest tests/integration/test_pipeline.py
```
This ensures that the full pipeline runs without errors and produces the expected artifacts.