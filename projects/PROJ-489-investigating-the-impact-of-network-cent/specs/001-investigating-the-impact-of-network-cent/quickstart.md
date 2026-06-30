# Quickstart: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Prerequisites
- Python 3.11+
- Valid PhysioNet account (for Sleep-EDF download via MNE).
- 2 CPU cores, 7 GB RAM (standard GitHub Actions runner).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/001-network-centrality-sleep-synchrony
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

## Running the Pipeline

1. **Download Data**:
   ```bash
   python code/download.py
   ```
   *Note: This will prompt for PhysioNet credentials or use environment variables.*

2. **Preprocess & Compute Metrics**:
   ```bash
   python code/main.py --stage preprocess
   python code/main.py --stage metrics
   ```

3. **Run Analysis**:
   ```bash
   python code/main.py --stage analysis
   ```

4. **Generate Report**:
   ```bash
   python code/main.py --stage report
   ```

## Verification

- Check `data/metrics/subject_metrics.csv` for expected columns (including `waking_night_id`, `sleep_night_id`).
- Check `data/results/analysis_results.json` for FDR-corrected p-values and LME coefficients.
- Ensure no `NaN` values in the processed data.