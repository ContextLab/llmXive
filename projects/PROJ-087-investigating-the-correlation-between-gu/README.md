# Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

This project implements an automated science pipeline to investigate the correlation between gut microbiome composition and sleep quality. It ingests raw data, performs statistical analysis (Spearman correlation with Benjamini-Hochberg correction), and generates visualizations and reports.

## Data Source

The pipeline relies on a verified external dataset containing microbiome OTU tables and sleep metadata. The specific source URL and access instructions are defined in the project's configuration environment variables (`DATA_URL`).

**Requirement**: The dataset must contain the following columns:
- `antibiotic_use_last_3m`: Boolean or indicator for recent antibiotic use (samples with `True` are excluded).
- `sleep_efficiency`: Float (0-100 or 0-1).
- `sleep_duration_hours`: Float.
- Microbiome feature columns (OTU counts).

If the `DATA_URL` is missing or the schema is invalid, the ingestion pipeline will halt with a `FileNotFoundError`.

## Usage Examples

### Prerequisites
- Python 3.11+
- Dependencies installed via `pip install -r requirements.txt`

### Running the Full Pipeline

Set the required environment variables:
```bash
export DATA_URL=""
export RANDOM_SEED=42
export LOG_LEVEL=INFO
```

Execute the pipeline step-by-step or run the main entry points:

1. **Ingestion**: Download, filter, and merge data.
 ```bash
 python -m src.ingestion
 ```
 Outputs: `data/processed/cleaned_microbiome_sleep.csv`, `data/processed/ingestion_report.json`

2. **Diversity Analysis**: Calculate alpha-diversity indices.
 ```bash
 python -m src.diversity
 ```
 Outputs: Appended diversity metrics to the processed dataset.

3. **Correlation Analysis**: Compute Spearman correlations and FDR correction.
 ```bash
 python -m src.correlation
 ```
 Outputs: `data/processed/correlation_results.csv`

4. **Visualization**: Generate scatterplots and boxplots.
 ```bash
 python -m src.viz
 ```
 Outputs: Plot files in `data/processed/plots/`

5. **Reporting**: Generate the final summary report.
 ```bash
 python -m src.report
 ```
 Outputs: `data/processed/report.txt`

### Running Tests
```bash
pytest tests/unit/ -v
```

### Configuration
Configuration is loaded from environment variables with sensible defaults:
- `DATA_URL`: URL to the raw dataset.
- `RANDOM_SEED`: Integer for reproducibility (default: 42).
- `LOG_LEVEL`: Logging verbosity (default: INFO).

See `src/config.py` for implementation details.
