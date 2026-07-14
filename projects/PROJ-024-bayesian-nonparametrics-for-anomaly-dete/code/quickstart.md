# Quickstart Guide for PROJ-024

This guide outlines the steps to run the full analysis pipeline for the Bayesian Nonparametrics for Anomaly Detection project.

## Prerequisites

- Python 3.11+
- Dependencies installed via `pip install -r code/requirements.txt`

## Execution Steps

Run the following commands in order. Each step must complete successfully before proceeding to the next.

### 1. Configuration Check
```bash
python code/src/config.py --check
```

### 2. Data Acquisition
```bash
python code/src/data/download_datasets.py
```

### 3. Synthetic Data Generation (for validation)
```bash
python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05
```

### 4. Simulation Study (Ground Truth Validation)
This step validates the ADVI estimator's fidelity before main inference.
```bash
python code/src/evaluation/simulation.py --seed 42 --n-samples 500 --anomaly-rate 0.05
```
*Deliverable*: `data/processed/results/simulation_snr.csv` must be generated with SNR > 1.

### 5. Main Inference Pipeline
```bash
python code/src/services/anomaly_detector.py
```

### 6. Baseline Comparison
```bash
python code/scripts/execute_evaluation_pipeline.py
```

### 7. Robustness Check
```bash
python code/src/evaluation/robustness.py --subset-size 50
```

### 8. Final Acceptance
```bash
python code/scripts/final_acceptance_verification.py
```

## Troubleshooting

- If `config.py` fails, check `code/config.yaml` for required keys.
- If data download fails, verify network access and URLs.
- If simulation SNR <= 1, review anomaly injection parameters or model hyperparameters.