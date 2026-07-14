# Quickstart: Predicting Molecular Polarity from SMILES Strings with Machine Learning

## Prerequisites

-   Python 3.10+
-   Git
-   6GB+ RAM available
-   Internet connection (for dataset download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-091-predicting-molecular-polarity-from-smile
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

## Data Download

Download the QM9 dataset to `data/raw/`:

```bash
python code/data/download_qm9.py
```

This script:
-   Fetches the dataset from the verified HuggingFace URL.
-   Computes a checksum.
-   Validates the file format.

## Running the Pipeline

Execute the full pipeline (Preprocessing -> Training -> Evaluation -> Interpretation):

```bash
python code/main.py
```

### Step-by-Step Execution

1.  **Preprocessing**:
    ```bash
    python code/data/preprocess_2d.py
    ```
    Generates the 2D descriptor matrix, excluding TPSA and 3D features.

2.  **Feature Clustering**:
    ```bash
    python code/data/feature_clustering.py
    ```
    Computes correlation matrix, groups features into clusters, and calculates VIF for diagnostic reporting (no pruning).

3.  **Training**:
    ```bash
    python code/models/train_lightgbm.py
    ```
    Trains the LightGBM model with 5-fold CV.

4.  **Evaluation & SHAP**:
    ```bash
    python code/models/evaluate.py
    python code/models/interpret.py
    ```
    Generates metrics and Cluster-Aware SHAP stability reports (Two-Stage Bootstrap).

## Verification

Run the test suite to ensure compliance with the spec:

```bash
pytest tests/ -v
```

**Key Tests**:
-   `test_3d_exclusion`: Asserts no 3D conformer generation functions are called.
-   `test_cluster_stability`: Verifies Jaccard similarity of top feature clusters.
-   `test_no_pruning`: Asserts that no features are removed based on VIF or correlation thresholds.

## Expected Outputs

-   `data/processed/features_*.parquet`: Cleaned feature matrix with cluster IDs.
-   `models/lightgbm_*.pkl`: Trained model.
-   `reports/metrics.json`: R², RMSE, MAE.
-   `reports/shap_summary.png`: SHAP summary plot.
-   `reports/stability_report.json`: Cluster Jaccard similarity scores.