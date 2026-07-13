# Quickstart: The Impact of Social Comparison on Self-Perception on AI-Generated Image Platforms

## Prerequisites

- Python 3.11+
- `pip`
- Git

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    cd projects/PROJ-513-the-impact-of-social-comparison-on-self-
    ```

2.  **Create a virtual environment** and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `statsmodels`, `pandas`, `numpy`, `scipy`, `pytest`.*

3.  **Verify Data Integrity**:
    Ensure the `data/stimuli/` directory contains the pre-generated images and `metadata.json`.
    ```bash
    python code/data_validation.py --check-stimuli
    ```
    This script validates the content hashes and metadata matching (FR-008). **If this fails, the script exits with a non-zero code, blocking further execution.**

## Running the Analysis Pipeline

The pipeline is designed to run on a CPU-only environment (GitHub Actions or local).

1.  **Prepare Data**:
    Ensure raw response data is present in `data/raw/`. If testing locally without real data, run the simulator:
    ```bash
    python code/simulate_participant.py --n-participants 150 --output data/raw/mock_responses/
    ```

2.  **Execute Analysis**:
    Run the main analysis script which performs validation, model fitting, outlier detection, and correction.
    ```bash
    python code/analysis.py
    ```
    *Note: This script includes a check for the Blind Pre-Test (FR-009). If the pre-test has not passed, it will exit with an error.*

3.  **Review Output**:
    The script generates:
    - `data/processed/analysis_dataset.csv`: The cleaned data used for modeling.
    - `data/analysis_results.json`: JSON object containing `f_stat`, `p_value`, `eta_squared`, `n`, `corrected_p_values`, and `sensitivity_analysis`.

## Testing

Run the test suite to ensure contract compliance:

```bash
pytest tests/ -v
```

- **Unit Tests**: Verify LME model output structure and data validation logic.
- **Integration Tests**: Verify the end-to-end flow from raw data to JSON results within memory limits.
- **Gate Tests**: Verify that the pipeline blocks execution if FR-008 or FR-009 validation fails.

## Troubleshooting

- **Memory Error**: Ensure the dataset is not loaded entirely into memory if N is extremely large (though N=150 is safe). The script uses chunked processing if needed.
- **Stimulus Mismatch**: If `data_validation.py` fails, check `data/stimuli/metadata.json` against the actual files in `data/stimuli/`.
- **Missing Dependencies**: Re-run `pip install -r code/requirements.txt` to ensure `statsmodels` is installed.
- **Pre-Test Failure**: If the pipeline blocks due to FR-009, check `data/pretest/results.json` for the p-value. The study must be redesigned if the images are distinguishable in quality.

## Next Steps

- **Data Collection**: Deploy the data collection interface (outside this repo) to gather real participant data.
- **Power Analysis**: If N < 150, re-run `code/analysis.py` with a sensitivity analysis flag to report power limitations.
- **Paper Generation**: Use `data/analysis_results.json` to populate the results section of the manuscript.