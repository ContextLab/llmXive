# Quickstart Guide: Climate-Smart Agriculture & Food Security Analysis

This guide provides step-by-step instructions to reproduce the full research pipeline for analyzing the impact of Climate-Smart Agricultural (CSA) practices on food security in rural areas.

## Prerequisites

- Python 3.11 or higher
- 7GB+ available RAM
- Internet connection (for data download)
- Valid API access for LSMS, FAOSTAT, and NASA POWER (if required by specific endpoints)

## 1. Environment Setup

Navigate to the project root and install dependencies:

```bash
cd code
pip install -r requirements.txt
```

Ensure the following directories exist (run if missing):

```bash
python setup_directories.py
```

## 2. Configuration

Set environment variables or edit `code/.env` (if present) to define:

- `TARGET_COUNTRIES`: Comma-separated list (e.g., `KE,IN,VN`)
- `TARGET_YEARS`: Comma-separated list (e.g., `2020,2021,2022`)
- `DATA_DIR`: Absolute path to the data directory

Example `.env`:
```
TARGET_COUNTRIES=KE,IN,VN
TARGET_YEARS=2020,2021,2022
DATA_DIR=/path/to/project/data
```

## 3. Data Pipeline Execution

Run the full data ingestion, cleaning, and sampling pipeline:

```bash
python main.py --stage data
```

This will:
1. Download raw data from LSMS, FAOSTAT, and NASA POWER.
2. Clean, merge, and impute missing values.
3. Apply stratified sampling with design weights.
4. Save the final dataset to `data/processed/merged_sample.parquet`.

**Output**: `data/processed/merged_sample.parquet`

## 4. Statistical Modeling

Run the mixed-effects regression, mediation analysis, and robustness checks:

```bash
python main.py --stage analysis
```

This will:
1. Construct the CSA Index (excluding digital/finance access).
2. Fit Mixed-Effects models with interaction terms.
3. Apply Benjamini-Hochberg FDR correction.
4. Perform bootstrap resampling and leave-one-region-out validation.
5. Save model results to `data/processed/model_results.json` and `data/processed/diagnostics.json`.

**Output**: `data/processed/model_results.json`, `data/processed/diagnostics.json`

## 5. Visualization

Generate plots and robustness reports:

```bash
python main.py --stage viz
```

This will:
1. Create scatter plots (CSA Index vs. Food Security).
2. Generate coefficient plots with confidence intervals.
3. Produce regional maps of CSA adoption.
4. Save figures to `figures/`.

**Output**: `figures/scatter_plot.png`, `figures/coefficient_plot.png`, `figures/regional_map.png`

## 6. Validation & Testing

Run the test suite to verify data integrity and model correctness:

```bash
pytest tests/ -v
```

Key tests include:
- Schema validation (`tests/contract/test_dataset_schema.py`)
- Data pipeline integration (`tests/integration/test_data_pipeline.py`)
- Model diagnostics (`tests/unit/test_diagnostics.py`)
- FDR correction verification (`tests/unit/test_model_correction.py`)

## 7. Troubleshooting

- **RAM Issues**: If the process exceeds 7GB, reduce `TARGET_YEARS` or sample size in `code/utils/config.py`.
- **Missing Data**: Ensure API keys are set if required for LSMS/FAOSTAT/NASA POWER.
- **Timeouts**: The model stage includes automatic retry logic for long-running tasks.

## 8. Reproducibility

To ensure full reproducibility:
- Use the pinned versions in `requirements.txt`.
- Run the pipeline in the order: Data → Analysis → Viz.
- Checksums for raw data are stored in `state/checksums.json`.

For detailed API documentation, refer to the docstrings in `code/` modules.