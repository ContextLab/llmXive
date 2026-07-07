# Quickstart: Quantifying Calibration Drift of Machine Learning Classifiers Over Time

## 1. Prerequisites
- Python 3.11+
- `pip`
- Access to the repository (for code and data directories).
- **IPUMS Account** (if using real data): Register at ` to access yearly extracts.

## 2. Installation

1. **Clone and Navigate**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-778-quantifying-calibration-drift-of-machine
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: `requirements.txt` pins all versions for reproducibility.*

## 3. Running the Pipeline

The pipeline is executed via the main orchestration script.

```bash
# Run the full pipeline (Gate -> Download/Generate -> Train -> Evaluate -> Analyze -> Report)
python code/main.py
```

### Step-by-Step Execution (Manual)

1. **Data Availability Gate**:
 ```bash
 python code/00_data_availability_gate.py
 ```
 *Checks for IPUMS CPS data or synthetic generator configuration. Halts if missing.*

2. **Data Acquisition/Generation**:
 ```bash
 python code/01_data_acquisition.py
 ```
 *Downloads IPUMS yearly snapshots or generates synthetic drift data to `data/raw/` and logs checksums.*

3. **Model Training**:
 ```bash
 python code/02_model_training.py
 ```
 *Trains LR and RF on the earliest snapshot. Saves to `data/models/`.*

4. **Evaluation**:
 ```bash
 python code/03_evaluation.py
 ```
 *Computes ECE (5, 10, 20 bins), Brier, PCA Shift, and Key Feature Shift for all years. Saves to `data/processed/metrics.csv`.*

5. **Statistical Analysis**:
 ```bash
 python code/04_statistical_analysis.py
 ```
 *Fits WLS, computes correlations, detects change-points. Saves to `data/processed/results.json`.*

6. **Report Generation**:
 ```bash
 python code/05_report_generation.py
 ```
 *Generates `docs/report.md` with plots and tables.*

## 4. Verifying Results

- **Check Data Integrity**:
 ```bash
 python -c "import utils.config as cfg; print(cfg.check_data_integrity())"
 ```
- **Reproduce Plots**:
 The `docs/report.md` file contains embedded images generated from `data/processed/`. Re-running `05_report_generation.py` should produce identical plots if the random seed is fixed.

## 5. Troubleshooting

- **Missing Datasets**: If the script fails to download a specific year or the IPUMS data is not found, check the `data/raw/` logs. The `00_data_availability_gate.py` will have halted execution if the primary source is missing.
- **Memory Errors**: If `OSError` occurs during PCA calculation, the script automatically switches to a 10k sample mode.
- **Schema Mismatch**: If column names differ between years, the script will abort with a clear error message (per Edge Case 2).