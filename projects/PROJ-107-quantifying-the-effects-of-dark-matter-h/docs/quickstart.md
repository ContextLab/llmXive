# Quick Start Guide

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Access to TNG-100 API (requires API key)

## Installation

1. Clone the repository and navigate to the project root:
 ```bash
 git clone <repository-url>
 cd PROJ-107-quantifying-the-effects-of-dark-matter-h
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

4. Configure your TNG API key:
 - Set the `TNG_API_KEY` environment variable
 - Or create a `.env` file in the project root with:
 ```
 TNG_API_KEY=your_api_key_here
 ```

## Running the Pipeline

The main entry point is `code/main.py`. Execute the full pipeline:

```bash
python code/main.py
```

### Stage-Specific Execution

You can run individual stages:

```bash
# Ingestion stage only
python code/main.py --stage ingestion

# Processing stage only
python code/main.py --stage processing

# Statistical analysis stage
python code/main.py --stage statistics

# Alignment analysis stage
python code/main.py --stage alignment

# Final report generation
python code/main.py --stage report
```

### Dry Run

To test the pipeline without executing heavy computations:

```bash
python code/main.py --dry-run
```

## Output Files

After successful execution, results are available in:

- `data/processed/halo_shapes.csv` - Computed halo shape metrics
- `data/processed/galaxy_properties.csv` - Central galaxy properties
- `data/processed/matched_chunks/` - Mass-matched dataset chunks
- `data/processed/statistical_results.csv` - Statistical test results
- `data/processed/alignment_angles.csv` - Orientation misalignment data
- `outputs/reports/final_report.md` - Comprehensive research report

## Verification

Run the test suite to verify installation:

```bash
pytest code/tests/
```

Key tests:
- `code/tests/test_pipeline.py` - Integration tests for data fetching and processing
- `code/tests/test_stats.py` - Statistical analysis verification
- `code/tests/test_shape_metrics.py` - Shape computation validation

## Troubleshooting

- **API Key Errors**: Ensure `TNG_API_KEY` is set correctly
- **Memory Issues**: The pipeline uses chunked streaming; reduce chunk size in `code/utils/config.py` if needed
- **Missing Data**: Check `data/metadata.yaml` for dataset availability status

## Next Steps

1. Review `outputs/reports/final_report.md` for analysis results
2. Examine `data/processed/sensitivity_results.csv` for robustness validation
3. Consult `docs/` for detailed documentation on specific modules