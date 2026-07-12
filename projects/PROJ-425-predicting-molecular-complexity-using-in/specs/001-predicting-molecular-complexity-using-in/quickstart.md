# Quickstart: Predicting Molecular Complexity Using Information Theory

## Prerequisites

- Python 3.11 or higher
- `pip`
- (Optional) `conda` for environment management

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-425-predicting-molecular-complexity-using-in
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: Ensure `rdkit` is installed. If using conda, `conda install -c conda-forge rdkit` is recommended.*

## Running the Analysis

The full pipeline can be executed via the main script:

```bash
python code/main.py
```

This script performs the following steps in order:
1.  **Download**: Fetches the dataset from the verified HuggingFace URL (`sagawa/pubchem-10m-canonicalized`) and verifies the SHA-256 checksum.
2.  **Sample**: Selects a random subset of molecules (e.g., [deferred]–[deferred]) to ensure representativeness.
3.  **Compute**: Calculates Shannon Entropy, LZMA Length (using `lzma`), SA, QED, MW, and Atom Count for each molecule.
4.  **Analyze**: Performs Pearson and Spearman correlation, partial correlation (controlling for MW/Atom Count), bootstrap resampling (1,000 iterations), and multiple-comparison correction.
5.  **Visualize**: Generates scatter plots.
6.  **Report**: Outputs a JSON summary and an HTML report.

### Output Files

After completion, check the `data/processed/` and `reports/` directories:
- `data/processed/metrics.csv`: Computed metrics for all molecules.
- `data/processed/correlations.csv`: Final correlation statistics (including partial correlations).
- `reports/analysis_report.html`: Human-readable report with plots.

## Verification

To verify the installation and basic functionality:

```bash
python -m pytest tests/unit/
```

This runs unit tests for metric calculation and error handling.

## Troubleshooting

- **RDKit Import Error**: Ensure `rdkit` is installed correctly. Try `pip install rdkit-pypi` or use `conda`.
- **Memory Error**: Reduce the sample size in `code/config.py` (e.g., `SAMPLE_SIZE = 500`).
- **Dataset Download Failed**: Check internet connection and ensure the HuggingFace URL is accessible. The script includes retry logic.
- **Checksum Mismatch**: If the downloaded file checksum does not match the HuggingFace manifest, the script will abort to ensure data integrity.