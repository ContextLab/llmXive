# Quickstart: Testing the Equivalence Principle with Satellite Laser Ranging

## Prerequisites
*   Python 3.11+
*   `pip`
*   Access to a GitHub Actions runner (or local environment with similar constraints)

## Installation

1.  Clone the repository and navigate to the project directory.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: `requirements.txt` will pin `numpy`, `scipy`, `pandas`, `astropy`, `huggingface_hub`, `pyyaml`, `pytest`)*

## Running the Pipeline

The main entry point is `src/cli/main.py`.

### Step 1: Data Ingestion
The script will attempt to load data from the verified Hugging Face dataset. If satellites are missing, it will fall back to the verified ILRS archive.
```bash
python -m src.cli.main --stage ingestion
```
*   **Output**: `data/processed/cleaned_slr_data.csv`
*   **Note**: If the verified dataset lacks required satellites, the script will log a warning and proceed with available data, flagging the result as "Incomplete".

### Step 2: Orbit Determination & Estimation
Run the joint estimation with shared error terms.
```bash
python -m src.cli.main --stage estimation
```
*   **Output**: In-memory `OrbitSolution` objects (logged to console and saved to `data/processed/orbit_solutions.json`).

### Step 3: Validation & Sensitivity Analysis
Run the F-test, geopotential/systematic sweep, simulation validation, and benchmark comparison.
```bash
python -m src.cli.main --stage validation
```
*   **Output**: `data/processed/eotvos_result.json`, diagnostic plots.

### Step 4: Full Run
Execute the entire pipeline end-to-end.
```bash
python -m src.cli.main --stage full
```

## Verification

To verify the pipeline:
1.  Run `pytest tests/` to ensure unit and integration tests pass.
2.  Check `state/projects/PROJ-752-testing-the-equivalence-principle-with-s.yaml` for artifact checksums.
3.  Verify that `data/processed/cleaned_slr_data.csv` has no NaN values in the `range` column.
4.  Verify that `data/processed/eotvos_result.json` contains the `chi2_improvement`, `simulation_validation`, and `consistency_check` fields.

## Troubleshooting

*   **HTTP 403 / 404 Errors**: The ingestion script implements exponential backoff. If the verified dataset URL becomes unreachable, the script will fail gracefully with a clear error message.
*   **Memory Errors**: If the dataset is too large, the script will automatically switch to streaming mode or sample the data. Check logs for "Memory limit exceeded" warnings.
*   **Missing Satellites**: If the log reports "Insufficient Data" for a specific satellite, the differential analysis will proceed only for available pairs, and the final report will be flagged as "Incomplete".
*   **Underpowered**: If N < 10,000 per satellite, the report will be flagged as "Underpowered".