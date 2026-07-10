# Quickstart: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Prerequisites

- Python 3.11+
- `pip` (or `venv`/`conda`)
- GitHub Actions runner (for CI validation)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Configuration

1. **Edit `code/config.yaml`** (must remain <2KB):
   ```yaml
   random_seed: 42
   window_length: 50
   stride: 1
   advi_max_iter: 500
   advi_tol: 0.01
   threshold_default: 0.05
   ```

2. **Verify configuration**:
   ```bash
   python code/src/data/validate_config.py
   ```

## Running the Pipeline

1. **Download datasets & validate URLs** (verified sources only):
   ```bash
   python code/src/data/download_datasets.py
   ```

2. **Run full analysis**:
   ```bash
   python code/src/services/anomaly_detector.py
   ```

3. **Generate report** (includes traceability):
   ```bash
   python code/src/evaluation/report_generator.py
   ```

## Validation

- **Check RAM usage**:
  ```bash
  python code/src/services/monitor_resources.py
  ```

- **Run tests**:
  ```bash
  pytest code/tests/
  ```

## Output

- **Posterior Trajectory**: `data/processed/posterior_trajectory.jsonl`
- **Detection Events**: `data/processed/detection_events.jsonl`
- **Sensitivity Report**: `data/processed/sensitivity_report.json`
- **Traceability Report**: `data/processed/traceability_report.json`
- **Final Report**: `data/processed/final_report.md`
