# Quickstart: Quantify Dataset Sparsity Impact

## Prerequisites

*   Python 3.11+
*   `MaterialsProject` API Key (set as `MP_API_KEY` environment variable)
*   7 GB RAM available (GitHub Actions Free Tier compatible)

## Installation

1.  Clone the repository and navigate to the project directory.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r code/requirements.txt
    ```

## Configuration

1.  Set your API key:
    ```bash
    export MP_API_KEY="your_api_key_here"
    ```
2. (Optional) Edit `code/config/sparsity_levels.json` to adjust the 7 sparsity percentages if needed (default: [deferred], [deferred], [deferred], [deferred], [deferred], [deferred], [deferred]).

## Running the Pipeline

Execute the full pipeline:

```bash
python code/data_ingestion.py
python code/sparsity_generation.py
python code/model_training.py
python code/statistical_analysis.py
```

### Step-by-Step Execution

1.  **Ingest Data**:
    ```bash
    python code/data_ingestion.py
    ```
    *Downloads and filters data. Output: `data/raw/mp_data.csv`.*

2.  **Generate Subsets**:
    ```bash
    python code/sparsity_generation.py
    ```
    *Creates stratified subsets. Output: `data/processed/subset_*.csv`.*

3.  **Train Models**:
    ```bash
    python code/model_training.py
    ```
    *Trains GPR and RF. Output: `models/*.pkl`, `results/metrics.csv`.*

4.  **Analyze Results**:
    ```bash
    python code/statistical_analysis.py
    ```
    *Runs ANOVA and generates plots. Output: `results/plots/`, `results/statistical_summary.json`.*

## Verification

Check the output:
*   Ensure `data/raw/mp_data.csv` has >100,000 rows (or the max available).
*   Ensure `results/plots/learning_curve.png` exists.
*   Ensure `results/statistical_summary.json` contains p-values < 0.05 for at least one comparison.

## Troubleshooting

*   **OOM Error**: Reduce the `max_samples` in `code/config/sparsity_levels.json` or lower `n_estimators` in `model_training.py`.
*   **API Error**: Check `MP_API_KEY` and network connectivity.
*   **Missing Descriptors**: The script will log the count of imputed rows. If >10%, check the `matminer` configuration.
