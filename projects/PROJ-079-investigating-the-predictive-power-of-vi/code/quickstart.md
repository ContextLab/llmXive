# Quick Start Guide (5-Minute Run)

This guide walks you through running a minimal version of the pipeline to verify your setup.

## Prerequisites

- Python 3.9+
- pip
- A virtual environment with dependencies installed (`pip install -r requirements.txt`)
- Environment variables set in `.env` (at minimum, `NCBI_API_KEY` if required by your NCBI access level)

## Step 1: Activate Environment

```bash
source venv/bin/activate # Windows: venv\Scripts\activate
```

## Step 2: Run the Pipeline

Execute the main entry point:

```bash
python -m src.main
```

> **Note**: By default, the pipeline expects a small subset of accessions defined in `.env` or `src/config.py`. For a quick test, ensure you have 2–3 viral accessions and 1–2 GEO series listed.

## Step 3: Verify Outputs

Check that the following files have been created:

- `data/processed/merged_dataset.csv`
- `data/processed/aggregated_dataset.csv`
- `data/artifacts/metrics.json`
- `data/artifacts/plots/coefficients.png` (if visualization step completes)

## Troubleshooting

- **Missing API Keys**: Ensure `NCBI_API_KEY` is set in `.env`.
- **Timeout Errors**: Increase `MAX_RUNTIME_HOURS` in `src/config.py` if the pipeline exceeds the default 4-hour limit (not expected for small subsets).
- **Import Errors**: Verify all dependencies in `requirements.txt` are installed.

## Next Steps

- Expand the accession list in `.env` for a full-scale run.
- Review `README.md` for detailed usage and configuration options.
- Run `pytest` to validate your environment's test coverage.