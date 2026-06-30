# Quickstart: Detecting Distribution Shift in Public Health Surveillance Data via Kernel Two‑Sample Tests

## Prerequisites

- Python 3.11+
- `pip` or `venv`
- Access to the project repository
- **Note**: Real CDC FluView and Virological/Hospitalization data are required for the full pipeline. If these are unavailable, the pipeline will halt with an error.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-734-detecting-distribution-shift-in-public-h
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Setup

1. **Download Data**:
   Run the download script. **Note**: If the CDC source is unavailable, this step will fail with error `E-NO-DATA`. Ensure you have a local `data/raw/` directory.
   ```bash
   python code/download_data.py
   ```
   *Expected Output*: `data/raw/fluview_ili.csv` (and `ground_truth_events.csv` if available)

2. **Verify Ground Truth**:
   Place your ground truth file (if available) at `data/raw/ground_truth_events.csv`. If missing, the pipeline will halt with error `E-NO-GROUND-TRUTH`.

## Running the Pipeline

Execute the full pipeline:
```bash
python code/main.py
```

### Expected Outputs

- `data/processed/ili_preprocessed.csv`: Preprocessed time series.
- `code/outputs/flags.csv`: Weeks flagged by MMD.
- `code/outputs/baselines.csv`: Change points from Pettitt/BOCPD.
- `code/outputs/sensitivity.csv`: Sensitivity analysis results.
- `code/outputs/report.pdf`: Summary report with metrics and plots.

**Note**: If real data is missing, the pipeline will halt and no outputs will be generated.

## Running Tests

```bash
pytest tests/ -v
```
*Note*: Unit tests use synthetic data to verify logic.

## Configuration

Edit `code/config.yaml` to adjust:
- `window_length`: Default 12.
- `n_permutations`: Default 1000.
- `alpha`: Default 0.01.
- `seed`: Random seed for reproducibility.
- `tolerance_weeks`: Default 2 (used in sensitivity analysis).
