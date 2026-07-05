# Quickstart: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for dataset fetching)

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/requirements.txt
   ```

## Running the Pipeline

The pipeline is executed via the master orchestrator script `00_run_pipeline.py` which coordinates the sequential execution of data extraction, cleaning, training, and analysis:

```bash
# Run the full pipeline (Data Extraction -> Cleaning -> Training -> Analysis)
python projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/00_run_pipeline.py
```

**Note**: If the Materials Project or NIST APIs are unreachable, or if the dataset lacks sufficient independent measurements (N < 50) after filtering, the script will halt with an error message indicating the data source failure or data unavailability.

## Verifying Results

1. **Check Data**: Inspect `data/processed/processed_data.parquet` to ensure rows are present.
2. **Check Metrics**: Inspect `data/processed/model_results.json` for `cv_mae`, `test_mae`, `vif_scores`, and `null_model_threshold`.
3. **Check Contracts**: Run the contract validation tests:
   ```bash
   pytest tests/test_contracts.py
   ```

## Troubleshooting

- **Error: "Insufficient Data: <50 independent measurements found"**: The dataset contained too many entries where Poisson's ratio was derived from Young's modulus alone. The pipeline cannot proceed without a minimum of 50 independent measurements.
- **Error: "Data Source Unavailable"**: The Materials Project or NIST APIs are unreachable or require authentication.
- **Error: "Insufficient Power"**: The sample size is too small to detect meaningful effects (MDES > 0.1).
- **Error: "VIF > 5"**: This is a warning, not a crash. The pipeline continues but flags high collinearity in the diagnostics (check `vif_scores` in results).
- **Error: "Poisson's ratio derived"**: Entries where Poisson's ratio is calculated from Young's modulus are excluded per FR-009.