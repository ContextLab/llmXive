# Quickstart Guide - Bayesian Nonparametrics for Anomaly Detection

## Prerequisites

- Python 3.11+
- pip and virtual environment

## Setup

1. Create virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 cd code
 pip install -r requirements.txt
 ```

## Running the Pipeline

### 1. Configuration Check

```bash
python code/src/config.py --check
```

### 2. Data Download

```bash
python code/src/data/download_datasets.py
```

### 3. Synthetic Data Generation (if real data unavailable)

```bash
python code/src/data/synthetic_generator.py --seed 42 --n-points 1000
```

### 4. Ground Truth Simulation (Phase 0)

```bash
python code/src/evaluation/simulation.py
```

### 5. Robustness Analysis (NEW - T103)

This step validates the robustness of the anomaly detection pipeline by testing
different window sizes and derivative calculation methods.

```bash
python code/src/evaluation/robustness.py --window-sizes 30 50 70 100 --anomaly-rate 0.05
```

Output: `data/processed/results/robustness_report_*.json` and `data/processed/results/robustness_results_*.csv`

### 6. Main Inference

```bash
python code/src/services/anomaly_detector.py
```

### 7. Evaluation

```bash
python code/scripts/execute_evaluation_pipeline.py
```

## Output Artifacts

- `data/processed/results/simulation_snr.csv` - Ground truth simulation results
- `data/processed/results/robustness_report_*.json` - Robustness analysis report
- `data/processed/results/robustness_results_*.csv` - Detailed robustness metrics
- `data/processed/results/posterior_trajectory.csv` - DP-GMM posterior trajectories
- `data/processed/results/statistical_report.csv` - Statistical test results

## Verification

Run the verification script to ensure all components are working:

```bash
python code/scripts/verify_robustness_script.py
python code/scripts/final_acceptance_verification.py
```