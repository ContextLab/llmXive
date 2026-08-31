# Quick Start Guide

This guide provides step-by-step instructions to get the distribution shift detection pipeline up and running quickly.

## Step 1: Environment Setup

Ensure you have Python 3.8+ installed. Then:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Verify Project Structure

Ensure the following directories exist:
```
data/raw
data/processed
code
tests
code/contracts
```

If any are missing, create them:
```bash
mkdir -p data/raw data/processed code tests code/contracts
```

## Step 3: Download Real CDC Data

The pipeline requires real CDC data. Run the download script:

```bash
python code/download_data.py
```

This will:
- Fetch CDC FluView ILI data to `data/raw/fluview_ili.csv`
- Fetch ground truth events to `data/raw/ground_truth_events.csv`
- Log the exact URLs and retrieval dates
- Verify checksums (if available)

**Note**: If the download fails, the script will raise an `E-NO-DATA` exception and halt. Do not use synthetic data for final results.

## Step 4: Run the Pipeline

Execute the main pipeline script:

```bash
python code/main.py
```

This runs:
1. **Preprocessing**: Handles missing weeks, log-transforms, and standardizes data.
2. **MMD Detection**: Identifies distribution shifts using Gaussian-kernel MMD.
3. **Baseline Comparison**: Runs Pettitt and BOCPD methods.
4. **Evaluation**: Computes precision, recall, and detection delay against ground truth.
5. **Sensitivity Analysis**: Tests robustness across parameter grids.
6. **Report Generation**: Creates `figures/report.pdf`.

## Step 5: Review Outputs

After completion, check the following:

- **Flags**: `data/processed/flags.csv` - Weeks flagged as having distribution shifts.
- **Baselines**: `data/processed/baselines.csv` - Change points detected by baseline methods.
- **Sensitivity**: `data/processed/sensitivity.csv` and `data/processed/tolerance_sensitivity.csv` - Results of sensitivity analysis.
- **Report**: `figures/report.pdf` - Comprehensive summary with metrics and visualizations.

## Step 6: Run Tests (Optional)

To verify the implementation:

```bash
pytest tests/
```

## Troubleshooting

- **Missing Data**: If `data/raw/fluview_ili.csv` or `data/raw/ground_truth_events.csv` is missing, re-run `python code/download_data.py`.
- **Import Errors**: Ensure all dependencies are installed (`pip install -r requirements.txt`).
- **Runtime Errors**: Check `code/config.yaml` for valid parameters and ensure your system has sufficient memory (recommended: >7GB RAM for large datasets).

## Next Steps

- Customize parameters in `code/config.yaml`.
- Extend the pipeline with new detection methods.
- Contribute to the project by adding tests or improving documentation.

For more details, see the [README.md](README.md).