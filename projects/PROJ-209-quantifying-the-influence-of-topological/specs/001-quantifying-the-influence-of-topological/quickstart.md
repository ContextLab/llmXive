# Quickstart: Quantifying the Influence of Topological Defects on 2D Material Properties

## Prerequisites

-   Python 3.11+
-   Git
-   API Key for Materials Project (set as `MP_API_KEY` environment variable)
-   (Optional) `data/raw/defect_dataset_2022.csv` if you have a local copy.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-209-quantifying-the-influence-of-topological
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

## Running the Pipeline

The pipeline can be run end-to-end via the orchestration script.

### 1. Data Acquisition
This step downloads pristine structures and attempts to load/generate defect data.
```bash
python code/01_data_acquisition.py
```
*   **Output**: `data/raw/pristine_structures.csv`, `data/raw/defect_dataset_2022.csv` (or `synthetic_train.csv` if real data missing), `data/state/cache_load_log.json`.

### 2. Feature Engineering
Normalizes data and encodes features.
```bash
python code/02_feature_engineering.py
```
*   **Output**: `data/processed/feature_matrix.csv`, `data/processed/target_matrix.csv`, `data/state/exclusion_log.json`.

### 3. Modeling & Inference
Trains models, performs CV, and runs permutation tests.
```bash
python code/03_modeling.py
```
*   **Output**: `data/state/model_results.json`, `data/state/permutation_pvalues.json`.

### 4. Analysis & Reporting
Generates sensitivity analysis and the final validation report.
```bash
python code/04_analysis.py
```
*   **Output**: `data/state/Validation_Report.json`, `data/state/sensitivity_analysis.csv`.

### 5. Full Pipeline (One Command)
```bash
python code/run_pipeline.py
```

## Testing

Run the unit tests to verify the pipeline logic:
```bash
pytest tests/unit/
```

Run the contract tests to verify data schemas:
```bash
pytest tests/contract/
```

## Troubleshooting

-   **API Failure**: If the Materials Project API fails, check `data/state/cache_load_log.json`. If no cache exists, the pipeline will halt with `[ERROR: API access unavailable and no cache present]`.
-   **Missing Defect Data**: If `defect_dataset_2022.csv` is missing, the pipeline will generate `synthetic_train.csv` and flag it as `TESTING_ONLY`. **Scientific analysis will halt.**
-   **Memory Error**: The pipeline is optimized for standard RAM configurations. If you encounter OOM, reduce the `N_PERMUTATIONS` in `code/03_modeling.py` (default a substantial number).