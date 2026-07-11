# Quickstart: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Prerequisites

- Python 3.11+
- `pip`
- Access to a GitHub Actions runner (or local environment with 7 GB+ RAM)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd <repo-name>
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r src/requirements.txt
 ```

## Data Setup

The pipeline requires the VAERS dataset. The verified source is:

- **Dataset Name**: `chrisvoncsefalvay/vaers-outcomes`
- **Accession ID**: `chrisvoncsefalvay/vaers-outcomes`
- **URL**: `

> **Note**: This is a derived dataset. The pipeline includes a **Schema Validation Gate** to verify it contains `VAX_TYPE` and MedDRA/SOC columns. If not, the pipeline will halt.

1. **Download the dataset**:
 ```bash
 python src/data/download.py
 ```
 This script will:
 - Fetch the dataset from the verified URL.
 - Verify the checksum.
 - Save to `data/raw/vaers.parquet`.

2. **Verify data integrity**:
 ```bash
 python src/data/validate.py
 ```
 This checks for required columns (`VAX_TYPE`, `SOC`, `REPT_DATE`) against `contracts/dataset.schema.yaml`. If validation fails, the pipeline halts.

## Running the Pipeline

Execute the full pipeline:

```bash
python src/main.py
```

This will:
1. Clean and filter the data.
2. Calculate ROR, PRR, IC for all SOCs.
3. Apply Benjamini-Hochberg correction.
4. Generate temporal profiles for top 5 signals.
5. Perform sensitivity analysis (Flu-only baseline).
6. Save results to `output/`.

## Output

- `output/signals.csv`: Final list of signals with metrics and adjusted p-values.
- `output/temporal_profiles/`: Plots and data for top 5 signals.
- `output/sensitivity_analysis.csv`: Delta metrics for Flu-only comparison.
- `output/report.md`: Summary of findings, including memory profile and limitations.

## Troubleshooting

- **Missing Columns**: If `VAX_TYPE` or `SOC` is missing, the pipeline will fail with a specific error code `E_SCHEMA_MISSING`. Check the dataset schema in `data/raw/`.
- **Memory Error**: If the dataset is too large, reduce the sample size or use chunked processing (modify `src/data/clean.py`).
- **Zero Counts**: The pipeline automatically applies a 0.5 continuity correction.

## Next Steps

- Review `output/report.md` for findings.
- Run `pytest tests/` to ensure all tests pass.
- Update `paper/` with the results.