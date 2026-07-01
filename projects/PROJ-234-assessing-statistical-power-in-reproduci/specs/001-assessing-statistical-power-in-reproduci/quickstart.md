# Quickstart: Assessing Statistical Power in Reproducible Research with Public Datasets

## 1. Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for OpenML API)
- GitHub Actions Free Tier runner (for CI validation)

## 2. Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-234-assessing-statistical-power-in-reproduci
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## 3. Running the Pipeline

The pipeline is executed sequentially. Run the following commands from the project root:

### Step 1: Ingest Data
Retrieves a representative set of datasets from OpenML and checks for Open Access links.
```bash
python code/01_ingest_openml.py
```
*Output*: `data/raw/openml_raw.json`, `data/processed/filtered_datasets.csv`

### Step 2: Parse Publications
Extracts N and standardized effect sizes from **Open Access** publications.
```bash
python code/02_parse_publications.py
```
*Output*: `data/processed/statistical_params.json`

### Step 3: Compute Sensitivity (MDES)
Calculates the Minimum Detectable Effect Size (MDES) for valid entries.
```bash
python code/03_compute_sensitivity.py
```
*Output*: `data/processed/mdes_results.csv`

### Step 4: Generate Report
Creates the final audit visualization and summary.
```bash
python code/04_generate_report.py
```
*Output*: `data/processed/audit_report.html`

## 4. Testing

Run the unit and contract tests:

```bash
pytest tests/
```

- **Unit Tests**: Verify regex parsing and MDES calculation logic.
- **Contract Tests**: Validate output JSON/CSV against schemas in `contracts/`.

## 5. Reproduction

To reproduce the analysis exactly:
1.  Ensure `random.seed` is set in `code/` scripts (as per Constitution Principle I).
2.  Delete `data/` (except `data/raw/` if you want to keep raw API responses).
3.  Re-run the pipeline steps above.
4.  Verify checksums in `data/metadata.json`.

## 6. Troubleshooting

- **HTTP 429 (Rate Limit)**: The script includes exponential backoff. If it fails after max retries, check your network or OpenML status.
- **Missing Publication**: If a dataset has no link, it is skipped. Check `data/processed/filtered_datasets.csv` for `null` links.
- **Paywalled Content**: If a link is paywalled, the entry is marked `paywalled` and excluded from MDES calculation. Check `data/processed/statistical_params.json` for status.
- **Parsing Errors**: Check `data/processed/statistical_params.json` for entries marked `unparseable` or `invalid_metric`.
