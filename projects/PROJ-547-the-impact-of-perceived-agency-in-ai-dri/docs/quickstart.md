# Quick Start Guide: Perceived Agency in AI-CBT Pipeline

This guide walks you through running the full analysis pipeline end-to-end.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- At least 6GB available RAM (enforced by `resource_monitor.py`)
- Internet connection for initial data download (if not already present)

## Step 1: Environment Setup

```bash
# Clone the repository (if not already done)
git clone <repo-url>
cd PROJ-547-the-impact-of-perceived-agency-in-ai-dri

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate # Linux/macOS
# or
venv\Scripts\activate # Windows

# Install dependencies
pip install -r requirements.txt

# (Optional) Install pre-commit hooks
pre-commit install
```

## Step 2: Verify Data Availability

The pipeline requires external data. Check if the agency scale dataset exists:

```bash
python code/data_acquisition/download_agency_scale.py
```

If the file `data/external/agency_scale.csv` is missing, this script will download it from the configured source.

Similarly, ensure consent documentation is present:

```bash
python code/logging/store_consent.py
```

## Step 3: Run the Agency Scoring Pipeline (US1)

1. **Ingest Transcripts**:
 ```bash
 python code/agency_scoring/ingest_transcripts.py \
 --input data/raw/transcripts.csv \
 --output data/processed/ingested_transcripts.csv
 ```

2. **Detect Linguistic Markers**:
 ```bash
 python code/agency_scoring/detect_markers.py \
 --input data/processed/ingested_transcripts.csv \
 --output data/processed/detected_markers.csv
 ```

3. **Compute Agency Scores**:
 ```bash
 python code/agency_scoring/compute_scores.py \
 --input data/processed/detected_markers.csv \
 --config config/agency_weights.yaml \
 --output data/processed/agency_scores.csv
 ```

## Step 4: Run Adherence Extraction (US2)

```bash
python code/adherence_extraction/extract_metrics.py \
 --input data/raw/usage_logs.json \
 --output data/processed/adherence_metrics.csv

python code/adherence_extraction/ingest_demographics.py \
 --input data/raw/demographics.csv \
 --output data/processed/demographics.csv

python code/adherence_extraction/impute_confounders.py \
 --input data/processed/adherence_metrics.csv \
 --output data/processed/imputed_metrics.csv
```

## Step 5: Merge Datasets (US3)

```bash
python code/analysis/merge_datasets.py \
 --agency data/processed/agency_scores.csv \
 --adherence data/processed/imputed_metrics.csv \
 --demo data/processed/demographics.csv \
 --output data/processed/merged_data.csv
```

## Step 6: Validation (US4)

Before running regression, validate the agency score metric:

```bash
python code/validation/select_subset.py \
 --agency data/processed/agency_scores.csv \
 --external data/external/agency_scale.csv \
 --output data/processed/validation_subset.csv

python code/validation/compute_reliability.py \
 --input data/processed/validation_subset.csv \
 --output data/validation/reliability_report.yaml

python code/validation/compute_convergent.py \
 --input data/processed/validation_subset.csv \
 --output data/validation/convergent_report.yaml

python code/validation/check_thresholds.py \
 --reliability data/validation/reliability_report.yaml \
 --convergent data/validation/convergent_report.yaml
```

*Note: If thresholds are not met, the pipeline aborts here.*

## Step 7: Regression Analysis (US3)

```bash
python code/analysis/check_agency_variance.py \
 --input data/processed/merged_data.csv

python code/analysis/run_regression.py \
 --input data/processed/merged_data.csv \
 --output output/results/regression_summary.csv \
 --plots output/plots/

python code/analysis/compute_posthoc_power.py \
 --input output/results/regression_summary.csv \
 --output output/results/power_analysis.yaml
```

## Step 8: Review Results

All final outputs are located in the `output/` directory:

- **Regression Summary**: `output/results/regression_summary.csv`
- **Power Analysis**: `output/results/power_analysis.yaml`
- **Plots**: `output/plots/` (PNG files)
- **Provenance**: `output/provenance.yaml`

Check the logs for detailed execution traces:
```bash
ls -t logs/run_*.log | head -1
```

## Troubleshooting

- **Memory Error**: The `resource_monitor.py` enforces a 6GB limit. If you hit this, reduce batch sizes or optimize data loading.
- **Missing Data**: Ensure all `data/raw/` and `data/external/` files are present. Re-run download scripts if needed.
- **Validation Failure**: If `check_thresholds.py` aborts, review `data/validation/` reports to understand which metric failed.

## Next Steps

- Review `docs/logging.md` for log format details.
- Run `pytest tests/` to validate your environment.
- Consult `docs/ethics_statement.md` for compliance information.