# Quick Start Guide

## Prerequisites
- Python 3.8+
- pip

## Installation
1. Clone the repository and navigate to the project root.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Directory Setup
The project uses the following data directories:
- `data/raw/`: Raw input data
- `data/processed/`: Processed/merged data
- `data/compliance/`: Compliance logs
- `results/`: Output reports and figures

Run the setup script to ensure directories exist:
```bash
python code/setup/setup_data_dirs.py
```

## Step 1: Generate Synthetic Baseline Data
For testing purposes, generate synthetic baseline data:
```bash
python code/validation/synthetic_baseline.py
```
Output: `data/raw/synthetic_baseline.csv`

## Step 2: Validate Instruments
Verify that scoring functions work correctly:
```bash
python code/validation/validate_instruments.py
```

## Step 3: Run Power Simulation
Estimate statistical power for the study design:
```bash
python code/analysis/power_simulation.py
```
Output: `results/power_analysis.json`

## Step 4: Calculate Change Scores
(Requires merged data from baseline and post-intervention)
```bash
python code/pipeline/merge_data.py
python code/analysis/change_scores.py
```

## Step 5: Run Statistical Analysis
Perform bootstrap analysis, effect size calculation, and corrections:
```bash
python code/analysis/bootstrap_ci.py
python code/analysis/effect_sizes.py
python code/analysis/holm_bonferroni.py
```

## Step 6: Generate Statistical Summary
```bash
python code/analysis/statistical_summary.py
```
Output: `results/statistical_summary.json`

## Step 7: Validate Success Criteria
Check if results meet the study's success criteria:
```bash
python code/validation/validate_success_criteria.py
```

## Step 8: Generate Visualizations
```bash
python code/viz/generate_plots.py
```
Output: Figures in `results/`

## Step 9: Generate Final Report
```bash
python code/report/generate_report.py
```
Output: `results/final_report.md`

## Running Tests
Run all unit and contract tests:
```bash
pytest tests/
```

## Configuration
Edit `code/config/env_config.py` or set environment variables to customize paths and parameters.
