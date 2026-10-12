# Quickstart: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

## Prerequisites

- Python 3.11+
- `git`
- (Optional) Kaggle API credentials for GPU offloading (configured in environment).

## Installation

1.  **Clone and Setup**:
    ```bash
    git checkout 001-llmxive-followup
    cd projects/PROJ-1000-llmxive-followup-extending-orbitquant-d
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Initialize Project**:
    Run the initialization script to create the directory skeleton:
    ```bash
    python code/main.py --phase init
    ```

3.  **Download Data**:
    Run the download script to fetch MS-COCO (including captions):
    ```bash
    python code/data/download_coco.py
    ```
    *Note: This will verify checksums and store data in `data/raw/`.*

4.  **Run Analysis Pipeline**:
    Execute the full pipeline (Correlation -> Clustering -> Evaluation):
    ```bash
    python code/main.py --phase validate
    ```
    *Note: The `validate` phase checks the clustering report. Individual analysis scripts should be run according to the tasks.md sequence.*

5.  **View Results**:
    - Correlation plots: `data/processed/correlation_plots/`
    - Clustering Report: `data/processed/clustering_report.json` (Required for Phase 2)
    - Rotation matrices: `data/processed/rotation_matrices/`
    - Final metrics: `data/processed/results.csv`

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests (requires data download):
```bash
pytest tests/integration/
```