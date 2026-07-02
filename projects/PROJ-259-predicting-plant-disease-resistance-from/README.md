# Predict Plant Disease Resistance from Multi-omics Data

Automated science pipeline for predicting plant disease resistance using integrated SNP and metabolite data.

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Feature selection, modeling, validation
│ ├── data/ # Data download, preprocessing, splitting
│ ├── utils/ # Utilities (exceptions, logging, stats)
│ ├── config.py # Configuration management
│ └── main.py # CLI entry point
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Preprocessed and aligned data
├── artifacts/ # Model outputs and reports
│ ├── models/ # Trained model files
│ ├── reports/ # Metrics and analysis reports
│ └── figures/ # Visualization outputs
├── tests/ # Test suites
├── specs/ # Design documents
├── Dockerfile # Container definition
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites

- Docker (for containerized execution)
- Python 3.11+ (for local execution)
- pip for package management

## Quick Start (Docker)

### Build the Docker Image

Build the container image containing Python 3.11, bioinformatics tools (fastp, bcftools), and project dependencies:

```bash
# Navigate to project root
cd /path/to/project

# Build the image (tag: plant-disease-resistance:latest)
docker build -t plant-disease-resistance:latest.
```

### Run the Pipeline

Execute the full pipeline inside the container:

```bash
# Run the main pipeline script
docker run --rm -v $(pwd):/app -w /app plant-disease-resistance:latest \
 python code/main.py

# Run with specific configuration (optional)
docker run --rm -v $(pwd):/app -w /app -e DATA_SOURCE=simulated \
 plant-disease-resistance:latest python code/main.py
```

### Interactive Shell

For debugging or manual inspection:

```bash
# Start an interactive shell inside the container
docker run --rm -it -v $(pwd):/app -w /app plant-disease-resistance:latest bash
```

## Local Execution (Python)

If you prefer running locally without Docker:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the pipeline
python code/main.py
```

## Configuration

The pipeline reads configuration from environment variables:

- `DATA_SOURCE`: Either `real` (fetch from NCBI/MetaboLights) or `simulated` (generate synthetic data)
- `DATA_PATH`: Directory for raw data (default: `data/raw`)
- `PROCESSED_DATA_PATH`: Directory for processed data (default: `data/processed`)
- `ARTIFACTS_PATH`: Directory for outputs (default: `artifacts`)

Example:
```bash
export DATA_SOURCE=simulated
python code/main.py
```

## Output Artifacts

After successful execution, the following artifacts are generated:

- `artifacts/reports/metrics.json`: Model performance metrics (CV accuracy, AUC/R², null model comparison)
- `artifacts/reports/selection_frequency.csv`: Feature selection frequencies across thresholds
- `artifacts/reports/top_features.csv`: Ranked list of significant biomarkers with p-values and effect sizes
- `artifacts/reports/holdout_metrics.json`: Independent validation results with permutation p-values
- `artifacts/models/`: Serialized trained models

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_pipeline.py -v
```

### Linting and Formatting

```bash
# Check code style
flake8 code/

# Format code
black code/
```

## Troubleshooting

### Docker Build Failures

If the build fails due to missing tools:
1. Ensure Docker is running (`docker info`)
2. Check network connectivity for package downloads
3. Verify `Dockerfile` has correct base image and tool installation steps

### Data Download Errors

If real data fetch fails:
1. Check internet connectivity
2. Verify accession IDs in `data/data_manifest.yaml`
3. Set `DATA_SOURCE=simulated` to use synthetic data for testing

### Memory Issues

For large datasets:
1. Increase container memory limit: `docker run -m 8g...`
2. Enable data chunking in preprocessing steps
3. Use stratified sampling to reduce dataset size

## License

This project is part of the llmXive automated science pipeline. See LICENSE for details.

## References

- FR-006: Documentation requirements for Docker usage
- Plan.md: Project planning document
- Spec.md: User stories and feature requirements