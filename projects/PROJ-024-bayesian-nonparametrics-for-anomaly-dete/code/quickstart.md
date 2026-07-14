# Quickstart Guide: Bayesian Nonparametrics for Anomaly Detection

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

```bash
cd code
pip install -r requirements.txt
```

## Quick Start

1. **Generate Synthetic Data** (if real data not available):
 ```bash
 python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05
 ```

2. **Run Ground Truth Simulation** (Phase 0):
 ```bash
 python code/src/simulation/ground_truth.py
 ```

3. **Train DP-GMM Model**:
 ```bash
 python code/src/models/dp_gmm.py --config code/config.yaml
 ```

4. **Run Baseline Comparisons**:
 ```bash
 python code/scripts/execute_evaluation_pipeline.py
 ```

5. **Threshold Calibration**:
 ```bash
 python code/src/evaluation/threshold_sweep.py
 ```

6. **Robustness Evaluation** (NEW):
 ```bash
 python code/src/evaluation/robustness.py --subset-size 50
 ```

7. **Resource Compliance Check**:
 ```bash
 python code/scripts/verify_resource_compliance.py
 ```

8. **Final Acceptance**:
 ```bash
 python code/scripts/final_acceptance_verification.py
 ```

## Output Artifacts

All results are saved to `data/processed/results/`:

- `simulation_snr.csv` - Ground truth simulation results
- `posterior_trajectory.csv` - DP-GMM posterior metrics
- `statistical_report.csv` - Baseline comparison statistics
- `sensitivity_report.csv` - Threshold sensitivity analysis
- `robustness_report.csv` - Robustness evaluation results
- `robustness_summary.csv` - Aggregated robustness metrics

## Troubleshooting

- **Config size error**: Ensure `code/config.yaml` is under 2KB
- **Data directory errors**: Verify no `data/results/` or `data/raw/raw/` exist
- **Import errors**: Ensure all code is under `code/src/`

## Full Pipeline Execution

To run the entire pipeline:

```bash
# Step 1: Setup and data generation
python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05

# Step 2: Ground truth validation
python code/src/simulation/ground_truth.py

# Step 3: Model training and evaluation
python code/src/models/dp_gmm.py --config code/config.yaml

# Step 4: Baseline comparison
python code/scripts/execute_evaluation_pipeline.py

# Step 5: Threshold calibration
python code/src/evaluation/threshold_sweep.py

# Step 6: Robustness evaluation
python code/src/evaluation/robustness.py --subset-size 50

# Step 7: Compliance checks
python code/scripts/verify_config_compliance.py
python code/scripts/verify_resource_compliance.py

# Step 8: Final acceptance
python code/scripts/final_acceptance_verification.py
```

## License

MIT License - See LICENSE file for details.