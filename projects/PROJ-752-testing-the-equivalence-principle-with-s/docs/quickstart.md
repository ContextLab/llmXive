# Quickstart Guide: Testing the Equivalence Principle with Satellite Laser Ranging

This guide provides instructions to validate the reproducibility of the `PROJ-752` pipeline.

## Prerequisites

- Python 3.9+
- `pip` and `venv`
- Access to the ILRS data archive (for full run) or cached data.

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Validation Procedure (T046)

To ensure the pipeline is reproducible and all artifacts are correctly generated, run the validation script:

```bash
python code/scripts/validate_quickstart.py
```

### What this script does:
1. **Configuration Check**: Verifies `config.yaml` is present and valid.
2. **Data Verification**: Checks for `data/processed/cleaned_slr_data.csv` and other required inputs. If missing, it attempts to run the ingestion pipeline.
3. **Lightweight Run**: Executes a minimal subset of the analysis (preprocessing and logic checks) to verify code integrity without requiring a full orbit determination.
4. **Artifact Validation**: Computes SHA-256 hashes for generated data and saves a report to `data/results/quickstart_validation_report.json`.

### Expected Output
- A log file at `data/logs/quickstart_validation.log`.
- A JSON report at `data/results/quickstart_validation_report.json`.
- Exit code `0` on success, `1` on failure.

## Full Pipeline Execution

To run the full analysis (requires significant time and data):

```bash
python code/cli/main.py --run-full
```

## Troubleshooting

- **Missing Data**: If the script fails due to missing data, ensure you have internet access to download from ILRS or that `data/verified_datasets.yaml` contains valid URLs.
- **Configuration Errors**: Verify `config.yaml` has the `benchmark_values.etvos_limit` key populated (see Research Phase T048).
