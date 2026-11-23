# Quick Start Guide

This guide provides step-by-step instructions to run the distribution shift detection pipeline.

## Prerequisites

- Python 3.8+
- pip package manager
- Internet connection (for downloading CDC data)

## Step 1: Setup Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Download Real CDC Data

The pipeline requires real CDC FluView ILI data and ground truth events.

```bash
python code/download_data.py
```

This script will:
- Fetch ILI data from the CDC FluView API
- Fetch ground truth events from CDC virological/hospitalization data
- Save raw data to `data/raw/`
- Verify checksums where available
- Log the exact URL and retrieval date

**Note**: If data download fails, the pipeline will halt with an `E-NO-DATA` exception. No synthetic fallback is provided.

## Step 3: Run the Main Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py
```

This will:
1. Validate configuration and data availability
2. Preprocess ILI data (remove missing weeks, log-transform, standardize)
3. Run MMD-based shift detection with Bonferroni correction
4. Execute baseline methods (Pettitt, BOCPD)
5. Evaluate detection performance against ground truth
6. Generate the comprehensive PDF report

## Step 4: Run Sensitivity Analysis (Optional)

Assess robustness to hyperparameter choices:

```bash
python code/sensitivity.py
```

This will:
- Sweep over bandwidth values (median, CV-based)
- Test different window lengths (8, 12, 16 weeks)
- Vary week-alignment tolerance (±1, ±2, ±3 weeks)
- Output `sensitivity.csv` and `tolerance_sensitivity.csv`
- Update the report with sensitivity analysis plots

## Step 5: View Results

After completion, you will find:

- `data/processed/flags.csv`: Weeks flagged as distribution shifts
- `data/processed/baselines.csv`: Change points from baseline methods
- `data/processed/sensitivity.csv`: Sensitivity analysis metrics
- `figures/report.pdf`: Full analysis report with visualizations

## Step 6: Run Tests (Optional)

Verify the implementation with the test suite:

```bash
pytest tests/
```

## Troubleshooting

### Data Download Fails
- Ensure internet connection is available
- Check that CDC API endpoints are accessible
- Verify no firewall is blocking the requests
- The script will raise `E-NO-DATA` if download fails

### Memory Issues
- The pipeline is designed to run on standard hardware (<7GB RAM)
- If permutation testing is too slow, the MMD detector will automatically reduce permutation count (but maintain strict Bonferroni threshold)

### Configuration Errors
- Ensure `code/config.yaml` exists with required keys
- Validate schema with: `python code/main.py --validate-only`

## Next Steps

- Review the generated `report.pdf` for detailed analysis
- Examine `sensitivity.csv` to understand parameter robustness
- Compare MMD performance against baseline methods in the report
- Contribute to ongoing development (see CONTRIBUTING.md)