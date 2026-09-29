# Quickstart Guide

## Prerequisites

- Python 3.8+
- Virtual environment (recommended)

## Installation

1. Clone the repository.
2. Create and activate a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Preparation

Ensure you have a valid SMILES dataset at `data/raw/smiles.csv`.
The file must contain at least two columns: `smiles` and a target variable
(e.g., `conductivity`, `HOMO_LUMO_gap`, or `log_conductivity_proxy`).

## Running the Pipeline

Execute the full pipeline end-to-end:

```bash
python code/main.py
```

This command will:
1. Load and validate the data.
2. Compute graph-based descriptors.
3. Perform scaffold splitting.
4. Run sensitivity analysis and outlier filtering.
5. Train models with iterative VIF filtering.
6. Generate feature importance and correlation plots.
7. Save all results to `data/processed/`.

## Validation

To verify that all expected output files were generated:

```bash
python code/main.py --validate-only
```

## Output Artifacts

The pipeline produces the following artifacts:

- `data/processed/descriptors.csv`: Computed molecular descriptors.
- `data/processed/sensitivity_analysis.json`: Results of sensitivity analysis.
- `data/processed/vif_iteration_log.json`: Log of VIF filtering iterations.
- `data/processed/feature_importance.csv`: Ranked feature importance.
- `data/processed/correlation_results.json`: Feature-target correlations.
- `data/processed/analysis_summary.json`: Final analysis summary.
- `data/processed/corr_plot_top5.png`: Scatter plots for top features.
- `data/processed/model_results.json`: Final model performance metrics.

## Troubleshooting

- **Missing Data**: If `data/raw/smiles.csv` is missing, provide a valid dataset.
- **Import Errors**: Ensure all dependencies in `requirements.txt` are installed.
- **Pipeline Failure**: Check `logs/pipeline.log` for detailed error messages.
