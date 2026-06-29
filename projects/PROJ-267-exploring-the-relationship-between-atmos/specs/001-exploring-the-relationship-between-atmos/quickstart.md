# Quickstart: Atmospheric River Gravity Correlation

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Access to GRACE-FO and NOAA AR Catalog data sources
- GitHub Actions runner or local Linux environment

## Installation

```bash
# Clone repository
git clone <repository-url>
cd projects/PROJ-267-exploring-the-relationship-between-atmos

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r code/requirements.txt
```

## Data Setup

1. **Download GRACE-FO data**: Fetch Level-2 mascon solutions from CSR/JPL official repository
2. **Download NOAA AR data**: Fetch Atmospheric River Catalog from NOAA CPC official repository
3. **Place raw data**: Put downloaded files in `data/raw/grace-fo/` and `data/raw/noaa-ar/`
4. **Verify checksums**: Run `python code/verify_checksums.py` to validate data integrity

## Running the Pipeline

```bash
# Execute full pipeline (all phases)
python code/01_data_ingestion.py
python code/02_preprocessing.py
python code/03_correlation_analysis.py
python code/04_visualization.py
python code/05_sensitivity_report.py
```

Or run sequentially via wrapper:

```bash
bash scripts/run_pipeline.sh
```

## Expected Outputs

| Output | Location | Description |
|--------|----------|-------------|
| Merged data | `data/processed/merged_monthly.csv` | Aligned time series |
| Correlation results | `data/processed/correlation_results.csv` | Statistical analysis output |
| Time-series plot | `output/plots/timeseries_overlay.png` | AR vs gravity over time |
| Scatter plot | `output/plots/scatter_regression.png` | Correlation visualization |
| Spatial map | `output/plots/spatial_anomaly.png` | Regional gravity anomaly map |
| Sensitivity report | `output/reports/sensitivity_analysis.pdf` | Threshold stability analysis |

## Verification

```bash
# Run contract tests
pytest tests/contract/

# Run integration tests
pytest tests/integration/

# Verify data completeness (SC-001)
python code/verify_completeness.py --threshold 0.90
```

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| Data download fails | Check network; retry with `--retry` flag |
| Missing months in output | Check raw data availability; log warning and proceed |
| Bootstrap timeout | Reduce iterations (not recommended); check system resources |
| No significant correlation | This is a valid result; report with CI as per edge cases |

## GitHub Actions CI

The pipeline runs automatically on push to the feature branch:

```yaml
# .github/workflows/pipeline.yml
name: Research Pipeline
on: [push]
jobs:
  analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r code/requirements.txt
      - name: Run pipeline
        run: bash scripts/run_pipeline.sh
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: outputs
          path: output/
```
