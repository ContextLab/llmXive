# Quickstart: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Prerequisites

- Python 3.11+
- Git
- Access to a Zenodo account (if required by the specific dataset) or internet access for public datasets.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/your-repo.git
    cd projects/PROJ-177-investigating-the-validity-of-the-equipa
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `zenodo_get` is listed as an optional dependency. It is only required if running with the real Zenodo dataset. Synthetic tests do not require it.*

## Data Preparation

1.  **Download Data**:
    The project uses the verified Zenodo dataset `10.5281/zenodo.1456789`.
    ```bash
    python -m code.data_ingestion --download --zenodo-id 10.5281/zenodo.1456789
    ```
    *Note: If no open dataset is found (fallback), the script will generate a synthetic dataset for testing only.*

2.  **Verify Checksums**:
    Ensure `data/raw/checksums.txt` is updated after download.

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python -m code.main
```

This will:
1.  Ingest and synchronize data.
2.  Calculate energy components ($E_{trans}, E_{rot}, E_{pot}, E_{vib}$).
3.  Perform KS and Chi-squared tests per frequency bin.
4.  Apply Permutation-based FDR correction.
5.  Run regression analysis on deviation metrics.
6.  Generate `data/derived/statistical_results.json` and plots.

## Verifying Results

1.  **Check Energy Calculations**:
    Compare `data/derived/energy_samples.csv` against manual calculations on a small synthetic subset (see `tests/unit/test_energy_calc.py`).

2.  **Verify Statistical Tests**:
    Inspect `data/derived/statistical_results.json` for p-values and significance flags.

3.  **Reproducibility Check**:
    Re-run the pipeline with a fixed seed:
    ```bash
    python -m code.main --seed 42
    ```
    Ensure outputs are identical.

## Troubleshooting

- **Missing Data**: If `NaN` values appear, check `data/derived/exclusion_log.csv` for reasons (e.g., "non-stationary signal").
- **Memory Error**: If processing large datasets, ensure `streaming=True` is enabled in `config.yaml` or reduce the sample size.
- **Dependency Errors**: Ensure `requirements.txt` is up to date and run `pip install -r requirements.txt` again.
