# Quickstart: Predicting the Yield Strength of BCC Steels from Density Functional Theory

## Prerequisites

- Python 3.11+
- Access to the Materials Project API (API Key required).
- Internet access to fetch experimental data (MatNavi/NIST).

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: `requirements.txt` pins versions compatible with CPU-only execution.*

## Configuration

1. Set your **Materials Project API Key** as an environment variable:
 ```bash
 export MP_API_KEY="your_api_key_here"
 ```
2. Ensure the `data/` directory exists.

## Running the Pipeline

Execute the main pipeline script:

```bash
python code/main.py
```

### What happens during execution?

1. **Data Fetching**:
 - Downloads experimental data from MatNavi ().
 - Queries the Materials Project API for DFT elastic constants.
 - **Stop Condition**: If the merged dataset has fewer than 20 valid rows, the script halts with `ERR_INSUFFICIENT_DATA`.
2. **Data Processing**:
 - Filters for BCC structure (Space Group 229).
 - Merges datasets, encodes composition, and calculates VIF scores.
 - Calculates Pearson correlation between Shear Modulus and Yield Strength.
3. **Modeling**:
 - Trains Random Forest (with DFT) and Baseline (Composition only) using **Nested Cross-Validation**.
 - Performs **Wilcoxon signed-rank test** on the hold-out test set errors.
4. **Analysis**:
 - Calculates R², MAE, and statistical power.
 - Generates TreeSHAP and Permutation Importance plots.
 - Runs **Full-Dataset Bootstrap** Stability analysis.
 - Checks if `std_dev < 0.05` for key features and reports `is_stable`.
5. **Output**:
 - Results saved to `data/results/output.json` (matching `contracts/output.schema.yaml`).
 - Plots saved to `data/results/plots/`.
 - Provenance logs in `data/provenance/`.

## Verifying Results

Check the `data/results/output.json` file for:
- `p_value`: From the Wilcoxon test (should be < 0.05 to reject the null hypothesis).
- `power`: Should be reported (warning if < 0.8).
- `row_count`: Must be >= 20.
- `is_stable`: Boolean indicating if feature importance is stable (< 0.05 std).

## Troubleshooting

- **`ERR_INSUFFICIENT_DATA`**: The public datasets did not yield enough BCC Fe-alloy matches. No synthetic data is generated.
- **API Rate Limit**: The script includes exponential backoff. If it fails after 3 retries, that specific entry is skipped.
- **Memory Error**: Unlikely on this dataset size, but ensure no other heavy processes are running.