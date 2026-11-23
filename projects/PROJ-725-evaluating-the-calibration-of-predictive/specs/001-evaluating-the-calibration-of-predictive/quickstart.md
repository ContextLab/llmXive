# Quickstart: Evaluating the Calibration of Predictive Uncertainty Intervals

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with sufficient RAM).

## Installation

1. **Clone the repository** and navigate to the project directory:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-725-evaluating-the-calibration-of-predictive
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

### 1. Download and Preprocess Data
Downloads datasets from the verified Hugging Face sources and performs the 70/30 split.
```bash
python code/main.py --action download
```
*Output*: `data/raw/` and `data/processed/` directories populated.

### 2. Run Uncertainty Methods
Fits all four methods (QR, BLR, GPR, SCP) and generates intervals.
```bash
python code/main.py --action fit
```
*Output*: `artifacts/intervals/` with parquet files for each method-dataset pair.

### 3. Analyze Calibration
Computes coverage, interval scores, binomial tests, and heteroscedasticity analysis.
```bash
python code/main.py --action analyze
```
*Output*: `artifacts/metrics/` and `artifacts/final_results.csv`.

### 4. Generate Report
Aggregates results and prints a summary of mis-calibrated methods.
```bash
python code/main.py --action report
```

## Verification

To verify the installation and pipeline integrity:
```bash
pytest tests/ -v
```

## Troubleshooting

- **Memory Error**: If GPR fails, the pipeline logs a warning and skips that method for the specific dataset. No manual intervention is needed.
- **Dataset Incompatible**: If a dataset lacks a numeric target, it is skipped and logged. Check `logs/run.log` for details.
- **Missing Data**: Ensure internet connectivity for the initial `download` step.
