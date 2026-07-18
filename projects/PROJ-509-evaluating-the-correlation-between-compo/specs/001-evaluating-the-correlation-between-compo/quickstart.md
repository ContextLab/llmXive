# Quickstart: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

## Prerequisites

*   Python 3.11 or higher
*   pip package manager
*   7 GB+ available RAM
*   14 GB+ available disk space

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd projects/PROJ-509-evaluating-the-correlation-between-compo
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

## Data Preparation

The pipeline expects the Materials Project MP-2020.12.1 dataset to be downloaded automatically. If the download fails, manually place the dataset in `data/raw/mp_2020_12_1.csv`.

1.  **Run the ingestion script**:
    ```bash
    python code/ingestion.py
    ```
    This will:
    *   Download the dataset (Zenodo or Matminer fallback).
    *   Filter for inorganic compounds.
    *   Compute compositional descriptors.
    *   Cap outliers conditionally (>1% threshold).
    *   Save `data/processed/computed_descriptors.csv`.

## Model Training

1.  **Train the models**:
    ```bash
    python code/train.py
    ```
    This will:
    *   Split the data (80/20 by Chemical Family).
    *   Train Random Forest and Gradient Boosting models.
    *   Save `data/evaluation/trained_models.pkl` and `data/evaluation/metrics.json`.

## Analysis & Evaluation

1.  **Run the importance analysis**:
    ```bash
    python code/importance.py
    ```
    This will:
    *   Calculate feature importances.
    *   Perform permutation importance validation (Pearson correlation).
    *   Generate Accumulated Local Effects (ALE) plots (saved to `data/evaluation/ale_plots/`).
    *   Compute VIF scores.
    *   Save `data/evaluation/permutation_importance.json`, `data/evaluation/feature_ranking.json`, and `data/evaluation/vif_scores.json`.

## Running the Full Pipeline

To run the entire pipeline end-to-end:

```bash
python code/ingestion.py && python code/train.py && python code/importance.py
```

## Verification

*   Check `data/evaluation/metrics.json` for R², MAE, and RMSE.
*   Verify `data/evaluation/feature_ranking.json` contains the top 5 features and correlation `r`.
*   Inspect `data/evaluation/ale_plots/*.png` for non-linear trends.
*   Check `data/evaluation/timing.json` for total execution time.

## Troubleshooting

*   **Memory Error**: If you encounter OOM errors, reduce the dataset size by enabling the sampling flag in `code/config.py` (though a substantial number of rows should fit).
*   **Download Failed**: Ensure the Zenodo mirror is accessible. If not, the script will fallback to Matminer.
*   **Missing Artifacts**: Ensure all scripts are run in the correct order (Ingestion -> Training -> Analysis).
