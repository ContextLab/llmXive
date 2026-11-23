# Quickstart: Multi-Property Trade-Offs in Alloy Design

## Prerequisites

- Python 3.11+
- Git
- ~14 GB Disk Space (for data and virtual environment)
- ~8 GB RAM (for processing)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-786-multi-property-trade-offs-in-alloy-desig
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The entire pipeline is orchestrated via `code/main.py`.

### 1. Full Pipeline Execution
```bash
cd code
python main.py
```
This script will:
- Download and verify OQMD data.
- Perform encoding and feasibility checks.
- Train surrogates and run LOSO-CV.
- Perform clustering (HDBSCAN on residuals) and sensitivity analysis.
- Generate Pareto frontier.

### 2. Individual Steps (Optional)

**Ingestion & Encoding**:
```bash
python ingestion/load_oqmd.py
python ingestion/encode_composition.py
```
*Output*: `data/processed/encoded_alloys.csv`

**Model Training**:
```bash
python modeling/train_surrogates.py
```
*Output*: `data/processed/model_validation_report.json`

**Analysis & Optimization**:
```bash
python analysis/feasibility_check.py
python analysis/clustering.py
python analysis/sensitivity.py
python modeling/pareto_optimize.py
```

## Verifying Results

### Check Data Integrity
Ensure all required files exist:
```bash
ls data/processed/
# Expected:
# - encoded_alloys.csv
# - feasibility_report.json
# - model_validation_report.json
# - cluster_analysis.json
# - sensitivity_analysis.csv
# - pareto_frontier.csv
```

### Run Tests
```bash
pytest tests/
```
- **Unit Tests**: Validate encoding and physics checks.
- **Integration Tests**: Verify `encoded_alloys.csv` columns and `model_validation_report.json` structure.
- **Contract Tests**: Validate JSON/CSV against YAML schemas.

## Expected Outputs

1. **`data/processed/encoded_alloys.csv`**: Clean, encoded dataset.
2. **`data/processed/feasibility_report.json`**: Global correlation and analysis mode.
3. **`data/processed/model_validation_report.json`**: Predictions, R² scores, uncertainty metrics.
4. **`data/processed/sensitivity_analysis.csv`**: Robustness scores for decoupling thresholds.
5. **`data/processed/pareto_frontier.csv`**: Optimal trade-off points.
6. **`data/processed/cluster_analysis.json`**: Decoupled regions.

## Troubleshooting

- **Error: "Insufficient data for research validity"**
  - *Cause*: Filtered dataset has < 500 valid entries.
  - *Fix*: Check OQMD source; ensure `bulk_modulus` and `shear_modulus` columns are present and non-null.

- **Error: "LOSO-CV R² < 0.6"**
  - *Cause*: Model underfitting or data quality issues.
  - *Fix*: The pipeline will log this but continue to Poisson Anomaly analysis. Check `model_validation_report.json` for per-system scores.

- **Memory Error**
  - *Cause*: Dataset too large for RAM.
  - *Fix*: Ensure `streaming=True` is used in data loading or reduce batch size in `ingestion/load_oqmd.py`.