# Quickstart: Predicting Plant VOC Emission Profiles

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-339-predicting-plant-volatile-organic-compou
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

The pipeline is orchestrated via `code/main.py`.

1.  **Execute the full pipeline**:
    ```bash
    python code/main.py
    ```
    This will:
    - Generate/Load the dataset (mock data if no real data is found).
    - Preprocess (normalize, impute, merge).
    - Train the Random Forest model.
    - Perform SHAP analysis.
    - Generate reports.

2.  **Run specific steps** (optional):
    ```bash
    python code/01_ingest.py
    python code/03_train.py
    ```

## Output

- **Reports**: `data/reports/model_metrics.json`, `data/reports/feature_importance.csv`, `data/reports/biological_overlap.txt`.
- **Visualizations**: `data/plots/shap_summary.png`, `data/plots/feature_importance_bar.png`.
- **Logs**: `logs/pipeline.log`.

## Troubleshooting

- **Error: "No paired samples found"**: The dataset lacks matching RNA-seq and VOC metadata. Check the mock data generator or the real data source.
- **Error: "Insufficient samples (<50)"**: The dataset is too small for cross-validation. The pipeline will emit a warning and skip modeling.
- **Error: "Missing environmental metadata"**: Samples with missing temperature/light/CO2 are excluded. Ensure the dataset has these columns.

## Data Note

This pipeline currently uses **synthetic/mock data** because no verified *Arabidopsis thaliana* RNA-seq/VOC dataset is available in the project's verified sources list. The results are for pipeline validation only.
