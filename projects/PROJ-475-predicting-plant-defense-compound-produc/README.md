# PROJ-475: Predicting Plant Defense Compound Production

Automated pipeline for predicting plant defense compound production from public genomic and environmental data.

## Project Structure

```
PROJ-475-predicting-plant-defense-compound-produc/
├── code/ # Source code
│ ├── data/ # Data ingestion, preprocessing, validation
│ ├── models/ # Model training and evaluation
│ ├── utils/ # Utility functions (IO, logging, stats)
│ ├── scripts/ # Utility scripts (linter, manifest, validation)
│ ├── config.py # Configuration loader
│ ├── main.py # Pipeline orchestration
│ └── tests/ # Unit and integration tests
├── data/
│ ├── raw/ # Raw downloaded/generated data
│ ├── processed/ # Processed and validated datasets
│ ├── schema/ # Schema definitions
│ └── manifest.yaml # Artifact manifest with checksums
├── docs/
│ └── api.md # Module API documentation
├── specs/ # Feature specifications and design docs
├── state/ # Pipeline state tracking
├── requirements.txt # Python dependencies
├── quickstart.md # Quick start guide
└── README.md # This file
```

## Prerequisites

- Python 3.11+
- pip (package installer)
- Virtual environment (recommended)

## Setup Instructions

1. **Clone the repository**
 ```bash
 git clone <repository-url>
 cd PROJ-475-predicting-plant-defense-compound-produc
 ```

2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify installation**
 ```bash
 python -m pytest code/tests/ -v
 ```

5. **Run the pipeline**
 ```bash
 python code/main.py
 ```

6. **Validate outputs**
 ```bash
 python code/scripts/validate_quickstart.py
 ```

## Configuration

The pipeline uses a configuration file (`config.yaml` or environment variables) to set:
- Data source URLs (verified only)
- Hyperparameters
- Random seeds
- Output paths

See `code/config.py` for details.

## Data Sources

This project uses real public data from:
- **Genomic**: NCBI SRA (verified URLs only)
- **Environmental**: WorldClim / GBIF
- **Compound Profiles**: ChemBank / PhenolExplorer

If verified URLs are not configured, the pipeline falls back to deterministic mock data generation for CI/testing.

## Output Artifacts

- `data/raw/genomic_vcf.json`
- `data/raw/env_data.json`
- `data/raw/compound_data.json`
- `data/processed/features_vif.csv`
- `data/processed/filtered.csv`
- `data/manifest.yaml`
- `state/PROJ-475-predicting-plant-defense-compound-produc.yaml`

## Testing

Run all tests:
```bash
python -m pytest code/tests/ -v
```

Run specific test suites:
```bash
python -m pytest code/tests/test_ingestion.py -v
python -m pytest code/tests/test_validation.py -v
python -m pytest code/tests/test_models.py -v
```

## Documentation

- **API Docs**: See `docs/api.md` for detailed module documentation.
- **Quick Start**: See `quickstart.md` for a step-by-step guide.
- **Specs**: See `specs/` for feature requirements and design documents.

## Contributing

1. Create a feature branch
2. Implement changes following the task structure in `tasks.md`
3. Write tests for new functionality
4. Run linting and formatting:
 ```bash
 python code/scripts/run_linter.py
 ```
5. Submit a pull request

## License

This project is part of the llmXive automated science pipeline.
