# Quickstart: Impact of Environmental Factors on Fungal Community Structure in Soil

## Prerequisites
*   Python 3.11+
*   `git`
*   At least 14 GB free disk space (for data and dependencies).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <project-dir>
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
    *Note: `requirements.txt` pins all versions to ensure reproducibility.*

## Data Setup

**Important**: This project requires at least 3 verified datasets with ITS sequences and matching metadata.
*   If no verified datasets are found in the `data/` directory, the workflow will abort with a `FATAL` error.
*   For development, you may generate synthetic data using `code/utils/generate_synthetic_data.py` (only for testing pipeline logic, not for final results).

1.  **Place data in `data/`**:
    *   Raw FASTQs (if available): `data/raw-seq/`
    *   Metadata CSVs: `data/metadata/raw/`

2.  **Verify data integrity**:
    ```bash
    python code/utils/checksums.py --verify
    ```

## Running the Workflow

Execute the full pipeline:
```bash
python -m src.cli.main --run-full
```

### Options
*   `--run-full`: Run ingestion, preprocessing, analysis, and reporting.
*   `--stratify-by biome`: Enable biome-specific stratification (FR-005).
*   `--sweep-thresholds`: Run sensitivity analysis (FR-006).
*   `--dry-run`: Validate configuration and data availability without processing.
*   `--mode pipeline-validation`: Use synthetic data for code testing (skips real data abort).

### Example: Stratified Analysis
```bash
python -m src.cli.main --run-full --stratify-by biome --sweep-thresholds
```

## Output

Results are saved in the `results/` directory:
*   `results/permanova_summary.csv`: Global PERMANOVA results.
*   `results/db_rda_variance.csv`: Variance explained by each predictor.
*   `results/db_rda_biome_<NAME>.csv`: Stratified results per biome.
*   `results/sensitivity_analysis.csv`: Robustness of driver ranking.
*   `results/robustness_summary.md`: Narrative summary of findings.
*   `results/sampling_report.csv`: **Mandatory** log of subsampling ratios (FR-009).
*   `results/plots/`: PNG figures (db-RDA triplots, etc.).

## Troubleshooting

*   **"Insufficient datasets for global analysis"**: Ensure at least 3 datasets with all required metadata columns (pH, nutrients, etc.) are present in `data/metadata/`.
*   **"Memory limit exceeded"**: The system will automatically subsample. Check `results/sampling_report.csv` for the ratio used.
*   **"MICE convergence failed"**: Samples with missing values in those studies will be excluded. Check logs for warnings.
