# Quickstart Guide for PROJ-015

## Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

## Setup
1. Create virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Run the Full Pipeline

The pipeline consists of three main stages:
1. Data Generation/Simulation (for development)
2. Data Cleaning
3. Statistical Analysis and Reporting

### Step 1: Generate Simulated Data (Development Only)
```bash
python -m code.simulator.simulator --n 10 --seed 42 --output data/raw/simulated_sessions.json
```

### Step 2: Clean the Data
```bash
python -m code.analysis.clean_data --input data/raw/simulated_sessions.json --output data/processed/cleaned_sessions.csv
```

### Step 3: Run Statistical Analysis
```bash
python -m code.analysis.run_analysis --input data/processed/cleaned_sessions.csv --output data/processed/metrics_summary.csv
```

### Step 4: Generate Visualizations
```bash
python -m code.analysis.run_visualizations --input data/processed/cleaned_sessions.csv --output_dir figures/
```

### Step 5: Generate Final Report
```bash
python -m code.analysis.report_generator --metrics data/processed/metrics_summary.csv --output data/processed/report_summary.txt
```

## Verify Outputs
After running the pipeline, verify that the following files exist:
- `data/raw/simulated_sessions.json`
- `data/processed/cleaned_sessions.csv`
- `data/processed/metrics_summary.csv`
- `data/processed/power_flags.json`
- `figures/completion_time.png`
- `figures/error_count.png`
- `figures/sus_score.png`
- `data/processed/report_summary.txt`

## Run Tests
```bash
python -m pytest tests/ -v
```

## Note on Real Data
For production use, replace the simulated data step with real participant data collection.
The pipeline will fail loudly if real data is not found (see CONTRIBUTING.md).