# Quickstart: Investigate Brain Network Dynamics and VR Therapy Response

## Prerequisites

- **Python**: 3.11 or higher.
- **Dependencies**: `pip install -r requirements.txt`.
- **Data**: The pipeline expects the dataset to be available via the verified HuggingFace link. No manual download is required if using the automated downloader.

## Installation

1.  **Clone the repository** (or navigate to the project root).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via the CLI. It performs the following steps in order:
1.  **Verify** dataset availability and variables.
2.  **Download** and preprocess data (streamed).
3.  **Compute** network metrics.
4.  **Run** statistical analysis and sensitivity checks.
5.  **Generate** reports.

### Command

```bash
python -m src.cli.run_pipeline --config config/default.yaml
```

### Configuration

The `config/default.yaml` file contains:
- `dataset_url`: The verified HuggingFace URL.
- `motion_threshold`: Default 3.0 mm.
- `atlas`: Default 'Schaefer-100'.
- `max_subjects`: Default 20.

## Expected Outputs

After successful execution, the following artifacts will be generated:

- `data/processed/`: Preprocessed NIfTI files.
- `data/metrics/network_metrics.csv`: Computed graph metrics.
- `reports/statistical_results.json`: Regression coefficients, p-values, effect sizes.
- `reports/sensitivity_analysis.md`: Summary of sensitivity sweeps (motion: {2.0, 3.0} mm; p: {0.01, 0.05, 0.1}).
- `reports/diagnostic_plots/`: Scatter plots and residual diagnostics.
- `data/verified_sources.json`: Verified dataset ID and validation log.

## Troubleshooting

- **"Missing required variable"**: The dataset lacks pre/post anxiety scores. The pipeline halts. No synthetic data is generated.
- **"Memory Error"**: The `streaming=True` flag should prevent this. If it occurs, reduce `max_subjects` in config.
- **"VIF > 5"**: The pipeline automatically switches to Ridge regression. Check `reports/statistical_results.json` for the `model_type` field.
- **"No Open Longitudinal Dataset Found"**: The pipeline could not find a dataset with both rs-fMRI and pre/post clinical scores. The study cannot proceed.