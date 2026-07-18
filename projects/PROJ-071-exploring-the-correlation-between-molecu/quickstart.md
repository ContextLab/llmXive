# Quick Start Guide

## Getting Started

1. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Run the Pipeline**:
 ```bash
 python code/pipeline_runner.py
 ```

3. **View Results**:
 - Analysis results: `data/processed/analysis_results.json`
 - Plots: `data/outputs/`
 - Report: `results_report.md`

## Key Steps

1. **Data Ingestion**: Fetches FDA-approved drugs from HuggingFace.
2. **Descriptor Calculation**: Computes molecular complexity metrics.
3. **Standardization**: Converts rate constants to half-lives and filters for standard conditions.
4. **Analysis**: Performs correlation analysis and regression modeling.
5. **Visualization**: Generates diagnostic plots.
6. **Reporting**: Creates a comprehensive report with reproducibility metadata.

## Troubleshooting

- **Data Insufficiency**: If the dataset size is below 30, the pipeline will generate a `data_insufficiency_report.md` and exit.
- **Missing Columns**: Ensure the dataset contains necessary columns (e.g., `half_life`, `degradation_rate`).
- **Invalid SMILES**: Invalid SMILES strings are logged to `data/errors.log`.

## Configuration

Edit `config.yaml` to customize paths and settings.

## Next Steps

- Explore the correlation results in `analysis_results.json`.
- Review the diagnostic plots in `data/outputs/`.
- Read the full report in `results_report.md`.
