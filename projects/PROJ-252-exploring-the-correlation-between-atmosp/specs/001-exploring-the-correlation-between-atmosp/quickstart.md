# Quickstart: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Prerequisites

- Python 3.11+
- `pip`
- ~14 GB free disk space
- Internet access (for data download)

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-252-exploring-the-correlation-between-atmosp
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via a single entry point script.

```bash
# Step 1: Download data (skips if checksums match)
python code/download.py

# Step 2: Preprocess (interpolation, anomaly calc, filtering)
python code/preprocess.py

# Step 3: Run statistical analysis
python code/analysis.py

# Step 4: Generate report
python code/report.py
```

**Output**:
- `data/processed/analysis_results.json`: Contains p-values, effect sizes, and robustness metrics.
- `paper/results.md`: Human-readable summary of findings.

## Validation

To verify the installation and data integrity:

```bash
pytest tests/
```

This will run unit tests for data loading and contract tests for schema validation.
