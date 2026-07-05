# Quickstart: Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

## 1. Prerequisites

*   Python 3.11+
*   Git
*   Access to Metabolomics Workbench (public)
*   GitHub Actions Runner (or local environment with 7GB+ RAM)

## 2. Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-144-predicting-plant-disease-resistance-from
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

## 3. Data Acquisition

The system is designed to fetch data from Metabolomics Workbench.

1.  **Configure Study IDs**: Edit `code/utils/constants.py` to include the target Metabolomics Workbench Study IDs (e.g., `["C-12345", "C-67890"]`).
    *   *Note*: Ensure these IDs correspond to studies with pre-challenge metabolite data and resistance labels.
2.  **Run the download script**:
    ```bash
    python code/data/download.py
    ```
    *   This will download raw intensity and phenotype files to `data/raw/`.
    *   Checksums are automatically generated and logged.

## 4. Preprocessing & Model Training

Run the full pipeline:

```bash
python code/main.py
```

This executes:
1.  **Preprocessing**: Normalization, missing value filtering, InChIKey alignment, ComBat batch correction.
2.  **Label Harmonization**: Z-scoring/stratification.
3.  **Training**: Random Forest with Stratified 5-Fold CV and GridSearch.
4.  **Evaluation**: Permutation testing, VIF diagnostics, sensitivity analysis.
5.  **Interpretation**: Pathway mapping (KEGG/MetaCyc).

## 5. Expected Outputs

*   `data/processed/batch_corrected_matrix.csv`: Final feature matrix.
*   `code/models/final_model.pkl`: Trained Random Forest.
*   `results/metrics.json`: Balanced accuracy, AUC, p-values from permutation test.
*   `results/interpretation_report.md`: Top metabolites and pathway mappings.
*   `plots/`: ROC curves, learning curves, VIF plots.

## 6. Verification

To verify the pipeline on your local machine:

```bash
pytest tests/
```

Ensure all tests pass, particularly `test_data_hygiene` (checksums) and `test_model_validation` (no data leakage).

## 7. Troubleshooting

*   **"No datasets found"**: Verify Study IDs in `constants.py`. Check Metabolomics Workbench for public access.
*   **"Memory Error"**: Reduce `n_estimators` in `constants.py` or filter metabolites more aggressively (>40% missing).
*   **"ComBat Convergence"**: If batch correction fails, the script falls back to study-level z-scoring and logs a warning.
