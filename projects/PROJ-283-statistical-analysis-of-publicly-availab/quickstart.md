# Quick Start Guide

This guide provides step-by-step instructions for running the chess Elo rating analysis pipeline.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- At least 7GB of available RAM (for full dataset processing)

## Step 1: Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd <project-name>

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Verify Configuration

The configuration file `code/src/config.py` contains:
- `RANDOM_SEED`: Random seed for reproducibility (default: 42)
- `DATA_DIR`: Path to data directory (default: `data/`)
- `LICHOSS_DATASET_URL`: URL for Lichess dataset

Review and adjust these settings if needed.

## Step 3: Run the Pipeline

### Full Pipeline

To run the complete analysis pipeline:

```bash
python code/src/main.py
```

This will:
1. Download chess game data from Lichess
2. Parse PGN files and extract features
3. Calculate Elo probabilities and deviations
4. Fit statistical models (Gaussian GLM and Ridge Regression)
5. Perform cross-validation and sensitivity analysis
6. Generate diagnostic plots and reports

### Individual Components

You can also run individual components:

```bash
# Download data only
python code/src/data/download.py

# Parse PGN files
python code/src/data/parse.py

# Process game records
python code/src/data/process.py

# Fit models
python code/src/models/fit.py

# Calculate metrics
python code/src/models/metrics.py

# Run validation
python code/src/models/validate.py

# Generate plots
python code/src/reports/generate_plots.py
```

## Step 4: Verify Outputs

After running the pipeline, check the output files:

```bash
# Processed game data
ls data/processed/

# Model metrics
cat data/results/model_metrics.json

# Diagnostic report
cat data/results/diagnostics.json

# Generated plots
ls data/results/*.png
```

## Step 5: Run Tests

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run contract tests only
pytest tests/contract/

# Run integration tests only
pytest tests/integration/
```

## Common Issues

### Memory Issues

If you encounter memory issues with the full dataset:
- The pipeline automatically streams data in chunks
- You can adjust the sample size in `code/src/config.py`
- Consider using a smaller subset of the data for testing

### API Rate Limiting

If you hit rate limits when downloading data:
- The download module includes exponential backoff retry logic
- You can adjust retry parameters in `code/src/data/download.py`

### Validation Errors

If schema validation fails:
- Check the log output for specific validation errors
- Verify that the input data matches the expected schema
- Review the contract definitions in `specs/contracts/`

## Next Steps

- Review the diagnostic plots in `data/results/`
- Analyze the model metrics in `data/results/model_metrics.json`
- Read the detailed API documentation in the source code
- Contribute to the project by adding new features or improvements

## Support

For issues or questions, please open an issue in the project repository.