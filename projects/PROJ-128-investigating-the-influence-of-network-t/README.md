# Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

**Status**: Production Ready

This project investigates whether topological properties of structural brain networks (derived from diffusion MRI) predict the prevalence, stability, and switching speed of recurrent activity patterns (derived from dynamic functional connectivity in fMRI).

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python code/main.py

# Validate outputs
python code/validate_quickstart.py
```

## What This Does

1. **Structural Metrics**: Computes global efficiency, clustering, and modularity from dMRI
2. **Dynamic Metrics**: Computes dwell time and visited states from fMRI using LOO k-means
3. **Correlation**: Statistically correlates structural and dynamic metrics with FDR correction
4. **Robustness**: Validates results against window length and density threshold variations
5. **Reporting**: Generates a final report with explicit "associational" framing

## Key Features

- **Real Data Only**: Downloads HCP data from OpenNeuro; no synthetic data
- **CPU-Only**: Optimized for CPU execution (no GPU required)
- **LOO Clustering**: Prevents circular correlation via Leave-One-Out k-means
- **FDR Correction**: Benjamini-Hochberg correction for multiple comparisons
- **Sensitivity Analysis**: Compares 30 TR vs 20 TR window lengths
- **Validation**: Schema validation and language auditing

## Output Files

- `data/processed/structural_metrics.csv`
- `data/processed/dynamic_metrics.csv`
- `data/processed/correlation_results.csv`
- `data/logs/exclusion_log.json`
- `data/reports/final_report.json`

## Documentation

- [User Guide](docs/USER_GUIDE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Methodology](docs/METHODOLOGY.md)

## Testing

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v
```

## Requirements

- Python 3.9+
- 7 GB RAM
- 14 GB disk space
- Internet access (for HCP data download)

## License

[Insert License]