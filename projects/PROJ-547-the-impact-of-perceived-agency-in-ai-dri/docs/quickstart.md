# Quickstart Guide: Perceived Agency in AI-CBT Pipeline

This guide provides step-by-step instructions to set up and run the research pipeline for **PROJ-547**.

## Prerequisites

- Python 3.11 or higher
- `pip` and `venv`
- Internet connection (for initial data download)

## 1. Environment Setup

Clone the repository and set up the virtual environment:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Data Acquisition

The pipeline requires raw transcript data and usage logs. If you are running this for the first time, download the datasets:

```bash
python code/data_acquisition/download_datasets.py
```

Validate the downloaded files to ensure integrity:

```bash
python code/data_acquisition/validate_metadata.py
```

*Note: External agency scale data is stored in `data/external/` and ingested via T062.*

## 3. Running the Pipeline

The pipeline consists of four main user stories (US1-US4) followed by the final analysis (US3).

### Step 3.1: Agency Scoring (US1)

Compute agency scores from conversation transcripts.

```bash
python code/agency_scoring/ingest_transcripts.py \
 --input data/raw/transcripts.json \
 --output data/processed/agency_scores_raw.csv

python code/agency_scoring/compute_scores.py \
 --input data/processed/agency_scores_raw.csv \
 --output data/processed/agency_scores.csv
```

### Step 3.2: Adherence Extraction (US2)

Extract adherence metrics from usage logs.

```bash
python code/adherence_extraction/extract_metrics.py \
 --input data/raw/usage_logs.json \
 --output data/processed/adherence_metrics.csv
```

### Step 3.3: Validation (US4)

Validate the agency score metric before proceeding to regression.

```bash
# Select a validation subset
python code/validation/select_subset.py \
 --agency data/processed/agency_scores.csv \
 --external data/external/agency_scale.csv \
 --output data/processed/validation_subset.csv

# Compute reliability and convergent validity
python code/validation/compute_reliability.py --input data/processed/validation_subset.csv
python code/validation/compute_convergent.py --input data/processed/validation_subset.csv

# Generate report
python code/validation/generate_report.py
```

*If validation thresholds are not met, the pipeline will abort. Check `validation/report.pdf`.*

### Step 3.4: Regression Analysis (US3)

Merge datasets and run the regression model.

```bash
# Merge data
python code/analysis/merge_datasets.py \
 --agency data/processed/agency_scores.csv \
 --adherence data/processed/adherence_metrics.csv \
 --demo data/processed/demographics.csv \
 --output data/processed/merged_data.csv

# Run regression
python code/analysis/run_regression.py \
 --input data/processed/merged_data.csv \
 --output output/
```

## 4. Reviewing Results

All final outputs are written to the `output/` directory.

- **Regression Summary**: `output/regression_summary.csv` contains coefficients, p-values, and confidence intervals.
- **Plots**: `output/plots/` contains visualizations of the relationship between agency and adherence.
- **Provenance**: `output/provenance.yaml` links every statistic to its source.

## 5. Logging and Verification

Every step logs to `logs/run_<timestamp>.log` in JSON-lines format.

To verify logging completeness:

```bash
python code/logging/verify_logging.py
```

This generates `logs/completeness_metric.json`.

## Troubleshooting

- **Missing Data**: Ensure `data/raw/` contains the required JSON files.
- **Validation Failure**: Check `validation/report.pdf` for specific metric failures.
- **Memory Errors**: The pipeline enforces a 6GB RAM limit; reduce batch sizes if necessary (via config).
