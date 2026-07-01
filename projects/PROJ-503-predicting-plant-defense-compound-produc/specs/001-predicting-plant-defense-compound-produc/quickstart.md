# Quickstart: Predicting Plant Defense Compound Production

## Prerequisites

- Python 3.11+
- `pip`
- Internet access (for data download)
- A GitHub Actions runner or a local machine with ≥ 7 GB RAM

## Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd projects/PROJ-503-predicting-plant-defense-compound-produc
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

The pipeline is executed via the main entry point. It will automatically:

1. Check for existing data.  
2. Download new data if missing (or abort with `E‑DATA`).  
3. Perform preprocessing, pairing, and feature selection.  
4. Run modeling, nested CV, permutation testing, and diagnostics.  
5. Abort if any runtime, pairing, power, or checksum constraint is violated (`E‑TIMEOUT`, `E‑PAIRING`, `E‑POWER`, `E‑CHECKSUM`).  

**Command**:
```bash
python code/main.py
```

### Expected Output

- **Logs**: `logs/runtime.log`, `logs/data_pairing.json`, `logs/feature_filtering.csv`, `logs/vif_diagnostics.csv`  
- **Data**: `data/processed/` (CSV files)  
- **Models**: `outputs/models/` (pickle files)  
- **Metrics**: `outputs/metrics/model_results.json`  

## Validation

To verify that the quickstart works on a fresh environment:

1. Run the quickstart script on a clean checkout (no `data/` or `outputs/` present).  
2. After completion, check that `outputs/metrics/model_results.json` exists and contains non‑empty results.  
3. Ensure `logs/runtime.log` does **not** contain an error code.  
4. Execute the validation script:
   ```bash
   pytest tests/integration/test_quickstart_validation.py
   ```
   This test logs success to `docs/quickstart_validation.md`.

## Troubleshooting

- **Error `E‑PAIRING`**: < 95 % of samples could not be paired. Review `logs/data_pairing.json`.  
- **Error `E‑POWER`**: Sample size < 28 or power < 0.8. Review `logs/power_analysis.log`.  
- **Error `E‑TIMEOUT`**: Total CPU time exceeded 4 h. Consider reducing permutation iterations or using a more powerful runner.  
- **Error `E‑CHECKSUM`**: < 99 % of downloaded files failed checksum verification. Review `logs/checksum_report.log`.  
- **Error `E‑DATA`**: No suitable paired GEO/Metabolomics Workbench study found. The pipeline cannot proceed.

--- End of Quickstart ---