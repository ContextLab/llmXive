# Quickstart Guide: Predicting Plant Root Architecture from Soil Nutrient Profiles

This guide provides instructions for setting up and running the `llmXive` automated science pipeline for predicting plant root architecture.

## Prerequisites

- Python 3.9 or higher
- `pip` package manager
- Access to the internet (for data fetching and package installation)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create and activate a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Configure environment variables**:
 - Copy `.env.example` to `.env` (if provided) or create a new `.env` file in the root directory.
 - Add necessary API keys or configuration values as specified in the project documentation.
 ```bash
 # Example.env content
 RUN_MODE=production
 DATA_SOURCE_URL=<your-data-source-url>
 ```

## Project Structure

```
.
├── code/ # Source code
│ ├── ingestion/ # Data ingestion and processing
│ ├── modeling/ # Model training and evaluation
│ ├── utils/ # Utility functions
│ └──...
├── data/ # Data storage
│ ├── raw/ # Raw data files
│ ├── processed/ # Processed data files
│ └── logs/ # Log files
├── docs/ # Documentation
├── tests/ # Test suites
├── artifacts/ # Model artifacts and metrics
├── figures/ # Generated plots and figures
├── requirements.txt # Python dependencies
├── quickstart.md # This file
└── research.md # Research documentation
```

## Running the Pipeline

The pipeline consists of several stages. You can run the entire pipeline or individual stages.

### Full Pipeline Execution

To run the complete pipeline from data ingestion to model evaluation:

```bash
python code/main.py
```

This will:
1. Validate data sources (T000)
2. Ingest and process soil and root trait data (T012, T013, T014)
3. Validate and merge datasets (T015, T017)
4. Train and evaluate models (T020A1..E, T021..T023)
5. Generate feature importance and sensitivity analysis (T025a..T029)

### Individual Stage Execution

You can also run specific stages independently:

#### Data Ingestion and Validation

```bash
python code/ingestion/source_validation.py
python code/ingestion/soil_data.py
python code/ingestion/trait_data.py
python code/ingestion/merge.py
python code/ingestion/validation.py
```

#### Model Training and Evaluation

```bash
python code/modeling/train.py
python code/modeling/baseline.py
python code/modeling/sc002_validator.py
```

#### Feature Importance and Sensitivity Analysis

```bash
python code/modeling/feature_importance.py
python code/modeling/sensitivity.py
```

## Output Artifacts

After successful execution, the following artifacts will be generated:

- **Processed Data**: `data/processed/merged_dataset.csv`
- **Model Metrics**: `artifacts/model_metrics.json`
- **Feature Importance**: `artifacts/feature_importance.csv` and `figures/feature_importance.png`
- **Sensitivity Report**: `artifacts/sensitivity_report.md`
- **Logs**: `data/logs/` directory containing execution logs

## Validation

To validate the pipeline and ensure reproducibility:

```bash
python code/validation/validate_quickstart.py
```

This script checks that all required files exist and that the pipeline can be executed end-to-end.

## Troubleshooting

### Common Issues

- **Data Fetch Errors**: Ensure `RUN_MODE` is set correctly in `.env`. In production mode, the pipeline will fail if real data cannot be fetched.
- **API Key Errors**: Verify that all required API keys are correctly configured in the `.env` file.
- **Missing Dependencies**: Re-run `pip install -r requirements.txt` to ensure all dependencies are installed.

### Logs

Check the log files in `data/logs/` for detailed error messages and execution status.

## Next Steps

- Review the research documentation in `docs/research.md` for methodology and data sources.
- Explore the generated figures and reports in the `artifacts/` and `figures/` directories.
- Contribute to the project by implementing additional features or improving existing ones.

## Support

For issues or questions, please refer to the project's issue tracker or contact the maintainers.
