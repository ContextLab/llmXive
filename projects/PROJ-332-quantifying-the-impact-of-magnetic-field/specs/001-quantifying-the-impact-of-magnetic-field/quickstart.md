# Quickstart: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

## Prerequisites

*   Python 3.11+
*   `pip`
*   `wget` (system utility)
*   Access to the DIII-D public MDSplus archive.

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    cd projects/PROJ-332-quantifying-the-impact-of-magnetic-field
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
    *Dependencies*: `numpy`, `pandas`, `scipy`, `matplotlib`, `requests`, `pyyaml`.

## Running the Pipeline

### Option A: Full CI Run (Recommended for Reproducibility)

Run the pipeline as it would run in GitHub Actions (with limits):

```bash
python code/main.py
```

*   **Input**: Fetches data from DIII-D MDSplus. If unreachable, the pipeline will fail with an error message and exit.
*   **Output**: `data/processed/unified_analysis.csv`, `data/processed/topology_vs_confinement.png`, `data/processed/summary_report.md`.
*   **Limits**: Enforced 6h runtime / 7GB RAM via `code/utils/limits.py`.

### Option B: Manual Step-by-Step

1.  **Retrieve Data**:
    ```bash
    python code/data/retrieval.py --shots 123456,123457,123458
    ```
    *Downloads raw files to `data/raw/`.*

2.  **Parse & Calculate**:
    ```bash
    python code/data/parsing.py
    python code/data/topology.py
    ```
    *Generates `data/processed/unified_analysis.csv`.*

3.  **Analyze**:
    ```bash
    python code/analysis/correlation.py
    ```
    *Generates `data/processed/correlation_results.json` and the plot.*

4.  **Report**:
    ```bash
    python code/reports/summary.py
    ```
    *Generates `data/processed/summary_report.md`.*

## Testing

Run the unit tests to verify logic:

```bash
pytest tests/unit/ -v
```

Run the integration test to verify the full flow (may fail if DIII-D is unreachable):

```bash
pytest tests/integration/ -v
```

## Troubleshooting

*   **"MDSplus unreachable"**: The pipeline will log a warning and terminate execution. No fallback data source will be used.
*   **"Memory Limit Exceeded"**: Verify `code/utils/limits.py` is imported in `main.py`. Check for large unnecessary arrays.
*   **"Missing island width"**: Discharges without this data are excluded from the analysis and logged in `data/processed/exclusions.log`.
