# Quickstart Guide: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

This guide provides instructions for setting up the environment and running the analysis pipeline.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Access to the public MDSplus archive for DIII-D data

## Environment Setup

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: This project does NOT require the `mdsplus` Python library as a direct dependency for the pipeline logic, as data retrieval is handled via specific client logic defined in `code/data/retrieval.py`.*

4. **Verify installation**:
 Ensure `numpy`, `pandas`, `scipy`, `matplotlib`, and `pytest` are installed:
 ```bash
 python -c "import numpy; import pandas; import scipy; import matplotlib; print('Dependencies OK')"
 ```

## Execution Commands

The main entry point for the analysis pipeline is `code/main.py`.

### Running the Full Pipeline

To run the analysis on a specific set of DIII-D discharges:

```bash
python code/main.py --discharges 123456,123457,123458,123459,123460
```

**Arguments**:
- `--discharges` (required): Comma-separated list of DIII-D discharge IDs (e.g., `123456,123457`).
- `--output-dir` (optional): Path to the output directory (default: `outputs/`).
- `--verbose` (optional): Enable verbose logging.

**Example**:
```bash
python code/main.py --discharges 123456,123457,123458
```

### Expected Outputs

Upon successful completion, the pipeline generates the following artifacts:

- **`data/processed/unified_analysis.csv`**: The unified dataset containing all parsed discharge data.
- **`data/processed/metrics.csv`**: Calculated topological metrics (island width, resonant surface density).
- **`outputs/summary_report.json`**: Final statistical analysis report including correlation coefficients, p-values, and hypothesis status.
- **`outputs/topology_vs_confinement.png`**: Diagnostic scatter plot visualizing the relationship between island width and energy confinement time.
- **`outputs/checksum.txt`**: Checksum for the unified dataset to ensure data integrity.

### Running Tests

To run the test suite:

```bash
pytest tests/ -v
```

To run a specific test file:

```bash
pytest tests/unit/test_metrics.py -v
```

## Configuration

Key configuration parameters are defined in `code/config.py`:

- `PER_OPERATION_TIMEOUT`: Timeout threshold for individual operations (default: 300 seconds).
- `MULTICOLLINEARITY_THRESHOLD`: Threshold for detecting multicollinearity (default: 0.95).
- `MIN_DISCHARGES`: Minimum number of valid discharges required to proceed (default: 5).

## Troubleshooting

- **MDSplus Connection Failures**: If the pipeline fails to connect to the MDSplus archive, check your network connection and ensure the public archive is accessible. The pipeline includes retry logic but will fail loudly if data cannot be retrieved.
- **Insufficient Data**: If fewer than 5 valid discharges are found after filtering, the pipeline will terminate with an error.
- **Memory Issues**: The pipeline monitors memory usage. If it exceeds the 7 GB limit, it will abort.

## Data Provenance

All data is retrieved directly from the public DIII-D MDSplus archive. No synthetic or placeholder data is used. If real data cannot be retrieved, the pipeline fails to ensure scientific integrity.