# Quickstart Guide - Bayesian Nonparametrics for Anomaly Detection

## Prerequisites

- Python 3.11+
- pip
- Virtual environment (recommended)

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Execution Pipeline

Run the full analysis pipeline in order:

```bash
# 1. Configuration check
python code/src/config.py --check

# 2. Download datasets (or use synthetic fallback)
python code/src/data/download_datasets.py

# 3. Generate synthetic data for testing
python code/src/data/synthetic_generator.py --seed 42 --n_points 1000

# 4. Run DP-GMM model training and inference
python code/src/models/dpgmm.py

# 5. Run baselines for comparison
python code/src/baselines/arima.py
python code/src/baselines/moving_average.py

# 6. Run evaluation metrics
python code/src/evaluation/metrics.py

# 7. Run threshold calibration
python code/src/services/threshold_calibrator.py

# 8. Run robustness analysis (NEW)
python code/src/evaluation/robustness.py --subset-size 100

# 9. Run simulation validation
python code/src/evaluation/simulation.py

# 10. Generate final reports
python code/scripts/execute_evaluation_pipeline.py
```

## Output Artifacts

After successful execution, the following files will be generated:

- `data/processed/results/simulation_snr.csv` - Simulation validation metrics
- `data/processed/results/posterior_trajectory.csv` - DP-GMM posterior trajectories
- `data/processed/results/statistical_report.csv` - Statistical test results
- `data/processed/results/sensitivity_report.csv` - Threshold sensitivity analysis
- `data/processed/results/robustness_report_*.json` - Robustness analysis results
- `data/processed/results/final_report.md` - Comprehensive final report

## Troubleshooting

- **Missing dependencies**: Run `pip install -r code/requirements.txt`
- **Config errors**: Ensure `code/config.yaml` exists and is under 2KB
- **Data errors**: Check that `data/raw/` contains valid datasets or run synthetic generator
- **Memory issues**: Reduce `--subset-size` in robustness analysis

## Verification

To verify the pipeline completed successfully:

```bash
# Check all required output files exist
ls data/processed/results/

# Run compliance checks
python code/scripts/verify_config_compliance.py
python code/scripts/verify_resource_compliance.py
```