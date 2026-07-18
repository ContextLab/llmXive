# Quick Start Guide

## Overview

This project explores the correlation between molecular complexity and degradation rates in pharmaceuticals. The pipeline ingests FDA-approved drug structures, calculates molecular descriptors, performs correlation analysis, and generates visualizations and reports.

## Prerequisites

- Python 3.9+
- pip package manager
- 7GB+ RAM recommended

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd projects/PROJ-071-exploring-the-correlation-between-molecu
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Verify installation:
```bash
python -c "import rdkit; print('RDKit installed successfully')"
```

## Running the Pipeline

### Full Pipeline Execution

Run the complete pipeline from data ingestion to report generation:

```bash
python code/pipeline_runner.py
```

This will:
1. Fetch FDA-approved drug structures from HuggingFace
2. Check data availability (minimum 30 samples required)
3. Calculate molecular descriptors (TPSA, MW, Rotatable Bonds, etc.)
4. Perform correlation analysis and regression modeling
5. Generate visualizations and reproducibility reports

### Individual Components

#### Data Ingestion
```bash
python code/ingest.py
```

#### Descriptor Calculation
```bash
python code/descriptors.py
```

#### Analysis
```bash
python code/analysis.py
```

#### Visualization
```bash
python code/viz.py
```

#### Report Generation
```bash
python code/report.py
```

### Performance Validation

Validate that the pipeline meets operational latency requirements:

```bash
python code/validate_performance.py
```

This script:
- Executes the full pipeline
- Measures total execution time
- Compares against the configured threshold (default: 300 seconds)
- Generates a validation report at `data/processed/performance_validation.json`

Exit codes:
- 0: Validation passed (execution successful and within threshold)
- 1: Validation failed (execution failed or exceeded threshold)

## Output Files

The pipeline generates the following outputs:

- `data/processed/merged_drugs.csv`: Combined structural and degradation data
- `data/processed/analysis_results.json`: Correlation and regression results
- `data/outputs/scatter_tpsa_vs_half_life.png`: Scatter plot with regression line
- `data/outputs/residuals.png`: Residual diagnostic plots
- `data/outputs/qq_plot.png`: Q-Q plot for residual normality
- `results_report.md`: Comprehensive results report
- `reproducibility_log.json`: Machine-readable reproducibility metadata
- `data/processed/performance_validation.json`: Performance validation results

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run specific test modules:

```bash
pytest tests/test_descriptors.py -v
pytest tests/test_analysis.py -v
pytest tests/test_performance_validation.py -v
```

## Configuration

Key configuration options can be modified in `code/config.py`:

- `PERFORMANCE_THRESHOLD_SECONDS`: Maximum allowed execution time (default: 300)
- `MIN_SAMPLES`: Minimum number of samples for data availability gate (default: 30)
- `CORRELATION_THRESHOLD`: Minimum |r| for significant correlation (default: 0.5)
- `P_VALUE_THRESHOLD`: Maximum p-value for significance (default: 0.05)

## Troubleshooting

### Data Availability Gate Failed

If you see "Data availability gate failed: N < 30", the dataset does not contain enough samples with both structural and degradation data. The pipeline will generate a `data_insufficiency_report.md` explaining the issue.

### Memory Issues

If you encounter memory errors, ensure you have at least 7GB of available RAM. The pipeline uses streaming for large datasets where possible.

### Logging

All pipeline logs are written to `data/outputs/pipeline.log`. Check this file for detailed error information.

## Data Sources

- FDA-approved drugs: HuggingFace dataset `Synthyra/FDA-Approved-Drugs`
- Molecular descriptors: Calculated using RDKit
- Degradation data: Extracted from the FDA dataset (if available)

## License

This project is for research purposes only. See LICENSE for details.
