# Quickstart: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for NNDC ENSDF and PDG retrieval).

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` includes `requests`, `pandas`, `numpy`, `scipy`, `pytest`.*

## Data Retrieval

The system fetches data from the NNDC ENSDF database.

1.  **Run the fetch script**:
    ```bash
    python code/data/fetch_ensdf.py --nuclei 6He,19Ne
    ```
    - This will download raw data to `data/raw/`.
    - **Edge Case**: If NNDC is down, the script retries with exponential backoff (max 3 times).

2.  **Validate Data**:
    ```bash
    python code/data/validate_data.py
    ```
    - Checks if raw/semi-raw data exists.
    - Flags nuclei as "fusion impossible" if only aggregates are found.

## Analysis

1.  **Run the fusion and permutation analysis**:
    ```bash
    python code/analysis/fusion.py --shuffles 10000 --seed 42
    ```
    - Computes cross-modal covariance.
    - Runs 10,000 permutation shuffles.
    - Outputs `data/processed/fusion_results.json`.

2.  **Benchmark against PDG**:
    ```bash
    python code/validation/benchmark.py
    ```
    - Compares derived bounds with 2024 PDG limits.
    - Generates a summary table.

## Verification

1.  **Run tests**:
    ```bash
    pytest tests/ -v
    ```
    - Verifies statistical stability (p-value variance < 0.01 when doubling shuffles).
    - Checks data parsing logic.

2.  **Check reproducibility**:
    - Re-run `fetch_ensdf.py` and `fusion.py`.
    - Verify checksums in `state/` match.

## Troubleshooting

- **NNDC 404 Error**: The script logs the failure and proceeds with available nuclei.
- **Floating Point Precision**: p-values are clamped to $[10^{-10}, 1-10^{-10}]$ to avoid exact 0/1.
- **Insufficient Data**: If a nucleus has only one measurement, the permutation test is skipped, and the single measurement's uncertainty is reported.
