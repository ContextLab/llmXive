# Quickstart: Quantifying the Impact of Network Structure on Energy Dissipation

## Prerequisites
- Python 3.11+
- Git
- GitHub Actions runner (for CI execution) or local Linux environment.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-468-quantifying-the-impact-of-network-struct
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Data Preparation

Since no verified granular DEM dataset is available in the provided list, the pipeline supports **Synthetic Data for Code Validation** only.

1.  **Generate synthetic data (Code Validation Only)**:
    ```bash
    python code/generate_synthetic_data.py --output data/raw/synthetic_demo.parquet
    ```
    *Note: This script creates a small-scale DEM simulation output with random particle positions and forces for testing the pipeline logic. **Results from this data are NOT scientifically valid.**.*

2.  **Verify data integrity**:
    ```bash
    python code/utils.py --check data/raw/synthetic_demo.parquet
    ```

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py --input data/raw/synthetic_demo.parquet --output results/
```

**Options**:
- `--input`: Path to the raw DEM output file (Parquet/CSV).
- `--output`: Directory for processed data and reports.
- `--max-memory`: Override the memory cap (default: 6GB).
- `--validation-mode`: Set to `code` (synthetic) or `science` (requires real data). Default: `code`.

## Expected Outputs

After successful execution, the `results/` directory will contain:
- `processed_metrics.csv`: Time-series of network metrics and dissipation (with metadata header).
- `regression_results.json`: Statistical summary (coefficients, p-values, R-squared, ANOVA, GAM/Quantile checks).
- `report.pdf`: Publication-ready PDF with scatter plots, heatmaps, and diagnostics.
- `validation_report.json`: Explicit status of "Code Validated" vs "Scientific Validated".

## Troubleshooting

- **OOM Error**: The pipeline automatically triggers subsampling. If the error persists, reduce `--max-memory` or use a smaller input file.
- **Non-Stationary Data**: If the ADF test fails, the pipeline will segment the data into windows. Check `results/regression_results.json` for per-window results.
- **Missing Variables**: If the input file lacks `contact_forces`, the script will abort with a clear error message.
- **Circularity Warning**: If `dissipation_rate_norm` is used, the report will include a warning about potential tautology.