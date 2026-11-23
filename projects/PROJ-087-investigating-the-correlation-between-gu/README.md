# Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

This project investigates the statistical correlation between gut microbiome alpha-diversity indices (Shannon, Simpson, Observed OTUs) and sleep quality metrics (efficiency, duration). The pipeline ingests raw data, filters for confounders (antibiotic use), computes diversity, runs Spearman correlations with FDR correction, and generates visualizations and reports.

## Data Source

This project relies on a verified external dataset containing microbiome OTU tables and associated sleep metadata.

**Data Source Details**:
- **URL**: The specific URL is configured via the `DATA_URL` environment variable or found in the `config.py` defaults.
- **Format**: CSV (OTU table and metadata merged or separate files as per ingestion logic).
- **Required Columns**:
 - `antibiotic_use_last_3m`: Boolean or string indicator of recent antibiotic use.
 - `sleep_efficiency`: Numeric value (0-100 or 0-1).
 - `sleep_duration_hours`: Numeric value.
 - OTU columns: Pre-fixed or identified via schema verification.

**Note**: If the verified data source is unavailable or the schema does not match, the pipeline will halt and generate a blocked status report (`data/processed/ingestion_report.json`) rather than fabricating data.

## Usage Examples

### Prerequisites
Ensure Python 3.11+ is installed and dependencies are satisfied:
```bash
pip install -r requirements.txt
```

### Environment Configuration
Set the required environment variables (or rely on defaults in `src/config.py`):
```bash
export DATA_URL=""
export RANDOM_SEED=42
export LOG_LEVEL=INFO
```

### Running the Full Pipeline
The pipeline is orchestrated via the main entry point `src/main.py` (if exists) or by running the stage scripts sequentially.

1. **Data Ingestion (T013-T017)**:
 Downloads and cleans data.
 ```bash
 python -m src.ingestion
 ```
 *Output*: `data/processed/cleaned_microbiome_sleep.csv`, `data/processed/ingestion_report.json`

2. **Diversity Analysis (T020b)**:
 Computes alpha-diversity with rarefaction.
 ```bash
 python -m src.diversity
 ```
 *Output*: `data/processed/diversity_indices.csv` (intermediate)

3. **Correlation Analysis (T021-T024)**:
 Computes Spearman correlations and applies Benjamini-Hochberg correction.
 ```bash
 python -m src.correlation
 ```
 *Output*: `data/processed/correlation_results.csv`

4. **Visualization (T027-T030)**:
 Generates scatterplots and boxplots.
 ```bash
 python -m src.viz
 ```
 *Output*: `data/processed/plots/scatterplot_shannon_sleep.png`, `data/processed/plots/boxplot_sleep_quartile.png`

5. **Reporting (T029, T031)**:
 Generates the final HTML report.
 ```bash
 python -m src.report_final
 ```
 *Output*: `data/processed/final_report.html`

### Running Specific Scripts
Individual scripts can be run directly from the `code` directory:
```bash
# Example: Run ingestion
python src/ingestion.py

# Example: Run correlation
python src/correlation.py
```

### Running Tests
```bash
pytest tests/
```

## Project Structure
```
.
├── code/
│ ├── src/ # Source code modules
│ │ ├── config.py
│ │ ├── ingestion.py
│ │ ├── diversity.py
│ │ ├── correlation.py
│ │ ├── viz.py
│ │ ├── report_final.py
│ │ └── models/
│ ├── tests/ # Unit and integration tests
│ ├── data/ # Data directories (raw, processed)
│ └──...
├── README.md
├── requirements.txt
└──...
```

## License
[Insert License Information]
