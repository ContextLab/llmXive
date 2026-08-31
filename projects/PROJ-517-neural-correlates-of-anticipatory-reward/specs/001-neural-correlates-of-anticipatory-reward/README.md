# Neural Correlates of Anticipatory Reward Processing in Vocal Learning

## Project Overview
This project implements an automated scientific pipeline to analyze neural correlates of anticipatory reward processing. The pipeline ingests spike train data, performs statistical modeling using Generalized Linear Models (GLMs), and generates visualizations and comprehensive reports.

## Directory Structure

```
specs/001-neural-correlates-of-anticipatory-reward/
├── README.md # This file
├── plan.md # Project plan and phases
├── spec.md # Detailed specification
├── data-model.md # Data model and entities
├── research.md # Research protocol and methodology
└── contracts/
 ├── dataset.schema.yaml # Input data schema
 └── output.schema.yaml # Output report schema
```

## User Stories

1. **US1**: Data Ingestion and Pre-processing Pipeline
2. **US2**: Statistical Modeling and Significance Testing
3. **US3**: Visualization and Reporting

## Quick Start

```bash
# Activate virtual environment
source.venv/bin/activate

# Run the full pipeline
python code/main.py
```

## Requirements

- Python 3.10+
- pandas, numpy, scipy, statsmodels, scikit-learn
- matplotlib, seaborn, pyyaml, pytest

## Data Sources

- Primary: OpenNeuro datasets (e.g., ds00XXXX)
- Secondary: Zenodo repositories
- CI Testing: Synthetic data generator

## Validation

- Minimum 30 trials per reward magnitude level
- Cue-reward delay >= 500ms
- Spike sorting quality: SNR > 3, Isolation Distance > 20

## Outputs

- `data/processed/validation_report.json`: Data quality metrics
- `data/processed/observed_variance.json`: Variance for power analysis
- `data/figures/`: Visualization plots (PNG)
- `data/reports/summary_report.txt`: Comprehensive analysis report

## License

MIT License
