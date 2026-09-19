# Quick Start Guide

## Prerequisites

1. Python 3.11+ installed
2. IBM Quantum account and API token
3. Git repository cloned

## Step 1: Setup Environment

```bash
# Create virtual environment
python -m venv.venv
source.venv/bin/activate # Windows:.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure IBM Quantum Access

Set your API token as an environment variable:

```bash
# Linux/Mac
export IBMQX_TOKEN="your-token-here"

# Windows PowerShell
$env:IBMQX_TOKEN="your-token-here"
```

Alternatively, use `qiskit-ibm-runtime` login:
```bash
python -c "from qiskit_ibm_runtime import QiskitRuntimeService; QiskitRuntimeService.save_account(token='your-token')"
```

## Step 3: Initialize Project Structure

```bash
python code/setup_project.py
```

This creates:
- `code/` - Source modules
- `data/raw/` - Raw API responses
- `data/processed/` - Cleaned metrics
- `tests/` - Test suite
- `figures/` - Plots
- `state/` - Project metadata

## Step 4: Run the Pipeline

### Fetch Calibration Data (US1)
```bash
python code/fetcher.py
```
Outputs:
- `data/raw/*.json` - Raw snapshots
- `data/processed/raw_calibration.csv` - Device metrics

### Compute Graph Metrics (US2)
```bash
python code/generate_graph_metrics_csv.py
```
Outputs:
- `data/processed/graph_metrics.csv` - Topological descriptors

### Run Statistical Analysis (US3)
```bash
python code/generate_correlation_results.py
```
Outputs:
- `data/processed/correlation_results.csv` - Correlation statistics

### Generate Report
```bash
python code/generate_report.py
```
Outputs:
- `docs/report.md` - Final analysis report
- `figures/*.png` - Visualizations

## Step 5: Validate Results

```bash
# Run tests
pytest tests/ -v

# Check code quality
ruff check code/
black --check code/
```

## Troubleshooting

### "No backends available"
- Verify your IBM Quantum token is set correctly
- Ensure your account has access to public backends
- Check network connectivity

### "Data freshness check failed"
- IBM Quantum may have limited backend availability
- Retry after some time; calibration data updates periodically

### "Import errors"
- Ensure virtual environment is activated
- Re-run `pip install -r requirements.txt`

## Next Steps

- Review `docs/report.md` for analysis results
- Explore `specs/` for detailed feature requirements
- Read `research.md` for methodology details