# Quickstart: Predicting Molecular Conductivity from Graph-Based Features

## Prerequisites

-   Python 3.11+
-   Git
-   Access to GitHub Actions (for CI) or a local Linux environment with 7 GB+ RAM.

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-528-predicting-molecular-conductivity-from-g
    ```

2.  **Create a virtual environment** and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

## Data Preparation

### Option A: Use Your Own Data (Recommended)
Create a CSV file named `input.csv` with at least two columns: `smiles` and `conductivity`.
```csv
smiles,conductivity
c1ccccc1,1.5e-4
CCO,2.3e-5
...
```
Place this file in `data/raw/input.csv`.

### Option B: Download Default Dataset
If no input is provided, the pipeline attempts to load from Hugging Face.
```bash
# The pipeline will automatically attempt to load from verified URLs if data/raw/input.csv is missing.
```

## Running the Pipeline

Execute the main orchestration script:
```bash
python code/main.py
```

This will:
1.  Load and validate data.
2.  Compute graph descriptors.
3.  Perform VIF filtering and scaffold splitting.
4.  Train Random Forest and Gradient Boosting models.
5.  Run sensitivity analysis and FDR correction.
6.  Generate plots and reports.

## Expected Outputs

-   `data/processed/descriptors.csv`: Computed features.
-   `data/processed/metrics.json`: R², MAE, CV scores.
-   `data/processed/plots/`: Feature importance and correlation plots.
-   `data/processed/reports/sensitivity_analysis.json`: R² variance across outlier thresholds.

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests:
```bash
pytest tests/integration/
```
