# Quickstart: Predicting Battery Electrolyte Decomposition Products via DFT and Machine Learning

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a CPU-only environment (e.g., GitHub Actions, local machine with <7GB RAM)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-085-predicting-battery-electrolyte-decomposi
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

## Running the Pipeline

The pipeline consists of three main stages: Data Curation, Feature Engineering (with Leakage Detection), and Model Training/Validation.

### 1. Data Curation & Contract Validation

This step loads the static, literature-sourced dataset and validates it against the schema.

```bash
python code/data_ingestion.py
```

**Output**: `data/raw/literature_subset.csv` (if not present, manual curation is required) and validation logs. **HALT** if DOI/Checksum verification fails.

### 2. Feature Engineering & Leakage Detection

This step calculates `decomp_energy`, **drops identity features** (`reactant_energy`, `product_energy`), checks for collinearity, and rejects identity features based on partial correlation.

```bash
python code/feature_engineering.py
```

**Output**: `data/derived/features_cleaned.csv` (containing only non-identity features) and `data/derived/rejected_features.json`.

### 3. Model Training

Trains the Random Forest Regressor on the cleaned feature set with 5-fold CV.

```bash
python code/model_training.py
```

**Output**: `data/derived/model_artifact.pkl`, `data/derived/importance.json`.

### 4. Validation & Sensitivity Analysis

Validates against the literature subset (proxy correlation) and performs threshold sweeps.

```bash
python code/validation.py
```

**Output**: `data/derived/validation_report.json`, `data/derived/sensitivity_analysis.csv`.

## Verification

To ensure the pipeline runs within constraints:

1.  **Check Memory**: Monitor RAM usage; it should not exceed a threshold appropriate for the experimental environment.
2.  **Check Runtime**: The full pipeline should complete in < 6 hours.
3.  **Check Leakage**: Verify `data/derived/rejected_features.json` to ensure `reactant_energy` and `product_energy` are not present in the feature set.
4.  **Check Residual**: Verify `data/derived/model_artifact.pkl` metadata to ensure residual correlation < 0.9.

## Troubleshooting

-   **No Viable Features**: If the pipeline halts with "No viable non-identity features found," it means all features were rejected due to mathematical identity with the target. This is a valid scientific result indicating ground-state descriptors are insufficient.
-   **Residual Identity Detected**: If the pipeline halts with "Residual Identity Detected," the remaining features are still mathematically tied to the target. Review the feature selection.
-   **Missing Data**: If the pipeline halts due to missing HOMO/LUMO, check the `data/raw/literature_subset.csv` source.
-   **Data Scarcity**: If the pipeline halts with "Data Scarcity" or "No Intersection Found," the curated dataset lacks the required experimental onset data for the training molecules.
-   **Validation Impossible**: If the pipeline halts with "Validation Impossible," the intersection of training molecules and experimental data is empty.
-   **OOM Error**: Reduce `n_estimators` in `code/model_training.py` or sample the dataset further.
-   **VIF Warnings**: High VIF features are flagged but retained only if partial correlation < 0.9. Review `data/derived/features_cleaned.csv` to ensure they are not used for causal claims.