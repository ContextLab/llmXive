# Quick Start

This document provides a minimal guide to running the pipeline and validating results.

## Prerequisites

- Python 3.9+
- 14GB+ free disk space
- 7GB+ available RAM
- Internet connection (for data download)

## Installation

```bash
# Clone repository
git clone <repository-url>
cd PROJ-128-investigating-the-influence-of-network-t

# Install dependencies
pip install -r requirements.txt
```

## Run Pipeline

```bash
python code/main.py
```

This will:
1. Download HCP data (if not present)
2. Compute structural and dynamic metrics
3. Perform correlation analysis with FDR correction
4. Run sensitivity analysis
5. Generate final report

## Validate Results

```bash
python code/validate_quickstart.py
```

Expected outputs:
- `data/processed/structural_metrics.csv`
- `data/processed/dynamic_metrics.csv`
- `data/processed/correlation_results.csv`
- `data/processed/sensitivity_comparison.csv`
- `data/reports/final_report.json`

## Expected Runtime

- Data download: 30-60 min
- Processing: 1-10 hours (depending on cohort size)
- Analysis: 5-10 min

## Troubleshooting

- **Download fails**: Check internet connection and OpenNeuro access
- **Out of memory**: Use `code/main_optimized.py` or reduce batch size
- **Convergence failure**: Check `data/logs/exclusion_log.json`

## Next Steps

- Read `docs/README.md` for full documentation
- Review `docs/ARCHITECTURE.md` for system design
- Run `pytest tests/` for validation
