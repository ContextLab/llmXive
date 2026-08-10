# Quickstart: Statistical Discrepancies in Publicly Available Election Data

## Prerequisites

-   Python 3.11+
-   `pip` or `poetry`
-   Access to GitHub Actions runner (for CI) or local environment with 7 GB+ RAM.

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Install dependencies**:
    ```bash
    pip install -r projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/requirements.txt
    ```
3.  **Verify environment**:
    ```bash
    python -c "import pandas, scipy, datasets; print('Environment OK')"
    ```

## Running the Pipeline

The pipeline is executed via the `main.py` script.

### 1. Data Ingestion & Validation
```bash
python projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/main.py --step ingestion
```
-   Downloads data from verified Hugging Face sources.
-   Validates schema (precinct/county variables).
-   **Fallback**: If no verified US election data is found, the pipeline automatically generates **synthetic data** with known ground truth to validate the methodology.
-   **Note**: If verified sources are absent, the pipeline proceeds with synthetic data and logs a warning.

### 2. Discrepancy Calculation
```bash
python projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/main.py --step discrepancy
```
-   Aggregates precincts to county level.
-   Calculates absolute and relative discrepancies.
-   Handles missing data and zero-denominator edge cases.
-   Validates temporal alignment of election years.

### 3. Statistical Analysis
```bash
python projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/main.py --step analysis --iterations 10000
```
-   Runs Negative Binomial (theoretical prior) and Permutation (intra-county noise) null models.
-   Performs Anderson-Darling and KS tests.
-   Calculates individual jurisdiction p-values for anomaly detection.
- Generates sensitivity analysis report with thresholds `{0.01%, 0.05%, 0.1%, [deferred]}`.

### 4. Visualization
```bash
python projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/main.py --step viz
```
-   Generates histograms, Q-Q plots, and anomaly lists.
-   Saves outputs to `data/processed/figures/`.

### 5. Reproducibility Verification
```bash
python projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/main.py --step verify
```
-   Re-runs the entire pipeline on a fresh virtual environment to ensure end-to-end reproducibility.

## Testing

Run the full test suite:
```bash
pytest projects/PROJ-064-statistical-discrepancies-in-publicly-av/tests/
```

## Troubleshooting

-   **Memory Error**: If the simulation exceeds 7 GB RAM, the `analysis` step automatically switches to chunked processing.
-   **Data Missing**: If verified sources do not contain US election data, the pipeline halts the primary path and switches to the **Synthetic Data Fallback** automatically.
-   **Collinearity**: If regression is performed and VIF > 5, the report will flag the collinearity and describe relationships descriptively.