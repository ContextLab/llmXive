# Quickstart: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

## Prerequisites

-   Python 3.11+
-   Git
-   Access to GitHub Actions (for CI) or a local environment with ~7GB RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-204-quantifying-the-impact-of-spatial-correl
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
    *Note: `requirements.txt` pins versions for CPU-only compatibility.*

## Data Setup

1.  **Download Raw Data**:
    Run the ingestion script to fetch verified JSONs and attempt EDS downloads.
    ```bash
    python code/data/download.py
    ```
    *This script reads the verified URLs from the spec and populates `data/raw/`.*

2.  **Verify Data**:
    Check that `data/raw/` contains the JSON files and any available EDS maps.
    ```bash
    ls -lh data/raw/
    ```
    *If EDS maps are missing, the pipeline will halt with a "Data Availability Report".*

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main_pipeline.py
```

This script performs the following steps in order:
1.  **Data Feasibility Check**: Verify EDS link programmatic access.
2.  **Align & Mask**: Preprocesses EDS maps (FR-001).
3.  **Co-location Validation**: Checks ID matching (FR-007).
4.  **Depth Resolution Validation**: Checks EDS vs PCE depth (FR-008).
5.  **Extract Metrics**: Computes autocorrelation and spectral power (FR-002, FR-003).
6.  **Model**: Runs correlations, BH correction, and GAMs (FR-004).
7.  **Robustness**: Performs LOO-CV (FR-005).
8.  **Sensitivity Analysis**: Performs conditional exclusion (FR-008).
9.  **Report**: Generates `results/summary_report.csv`, `results/summary_report.pdf`, and `results/ingestion_metrics.json` (SC-004).

## Testing

Run the unit tests to verify metric extraction accuracy (SC-001):

```bash
pytest tests/unit/test_spatial_metrics.py -v
```

Run integration tests:

```bash
pytest tests/integration/test_pipeline.py -v
```

## Output

-   **Processed Data**: `data/processed/` (Aligned maps, derived metrics).
-   **Results**: `results/summary_report.csv` (Correlation coefficients, p-values, robustness metrics).
-   **Ingestion Metrics**: `results/ingestion_metrics.json` (Global ingestion success rate as per SC-004).
-   **Logs**: `logs/` (Detailed logs of masking, fitting, and exclusions).