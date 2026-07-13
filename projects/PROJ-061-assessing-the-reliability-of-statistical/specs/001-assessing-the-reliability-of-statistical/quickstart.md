# Quickstart: Assessing the Reliability of Statistical Power Calculations

## Prerequisites

- Python 3.11+
- Git
- (Optional) Docker for isolated environment

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-061-assessing-the-reliability-of-statistical
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Dependencies include: pandas, numpy, scipy, statsmodels, scikit-learn, pytest.*

## Running the Pipeline

### 1. Data Acquisition
The pipeline automatically downloads canonical datasets from `sklearn` and `rdatasets`. No manual download is required.
```bash
python code/main.py --stage download
```

### 2. Validation (Synthetic Ground Truth)
Run the synthetic validation test (FR-008) to ensure the bootstrap engine is accurate.
```bash
python code/main.py --stage validate_synthetic
```
*Expected Output*: Recovery rate within 5% of true power.

### 3. Full Analysis
Execute the full pipeline: baseline, violation induction, and sensitivity analysis.
```bash
python code/main.py --stage run_full
```
*Note*: This will process multiple datasets, multiple violation types, and 1000 bootstrap iterations. Estimated runtime: minutes.

### 4. Sensitivity Analysis
Run the sensitivity sweep on bias thresholds (FR-006).
```bash
python code/main.py --stage sensitivity
```

## Verifying Results

1. **Check Output Files**:
   - `data/results/power_estimates.json`: Contains all `PowerEstimate` records.
   - `data/results/sensitivity_report.csv`: Summary of bias classification across thresholds.

2. **Run Tests**:
   ```bash
   pytest tests/
   ```
   Ensure all unit, integration, and contract tests pass.

3. **Reproducibility Check**:
   Re-run the pipeline with a different seed (if supported) or verify that the same seed produces identical results (due to pinning).

## Troubleshooting

- **Runtime Error**: Ensure sufficient memory. Close other applications.
- **Bootstrap Validity Flag**: If many records are "unreliable", check `data/processed/` for small sample sizes or heavy-tailed distributions.
- **Missing Datasets**: Verify internet connection for `rdatasets` or `sklearn` loading.
