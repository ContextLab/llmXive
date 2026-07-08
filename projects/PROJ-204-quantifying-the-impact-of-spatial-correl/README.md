# Quantifying the Impact of Spatial Correlations in Perovskite Solar Cell Efficiency

This project implements an automated science pipeline to analyze the relationship between elemental map spatial correlations (Pb, I, MA) and perovskite solar cell performance metrics (PCE, Jsc, Voc).

## Project Structure

```
.
├── code/
│ ├── analysis/ # Spatial metrics, Fourier transforms, robustness checks
│ ├── data/ # Data ingestion, alignment, and preprocessing
│ ├── modeling/ # Correlation analysis, GAMs, sensitivity, power analysis
│ ├── preprocess/ # Calibration and defect masking
│ ├── report/ # Report generation (CSV, PDF)
│ ├── validation/ # Co-location and depth resolution checks
│ ├── utils/ # Configuration, state management, ingestion stats
│ └── main_pipeline.py # Main entry point
├── data/
│ ├── raw/ # Downloaded raw EDS maps and metadata
│ └── processed/ # Unified datasets, spatial metrics, correlation results
├── state/
│ └── projects/ # Project state and artifact hashes
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites

- Python 3.9+
- pip
- A Unix-like environment (Linux/macOS/WSL)

## Installation

1. Clone the repository and navigate to the project root:
 ```bash
 git clone <repository-url>
 cd PROJ-204-quantifying-the-impact-of-spatial-correl
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Configuration

The pipeline uses a YAML configuration file. A default configuration is provided in `config.yaml`. You can customize paths, thresholds, and analysis parameters.

Example `config.yaml`:
```yaml
random_seed: 42
min_sample_count: 10
ingestion_success_threshold: 0.8
paths:
 data_raw: "data/raw"
 data_processed: "data/processed"
 state_dir: "state"
 logs_dir: "logs"
```

## Usage

### Running the Full Pipeline

Execute the main pipeline script with an optional configuration file:

```bash
python code/main_pipeline.py --config config.yaml
```

This orchestrates the following steps:
1. **Data Download**: Fetches EDS maps from verified sources (NREL, Zenodo).
2. **Preprocessing**: Aligns maps, masks defects, and calibrates data.
3. **Analysis**: Computes spatial metrics (autocorrelation, Fourier transforms).
4. **Modeling**: Calculates correlations, fits GAMs, performs robustness checks.
5. **Reporting**: Generates summary reports (CSV and PDF).

### Running Individual Modules

You can run specific modules independently for testing or incremental analysis.

#### Data Ingestion
```bash
python code/data/ingest.py --config config.yaml
```
Outputs: `data/processed/unified_dataset.csv`

#### Spatial Metrics Extraction
```bash
python code/analysis/spatial_metrics.py --config config.yaml
```
Outputs: `data/processed/spatial_metrics.csv`

#### Correlation Analysis
```bash
python code/modeling/correlation.py --config config.yaml
```
Outputs: `data/processed/correlation_results.csv`

#### Sensitivity Analysis
```bash
python code/modeling/sensitivity.py --config config.yaml
```
Outputs: `data/processed/sensitivity_analysis.json`

#### Report Generation
```bash
python code/report/generate.py --config config.yaml
```
Outputs: `data/report/summary.csv`, `data/report/summary.pdf`

### Running Tests

Run the full test suite:
```bash
pytest tests/ -v
```

Run specific test categories:
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v
```

### Code Quality

Lint and format the code:
```bash
ruff check code/
black code/
```

## Output Artifacts

After a successful run, the following artifacts will be generated:

- `data/processed/unified_dataset.csv`: Pre-filtered dataset with aligned maps and performance metrics.
- `data/processed/spatial_metrics.csv`: Autocorrelation and Fourier-based spatial metrics.
- `data/processed/correlation_results.csv`: Pearson/Spearman correlations with adjusted p-values.
- `data/processed/sensitivity_analysis.json`: Results of the counter-factual sensitivity analysis.
- `data/report/summary.csv`: Summary statistics for the final report.
- `data/report/summary.pdf`: Human-readable PDF report.
- `state/ingestion_stats.json`: Ingestion success rate and metadata.
- `state/projects/PROJ-204-quantifying-the-impact-of-spatial-correl.yaml`: Project state with artifact hashes.

## Data Sources

The pipeline fetches real data from:
- **NREL Perovskite Database**: Primary source for EDS maps and device performance data.
- **Zenodo**: Supplementary datasets with verified DOIs.

If no data is available or accessible, the pipeline will halt and generate a "Data Availability Report" in `state/data_feasibility_status.yaml`.

## Troubleshooting

- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed.
- **Data Fetching Errors**: Check network connectivity and verify the URLs in `config.yaml`.
- **Memory Issues**: The pipeline is optimized for CPU-only execution. If memory usage is high, reduce batch sizes or process samples individually.
- **Configuration Errors**: Validate your `config.yaml` against the schema in `code/utils/config.py`.

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Implement your changes and write tests.
4. Submit a pull request.

## License

This project is licensed under the MIT License. See `LICENSE` for details.