# Quickstart: Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites

## Prerequisites

- Python 3.11+
- Materials Project API Key (stored in `MP_API_KEY` env var)
- 7 GB RAM available

## Installation

1.  **Clone & Setup**
    ```bash
    cd projects/PROJ-035-exploring-the-correlation-between-crysta
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Configure API**
    ```bash
    export MP_API_KEY="your_api_key_here"
    ```

## Execution

1.  **Ingest Data** (Phase 1)
    ```bash
    python code/ingestion.py --output data/processed/cleaned_perovskites.csv
    ```
    *Checks for ABX3 stoichiometry and missing thermal values.*

2.  **Compute Descriptors** (Phase 2)
    ```bash
    python code/descriptors.py --input data/processed/cleaned_perovskites.csv --output data/processed/with_descriptors.csv
    ```
    *Calculates tilting, bond variance, tolerance factor.*

3.  **Run Analysis** (Phase 3)
    ```bash
    python code/analysis.py --input data/processed/with_descriptors.csv --output data/processed/analysis_results.csv
    ```
    *Runs correlations, FDR correction, VIF, and regression.*

4.  **Generate Report** (Phase 4)
    ```bash
    python code/reporting.py --input data/processed/analysis_results.csv --output docs/report.md
    ```
    *Generates plots and text with associational framing.*

## Verification

- **Contract Test**: Run `pytest tests/contract/` to validate output against `contracts/analysis_result.schema.yaml`.
- **Reproducibility**: Re-run `code/` scripts; checksums in `state/...yaml` should match (if data unchanged).
