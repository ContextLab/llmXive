# Quickstart: Neuro-Symbolic Learning Networks

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with similar specs).
- (Optional) Access to Kaggle GPU for manual fallback.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-559-neuro-symbolic-learning-networks-bridgin
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

The pipeline is orchestrated by `code/main.py`. It performs the following steps:
1. Download datasets (with timeout handling).
2. Generate explanations (Neural, Symbolic, Neuro-Symbolic).
3. Calibrate BKT simulator (if pilot data exists).
4. Run simulation (a substantial cohort of students per condition).
5. Merge with real student data (if available).
6. Run mixed-effects regression analysis.

### Execute the full pipeline:
```bash
python code/main.py
```

### Run specific stages:
- **Download Data**: `python code/main.py --stage download`
- **Generate Explanations**: `python code/main.py --stage generate`
- **Run Simulation**: `python code/main.py --stage simulate`
- **Run Analysis**: `python code/main.py --stage analyze`

## Expected Outputs

- `data/derived/explanations/`: Contains `explanation_neural.txt`, `explanation_symbolic.txt`, `explanation_neuro_symbolic.txt` for each problem.
- `data/derived/logs/simulated_logs.csv`: The main dataset of simulated interactions.
- `results/regression_summary.md`: The final analysis report with effect sizes and p-values.

## Troubleshooting

- **Dataset Download Timeout**: If the download exceeds 300 seconds, the pipeline will abort with `ERROR: Failed to download [dataset name] within 300 seconds – aborting pipeline.`. Check your network connection or try a different dataset subset.
- **Memory Error**: If you encounter OOM errors, reduce the sample size in the configuration or use the `--streaming` flag (default).
- **Missing Pilot Data**: If `data/pilot/raw_pilot_data.csv` is missing, the calibration step will be skipped, and the simulation will use default BKT parameters. This may affect the validity of the results. Ensure the file is provided via T030a.
- **Missing Real Data**: If `data/real/raw_real_data.csv` is missing, the final analysis will proceed with simulated data only, noting the limitation.
