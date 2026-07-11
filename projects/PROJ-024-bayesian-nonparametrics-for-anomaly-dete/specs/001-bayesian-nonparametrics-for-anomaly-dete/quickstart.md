# Quickstart: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Prerequisites
- Python 3.11+
- pip
- Access to GitHub Actions (for CI validation) or local environment with sufficient RAM.

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins CPU-compatible versions of PyMC 4 and other libraries.*

3. **Verify Environment**:
   ```bash
   python code/src/config.py --check
   ```
   This validates `config.yaml` against `contracts/config.schema.yaml` (FR-024) and checks file size (<2KB).

## Data Preparation

1. **Download Datasets**:
   ```bash
   python code/src/data/download_datasets.py
   ```
   This script fetches only verified datasets from HuggingFace/UCI as per `research.md`.

2. **Generate Synthetic Data** (if needed):
   ```bash
   python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05
   ```
   *This includes pre-anomaly dynamics as per FR-021.*

## Running the Pipeline

### Full Analysis
```bash
python code/src/services/anomaly_detector.py
```
This executes:
1. Sliding window extraction.
2. DP-GMM inference (ADVI) and baseline fitting.
3. Statistical testing (Wilcoxon, KS, Bootstrap, Survival Analysis).
4. Sensitivity analysis.
5. Report generation.

### Specific Tasks
- **Simulation Study**:
  ```bash
  python code/src/evaluation/simulation.py
  ```
- **MCMC Robustness Check**:
  ```bash
  python code/src/evaluation/robustness.py --subset-size 50
  ```

## Output Artifacts

- **Reports**: `data/processed/results/detection_report.json`
- **Trajectories**: `data/processed/posterior_trajectory.parquet`
- **Figures**: `data/processed/results/figures/`
- **State**: `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`

## Validation

1. **Check Convergence**:
   Review logs for `WARNING: ADVI did not converge`.
2. **Verify Config Size**:
   ```bash
   ls -lh code/config.yaml  # Must be < 2KB
   ```
3. **Memory Check**:
   Ensure peak RAM < 7GB (logged in `state/` file).
4. **Verify Data Split**:
   Check `data/processed/split_indices.json` for Train/Val/Test split (FR-019).