# Quickstart: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## 1. Prerequisites

*   Python 3.11+
*   Git
*   Access to GitHub Actions (for CI execution) or local environment.

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-529-assessing-the-impact-of-sample-size-on-t

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Setup

If running locally, ensure the `data/raw/` directory contains the downloaded meta-analysis data.
If running on CI, the `download.py` script will fetch data automatically (if a verified source is found) or generate synthetic data.

```bash
# Run the download script (Phase 0)
python code/download.py
```

## 4. Running the Analysis

Execute the full pipeline:

```bash
# Run the main orchestration script
python code/main.py
```

This will:
1.  Download/Generate data.
2.  Perform subsampling.
3.  Fit models (FE/RE).
4.  Calculate metrics.
5.  Fit GAM and detect thresholds.
6.  Generate plots in `data/output/`.

## 5. Verifying Results

Check the output files:
*   `data/output/metrics_summary.csv`: Aggregated stability and coverage.
*   `data/output/thresholds.json`: Detected inflection points.
*   `data/output/stability_curve.png`: Visual stability analysis.
*   `data/output/coverage_curve.png`: Visual coverage analysis.

Run tests:
```bash
pytest tests/
```
