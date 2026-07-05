# Quickstart: Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

## Prerequisites

-   Python 3.11+
-   Git
-   Docker (optional, for containerized execution)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <project-dir>
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
    *Dependencies include: `scikit-learn`, `pandas`, `numpy`, `pyyaml`, `pytest`.*

## Running the Pipeline

### Option 1: Local Execution (Recommended for Development)

1.  **Generate Synthetic Data** (if real data is missing):
    ```bash
    python code/data/synthetic.py --output data/raw/synthetic_data.csv --samples 250
    ```
    *This creates a dataset with a representative set of samples across 3 alloy families.*

2.  **Run the Full Pipeline**:
    ```bash
    python code/main.py --data data/raw/synthetic_data.csv --output data/processed/ --model-output code/models/
    ```
    *This will:*
    *   Ingest and preprocess data.
    *   Train the RandomForest model.
    *   Generate `predictions.csv`.
    *   Output `evaluation_report.json` and `importance_plot.png`.

3.  **View Results**:
    -   Check `data/processed/predictions.csv` for predicted texture coefficients.
    -   Check `code/models/evaluation_report.json` for performance metrics.
    -   Check `code/models/importance_plot.png` for feature importance visualization.

### Option 2: Docker (Reproducibility)

1.  **Build the Docker image**:
    ```bash
    docker build -t texture-pipeline:latest .
    ```

2.  **Run the container**:
    ```bash
    docker run --rm -v $(pwd)/data:/app/data -v $(pwd)/code:/app/code texture-pipeline:latest python code/main.py
    ```

### Option 3: GitHub Actions (CI)

Push to the `001-uncovering-correlations` branch to trigger the workflow:
```yaml
# .github/workflows/pipeline.yml
name: Run Texture Pipeline
on: [push]
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Pipeline
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install -r code/requirements.txt
          python code/main.py
```

## Troubleshooting

-   **Missing Data**: If the pipeline aborts with "Data quality insufficient", ensure you have generated synthetic data or provided a valid real dataset with ≥50 samples per alloy.
-   **Memory Error**: Reduce the number of samples in the synthetic generator or limit the `max_depth` of the RandomForest.
-   **Import Error**: Ensure `pymtex` is installed correctly. If it fails, the pipeline will fall back to synthetic ground truth values.
