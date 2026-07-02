# Quickstart: Predicting Molecular Conductivity from Graph-Based Features

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a GitHub Actions runner (or local environment with 7GB+ RAM).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-528-predicting-molecular-conductivity-from-g
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

1.  **Download Data**:
    The `data_loader.py` script will fetch verified datasets from HuggingFace.
    ```bash
    python code/data_loader.py --download
    ```

2.  **Compute Descriptors**:
    ```bash
    python code/descriptors.py --input data/raw/combined_smiles.csv --output data/processed/descriptors.csv
    ```

3.  **Train Models**:
    ```bash
    python code/model_training.py --data data/processed/descriptors.csv --output data/processed/model_results.json
    ```

4.  **Generate Analysis and Plots**:
    ```bash
    python code/analysis.py --results data/processed/model_results.json --plots data/processed/correlation_plots/
    ```

## Verification

Run the test suite to ensure correctness:
```bash
pytest tests/
```

Expected output:
-   `test_descriptors.py`: All descriptor values match reference SMILES.
-   `test_scaffold_split.py`: Train and test sets have no overlapping Murcko scaffolds.
-   `test_analysis.py`: VIF, FDR, and sensitivity analysis calculations are correct.

## Troubleshooting

-   **Memory Error**: If the dataset is too large, the `data_loader.py` script automatically samples to 5000 rows.
-   **Missing Target**: If no conductivity or HOMO-LUMO gap column is found, the script will halt with an error "No valid target variable found."
-   **SMILES Errors**: Invalid SMILES strings are logged to `data/logs/errors.log` and excluded.
-   **Weak Correlation**: If topological descriptors show weak correlation with the target, a warning will be logged indicating the proxy hypothesis may be unsupported.