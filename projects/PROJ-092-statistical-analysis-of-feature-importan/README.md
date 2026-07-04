# Statistical Analysis of Feature Importance Drift in Pre-trained Models

## Project Overview

This project implements a pipeline to detect and quantify statistical drift in feature importance rankings over time using pre-trained Random Forest models. The system processes the UCI Electricity Load Diagrams dataset, splits it into sequential time windows, trains models, and analyzes drift using Spearman rank correlation and Mann-Kendall trend tests.

## Quick Start

```bash
# Install dependencies
pip install -r code/requirements.txt

# Set up directories
python code/setup_directories.py

# Download dataset
python code/download.py

# Run the pipeline
python code/main.py

# Run drift analysis
python code/drift_analysis.py

# Run significance tests
python code/significance_test.py

# Generate final report
python code/generate_final_report.py
```

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Quick Start Guide](docs/QUICKSTART.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Contributing Guide](docs/CONTRIBUTING.md)

## Key Features

- **Windowed Analysis**: Processes data in sequential 30-day windows
- **Model Validation**: Skips windows with R² < 0.8
- **Drift Quantification**: Spearman rank correlation between consecutive windows
- **Statistical Rigor**: Mann-Kendall trend test and block permutation testing
- **Null Baseline**: Shuffled window order for significance validation

## Outputs

- `outputs/importance_profiles.csv`: Per-window feature importance scores
- `outputs/drift_metrics.csv`: Pairwise drift metrics (rho, p-value)
- `outputs/null_baseline.json`: Baseline distribution from shuffled data
- `outputs/global_stats.json`: Aggregated statistics and trend analysis

## Requirements

- Python 3.11+
- CPU-only execution (no GPU required)
- See `code/requirements.txt` for full dependency list

## License

[Add license information here]