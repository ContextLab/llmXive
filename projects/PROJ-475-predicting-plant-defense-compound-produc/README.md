# PROJ-475: Predicting Plant Defense Compound Production

## Overview
This project implements a machine learning pipeline to predict plant defense compound production using public genomic and environmental data. The pipeline ingests VCF genomic data, environmental CSV data, and compound JSON data, merges them, performs feature engineering, trains a regularized regression model, and conducts statistical significance testing.

## Project Structure
```
.
├── code/ # Source code
│ ├── config.py # Configuration loader
│ ├── data/ # Data ingestion, validation, preprocessing
│ │ ├── ingestion.py
│ │ ├── validation.py
│ │ ├── preprocessing.py
│ │ └── mock_generator.py
│ ├── models/ # Model training and evaluation
│ │ ├── training.py
│ │ └── evaluation.py
│ ├── utils/ # Utility functions
│ │ ├── io.py
│ │ ├── logging.py
│ │ └── stats.py
│ ├── scripts/ # Pipeline scripts
│ │ ├── generate_mock_data.py
│ │ ├── run_validation.py
│ │ ├── run_preprocessing.py
│ │ ├── update_manifest.py
│ │ └── validate_quickstart.py
│ ├── tests/ # Unit and integration tests
│ └── main.py # Main pipeline orchestrator
├── data/ # Data storage
│ ├── raw/ # Raw downloaded/generated data
│ ├── processed/ # Processed/merged data
│ └── schema/ # Data schemas
├── docs/ # Documentation
├── logs/ # Execution logs
├── results/ # Model results and reports
├── specs/ # Feature specifications
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- pip

### Installation
1. Clone the repository
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

### Configuration
Create a `config.yaml` file in the project root with the following structure:
```yaml
seeds:
 random_seed: 42
paths:
 data_raw: "data/raw"
 data_processed: "data/processed"
 logs: "logs"
 results: "results"
verified_urls:
 genomic: ""
 env: ""
 compound: ""
hyperparameters:
 alpha: 0.1
 cv_folds: 5
```

If no `config.yaml` is provided or URLs are unavailable, the pipeline will generate deterministic mock data for testing.

## Running the Pipeline

### Full Pipeline Execution
```bash
python code/main.py
```

### Individual Steps
- Generate mock data (for CI/testing):
 ```bash
 python code/scripts/generate_mock_data.py
 ```
- Run data ingestion and validation:
 ```bash
 python code/scripts/run_validation.py
 ```
- Run feature engineering and preprocessing:
 ```bash
 python code/scripts/run_preprocessing.py
 ```
- Validate quickstart requirements:
 ```bash
 python code/scripts/validate_quickstart.py
 ```

### Running Tests
```bash
pytest code/tests/ -v
```

## Data Outputs
The pipeline produces the following artifacts:
- `data/raw/genomic.vcf` or `data/raw/mock_genomic.vcf`
- `data/raw/env_data.csv` or `data/raw/mock_env.csv`
- `data/raw/compound_data.json` or `data/raw/mock_compounds.json`
- `data/processed/merged_raw.csv`
- `data/processed/final_cleaned.csv`
- `data/processed/variant_table.csv`
- `data/processed/diversity_metrics.csv`
- `data/processed/features_normalized.csv`
- `results/model.pkl`
- `results/stability_report.json`

## Documentation
See `docs/api.md` for detailed module documentation.

## License
This project is for research purposes.
