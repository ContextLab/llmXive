# Quickstart: Quantifying the Impact of Network Structure on Energy Dissipation in Driven Granular Materials

## Prerequisites

- Python 3.10 or higher
- Git
- Access to a GitHub Actions runner (for CI) or a local Linux environment with ≥7GB RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-468-quantifying-the-impact-of-network-struct/code
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins specific versions to ensure reproducibility.*

## Running the Pipeline

### Option A: Synthetic Test (Recommended for First Run)

This generates a small-scale synthetic DEM dataset and runs the full pipeline to verify functionality.

```bash
python main.py --mode synthetic --output data/processed/synthetic_results.json
```

- **Expected Output**: A `synthetic_results.json` file and a `synthetic_report.pdf` in `data/processed/`.
- **Runtime**: [deferred].
- **Memory**: < 1GB.

### Option B: Real Data Analysis

1.  **Prepare Data**: Place your Yade-DEM output file (e.g., `simulation.csv`) in `data/raw/`.
2.  **Run Pipeline**:
    ```bash
    python main.py --input data/raw/simulation.csv --output data/processed/real_results.json
    ```
3.  **Check Logs**: Monitor `logs/pipeline.log` for warnings about missing data or subsampling triggers.

## Verifying Results

1.  **Check Metrics**: Open `data/processed/metrics_<run_id>.csv` to ensure non-null values for `mean_coordination`, `clustering_coeff`, and `dissipation_rate`.
2.  **Review Report**: Open `data/processed/report_<run_id>.pdf` to visualize correlations and regression diagnostics.
3.  **Validate JSON**: Ensure `analysis_results_<run_id>.json` contains `p_values` < 0.01 for significant findings.

## Troubleshooting

- **Memory Error**: If you encounter `MemoryError`, the system should have automatically triggered subsampling. If not, reduce the input file size or increase the `--subsample-ratio` flag.
- **Missing Forces**: The system logs a warning if >50% of contacts are missing in a timestep. Such timesteps are excluded.
- **Static Packing**: If driving amplitude is zero, the system calculates dissipation as `|ΔKE + ΔPE|`.

## Next Steps

- **Customization**: Modify `code/extraction/network_metrics.py` to add new topological metrics.
- **Extended Analysis**: Add new datasets to `data/raw/` and run the validation module for cross-dataset comparison.
- **Publication**: Use the generated PDF report as a draft for your scientific paper.
