# Quickstart: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

## Prerequisites

-   Python 3.11+
-   Git
-   Access to GitHub Actions (for CI) or a local environment with sufficient RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-800-assessing-parcellation-sensitivity-of-hu
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Pre-commit Hooks** (optional but recommended):
    ```bash
    pre-commit install
    ```

## Running the Pipeline

### 1. Download & Process (Single Subject Test)
To test the pipeline on a single subject (e.g., `sub-01`):
```bash
python code/main.py --subject sub-01 --atlas AAL-90,Schaefer-200,Schaefer-400 --mode test
```
*Note: This will download only the required data for `sub-01` and process it.*

### 2. Full Run (N=50 or N=100)
To run the full analysis (adjust N in config or env var):
```bash
export SUBJECT_COUNT=50
python code/main.py --mode full
```

### 3. Generate Results
The pipeline automatically generates:
-   Adjacency matrices in `data/processed/`
-   Centrality scores and hub sets in `data/processed/`
-   Overlap statistics and plots in `data/results/`

### 4. Validation
Run the validation script to ensure data integrity:
```bash
python code/utils/checksums.py --verify
```

## Troubleshooting

-   **Memory Error**: Ensure you are using the `streaming=True` mode. If running locally, reduce `SUBJECT_COUNT`.
-   **Dataset Not Found**: Check `research.md` for the verified dataset URL. Ensure internet connection.
-   **Permission Denied**: Check file permissions in `data/` directory.

## Output Files

-   `data/results/overlap_stats.json`: Main statistical results.
-   `data/results/heatmap_centrality.png`: Correlation heatmap.
-   `data/results/venn_diagram_hubs.png`: Hub overlap visualization.
-   `data/results/validation_report.json`: Integrity report.