# Quickstart: Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys

## Prerequisites

- Python 3.11+
- `pip` (or `conda`)
- Access to the verified dataset URL (if available) or `ase` for synthetic generation

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-538-quantifying-the-impact-of-network-struct
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Data Setup

**IMPORTANT**: The pipeline requires a dataset with atomic coordinates and thermal conductivity.
No verified real-world dataset exists for this specific query. The pipeline will default to **Synthetic Validation Mode**.

1.  **Run the pipeline**:
    ```bash
    python code/main.py
    ```
    - If real data is found (unlikely), it will attempt to use it.
    - If real data is missing, it will automatically generate a set of synthetic snapshots using Lennard-Jones potentials and proceed with methodological validation.

2.  **Verify Data**:
    Run `python code/ingest.py --check`.
    - If coordinates are missing in real data, you will see: `Error: Missing required columns [x, y, z, species]. Data availability failure. Switching to Synthetic Mode.`

## Running the Pipeline

1.  **Execute the full analysis**:
    ```bash
    python code/main.py
    ```
    This will:
    - Audit data sources.
    - Generate synthetic data if real data is missing.
    - Construct graphs.
    - Extract metrics.
    - Run correlations.
    - Perform sensitivity analysis.
    - Generate plots in `data/processed/`.

2.  **View Results**:
    - Check `data/processed/correlation_results.csv` for statistical tables.
    - Check `data/processed/sensitivity_report.csv` for threshold stability.
    - Check `data/processed/figures/` for scatter plots and heatmaps.
    - Check `data/audit_log.json` for the mode selection (Real vs. Synthetic).

## Troubleshooting

- **Error: "DataAvailabilityError"**: The verified dataset does not contain atomic coordinates. The pipeline switches to Synthetic Mode.
- **Error: "PercolationThreshold undefined"**: The graph is too sparse or disconnected. This is expected for some samples; the metric will be recorded as `NaN`.
- **Error: "Bonferroni Correction failed"**: Ensure `scipy` is installed.

## Verification

To verify the pipeline on a synthetic graph (bypassing data ingestion):
```bash
python tests/unit/test_metrics.py --synthetic
```
This tests the metric extraction logic against a known Erdős-Rényi graph.

## Important Note on Results

- **Real Data Mode**: If no real data is found, results are **N/A**.
- **Synthetic Mode**: Results validate the *methodology* (graph construction, correlation analysis) but do not claim to represent real-world Cu-Ni/Au-Ag physics.
