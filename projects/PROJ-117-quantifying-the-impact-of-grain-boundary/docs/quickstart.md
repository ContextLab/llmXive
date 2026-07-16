# Quickstart Guide

This guide provides a minimal example to get started with the Grain Boundary Diffusivity pipeline.

## Prerequisites

- Python 3.9+
- pip package manager
- API keys for Materials Project and OpenKIM

## Step 1: Clone and Setup

```bash
git clone <repository-url>
cd PROJ-117-quantifying-the-impact-of-grain-boundary
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Configure Environment

Create a `.env` file in the project root:

```bash
MP_API_KEY=your_materials_project_api_key
OPENKIM_API_KEY=your_openkim_api_key
```

## Step 3: Run the Pipeline

Execute the pipeline steps in order:

```bash
# Download raw data
python code/download.py

# Parse geometry
python code/geometry_parser.py

# Preprocess and validate
python code/preprocess.py

# Run diagnostics
python code/diagnostics.py

# Train model
python code/train.py

# Validate model
python code/validate.py

# Generate interpretability reports
python code/interpret.py
```

## Step 4: Verify Outputs

Check that the following artifacts were created:

```bash
ls -la data/raw/
ls -la data/processed/
ls -la models/
ls -la artifacts/reports/
ls -la artifacts/figures/
```

## Step 5: Run Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Quickstart validation
python code/validate_quickstart.py
```

## Troubleshooting

### API Key Errors
Ensure `.env` file exists and contains valid API keys.

### Data Insufficiency
If the pipeline fails with "Data Insufficiency", check that:
- Your API keys have access to sufficient data
- The search keywords match available records
- You have at least 500 valid records after preprocessing

### Memory Errors
The pipeline is designed to run within 7GB RAM. [UNRESOLVED-CLAIM: c_b3dcd4d3 — status=not_enough_info] If you encounter memory issues:
- Reduce the dataset size by filtering early
- Use streaming mode for large datasets (if supported)

## Next Steps

- Read the [API Reference](api_reference.md) for detailed module documentation
- Review the [Data Schema](data_schema.md) for data format details
- Check the [README](../README.md) for project overview
