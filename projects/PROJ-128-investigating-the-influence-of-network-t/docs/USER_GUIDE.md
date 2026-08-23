# User Guide

## Getting Started

### Prerequisites

- Python 3.9+
- 7 GB RAM minimum
- 14 GB disk space
- Internet connection (for data download)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd PROJ-128-investigating-the-influence-of-network-t

# Create virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Pipeline

```bash
python code/main.py
```

This will:
1. Download HCP data (first run only)
2. Compute structural and dynamic metrics
3. Perform correlation analysis
4. Run sensitivity checks
5. Generate final report

### Output Files

- `data/processed/structural_metrics.csv`: Global efficiency, clustering, modularity per subject
- `data/processed/dynamic_metrics.csv`: Dwell time, visited states per subject
- `data/processed/correlation_results.csv`: Correlation coefficients, p-values, FDR flags
- `data/logs/exclusion_log.json`: Subjects excluded due to convergence/sparsity
- `data/reports/final_report.json`: Complete analysis summary

## Configuration

Edit `code/config.py` to adjust:

```python
# Sliding window parameters
WINDOW_LENGTH_TR = 30 # Baseline
SENSITIVITY_WINDOW_TR = 20 # Sensitivity check

# K-means
N_CLUSTERS = 5

# Statistical thresholds
ALPHA = 0.05
FDR_Q = 0.05

# Density thresholds
DENSITY_THRESHOLD = 0.10
```

## Running Tests

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v
```

## Troubleshooting

### Data Download Fails
- Check internet connection
- Verify OpenNeuro availability
- Script will fail loudly (no synthetic fallback)

### Convergence Failures
- Check `data/logs/exclusion_log.json` for excluded subjects
- May be due to sparse networks or noisy data

### Memory Errors
- Reduce number of subjects processed
- Ensure streaming is enabled for large datasets

### Zero Significant Findings
- This is a valid outcome
- Report will explicitly state "no significant findings after FDR correction"

## Custom Analysis

### Running Single-Subject Pipeline

```python
from main import process_subject
subject_id = "100307"
process_subject(subject_id)
```

### Manual Correlation Analysis

```python
from analysis.correlation import run_correlation_analysis
results = run_correlation_analysis("data/processed/structural_metrics.csv",
 "data/processed/dynamic_metrics.csv")
```

### Sensitivity Analysis

```python
from analysis.robustness import run_sensitivity_analysis
sensitivity = run_sensitivity_analysis()
```

## Reporting

The final report (`data/reports/final_report.json`) includes:
- Summary statistics
- Correlation matrix with FDR flags
- Sensitivity metrics (30 TR vs 20 TR difference)
- Exclusion log summary
- Explicit "associational" framing statement

## Support

For issues, open a GitHub issue with:
- Error traceback
- System configuration
- Steps to reproduce
