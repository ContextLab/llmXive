# Quickstart: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

## Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for DIII-D archive retrieval)
- (Optional) `wget` (if not using Python `requests`)

## Installation

1.  **Clone the repository** (if not already done).
2.  **Navigate to the project directory**:
    ```bash
    cd projects/PROJ-332-quantifying-the-impact-of-magnetic-field
    ```
3.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
4.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### 1. Data Retrieval & Processing

Run the main pipeline script. This will:
- Fetch 10 discharges from the DIII-D public archive.
- Calculate topological metrics.
- Perform statistical analysis.
- Generate plots and reports.

```bash
python code/main.py
```

**Note**: If the DIII-D archive is unreachable, the script will retry 3 times and then fail with an error code. Do not proceed if data retrieval fails.

### 2. Verifying Results

Check the output files:
- **Scatter Plot**: `outputs/topology_vs_confinement.png`
- **Summary Report**: `outputs/summary_report.json`
- **Processed Data**: `data/processed/discharge_metrics.csv`

### 3. Running Tests

Run the unit and integration tests to verify the logic:

```bash
pytest tests/ -v
```

### 4. CI Execution (GitHub Actions)

The pipeline is configured to run on the GitHub Actions free-tier runner.
- **Trigger**: Push to `001-quantify-topology-confinement` branch.
- **Constraints**: 2 CPU, 7GB RAM, 6-hour limit.
- **Outcome**: If the DIII-D archive is accessible, the job will complete and upload artifacts. If not, it will fail with a clear error message.

## Troubleshooting

- **Error: "Too few valid discharges"**: The archive returned fewer than 5 valid shots. Check the logs for specific exclusion reasons (missing island width, missing tau_e).
- **Error: "Connection Timeout"**: The DIII-D MDSplus server is unreachable. Verify network connectivity. The script retries automatically.
- **Error: "Stratification skipped"**: This is a warning, not a failure. It means there were not enough L-mode or H-mode shots to split the data. The global correlation is still reported.
