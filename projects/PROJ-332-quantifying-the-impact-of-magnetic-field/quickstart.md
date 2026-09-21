# Quickstart Guide: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

This guide provides instructions for setting up the environment and executing the analysis pipeline to study the relationship between magnetic island topology and energy confinement time in DIII-D tokamak discharges.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Git (for cloning the repository)
- Internet connection (to fetch DIII-D data from the public MDSplus archive)

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
 Install the required Python packages listed in `requirements.txt`:
 ```bash
 pip install -r requirements.txt
 ```

 *Note: This project uses `scipy`, `numpy`, `pandas`, `matplotlib`, and `pytest`. It does **not** require the `mdsplus` library as a Python dependency, as data retrieval is handled via HTTP requests to the public MDSplus archive.*

4. **Verify installation**:
 Ensure all dependencies are correctly installed:
 ```bash
 python -c "import scipy, numpy, pandas, matplotlib, pytest; print('All dependencies installed successfully.')"
 ```

## Execution Commands

The pipeline is executed via the `code/main.py` entry point.

### Basic Usage

Run the full pipeline with a list of DIII-D discharge IDs:
```bash
python code/main.py --discharges 123456 123457 123458 123459 123460 123461 123462 123463 123464 123465
```

**Important**: You must provide at least 5 valid discharge IDs. The pipeline will fail if fewer than 5 valid discharges are retrieved (per FR-001).

### Configuration Options

- `--discharges`: Comma-separated or space-separated list of DIII-D discharge IDs (required).
- `--timeout`: Maximum execution time in seconds (default: 3600).
- `--output-dir`: Directory for output artifacts (default: `outputs/`).
- `--log-level`: Logging verbosity (default: `INFO`; options: `DEBUG`, `INFO`, `WARNING`, `ERROR`).

Example with custom options:
```bash
python code/main.py --discharges 123456,123457,123458,123459,123460 --timeout 7200 --log-level DEBUG
```

### Expected Outputs

Upon successful completion, the pipeline generates the following artifacts:

- **`data/processed/unified_analysis.csv`**: The unified dataset containing discharge metrics (island width, resonant surface density, tau_e, confinement mode, etc.).
- **`data/processed/metrics.csv`**: Detailed metric calculations for each discharge.
- **`outputs/summary_report.json`**: Final statistical analysis results, including correlation coefficients, p-values, confidence intervals, power analysis, and hypothesis status.
- **`outputs/topology_vs_confinement.png`**: Diagnostic scatter plot visualizing the relationship between island width and energy confinement time.
- **`outputs/checksum.txt`**: SHA-256 checksum for the unified dataset.

### Running Specific Modules

You can also run individual modules directly for testing or debugging:

- **Data Retrieval**:
 ```bash
 python code/data/retrieval.py --discharges 123456
 ```
- **Metrics Calculation**:
 ```bash
 python code/analysis/run_metrics.py
 ```
- **Correlation Analysis**:
 ```bash
 python code/analysis/correlation.py
 ```
- **Visualization**:
 ```bash
 python code/viz/plots.py
 ```

## Troubleshooting

- **Missing Data**: If the pipeline fails to retrieve data for a discharge, it will log a warning and exclude that discharge. Ensure you have a stable internet connection and that the discharge IDs are valid DIII-D discharges.
- **Timeout Errors**: If the pipeline exceeds the timeout limit, increase the `--timeout` value. The default is 3600 seconds (1 hour).
- **Insufficient Discharges**: The pipeline requires at least 5 valid discharges to proceed. If fewer are retrieved, the pipeline will abort with an error (FR-001).
- **MDSplus Connection Issues**: The retrieval logic includes retry mechanisms. If all retries fail, the discharge is excluded. Check the logs for specific error messages.

## Testing

Run the test suite to verify the implementation:
```bash
pytest tests/ -v
```

To run specific test categories:
- **Unit Tests**: `pytest tests/unit/ -v`
- **Integration Tests**: `pytest tests/integration/ -v`

## Further Reading

- **Project Specification**: See `specs/001-quantify-topology-confinement/spec.md` for detailed requirements.
- **Data Model**: Refer to `specs/001-quantify-topology-confinement/data-model.md` for schema definitions.
- **Contracts**: Review `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` for data validation rules.