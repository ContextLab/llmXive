# Quickstart: The Impact of Perceived Agency in AI‑Driven Cognitive Behavioral Therapy on Treatment Adherence

## Prerequisites

- Python 3.11
- Git
- ≥ 7 GB available RAM
- ≥ 14 GB available disk space
- Internet access (for dataset download)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Dataset Acquisition

```bash
# Download CBT conversation transcripts (verified URLs)
python code/data_acquisition/download_datasets.py

# This will:
# 1. Download the parquet files from the URLs listed in the plan.
# 2. Compute SHA‑256 checksums.
# 3. Verify checksums match the expected values.
# 4. Record source, version, license, and checksum in data/metadata.yaml.
# 5. Abort if any checksum mismatch occurs.
```

> **Important:** The pipeline **requires** a real usage‑metadata file, a demographics file, and an external perceived‑agency scale file. These are **not** provided by the verified CBT datasets. Place them in `data/raw/` with the exact filenames:
> - `usage_metadata.csv`
> - `demographics.csv`
> - `external_agency_scale.csv`
> If any of these files are missing, the pipeline will stop after the acquisition step and log a clear error.

## Running the Pipeline

### Full Pipeline (recommended)

```bash
python code/pipeline/run_full_pipeline.py
```

The orchestrator executes the steps in the required order:

1. **Data acquisition & checksum verification** (`download_datasets.py`)  
2. **Transcript ingestion** (`ingest_transcripts.py`) – supports CSV/JSON input.  
3. **Agency scoring** (`detect_markers.py` → `compute_scores.py`).  
4. **Adherence extraction** (`extract_metrics.py`) – enforces ≥ 7‑day gap for self‑report.  
5. **Confounder imputation / bias assessment** (`impute_confounders.py`).  
6. **Psychometric validation** (`compute_reliability.py`, `compute_convergent.py`). **If validation fails, the pipeline aborts.**  
7. **Dataset merge** (`merge_datasets.py`).  
8. **Regression analysis** (`run_regression.py`) – runtime guard < 30 min, power analysis, FDR correction.  
9. **Result generation** (`generate_plots.py`, summary CSV).  
10. **Logging audit** (`verify_logging.py`) – produces `logs/completeness_metric.json`.  

### Individual Components (for development)

```bash
# Ingest transcripts (CSV or JSON)
python code/agency_scoring/ingest_transcripts.py --input data/raw/transcripts.csv --output data/derived/cleaned_transcripts.parquet

# Compute agency scores
python code/agency_scoring/compute_scores.py --input data/derived/cleaned_transcripts.parquet --output data/derived/agency_scores.csv

# Extract adherence metrics (requires real usage_metadata.csv)
python code/adherence_extraction/extract_metrics.py --input data/raw/usage_metadata.csv --output data/derived/adherence_metrics.csv

# Impute missing confounders (if any)
python code/adherence_extraction/impute_confounders.py --input data/raw/demographics.csv --output data/derived/demographics_imputed.csv

# Psychometric validation (requires external_agency_scale.csv)
python code/validation/compute_reliability.py --input data/derived/agency_scores.csv --output data/validated_features/reliability.yaml
python code/validation/compute_convergent.py --agency data/derived/agency_scores.csv --scale data/raw/external_agency_scale.csv --output data/validated_features/convergent.yaml

# Merge for regression
python code/analysis/merge_datasets.py --agency data/derived/agency_scores.csv --adherence data/derived/adherence_metrics.csv --demo data/derived/demographics_imputed.csv --output data/derived/merged_data.csv

# Run regression
python code/analysis/run_regression.py --input data/derived/merged_data.csv --output data/derived/regression_results.csv

# Verify logging completeness
python code/logging/verify_logging.py --log_dir logs/ --output logs/completeness_metric.json
```

## Output Files

| File | Description |
|------|-------------|
| `data/derived/agency_scores.csv` | Per‑session agency scores (includes `utterance_count`, `processing_timestamp`). |
| `data/derived/adherence_metrics.csv` | Per‑user adherence metrics (including `time_gap_days`). |
| `data/validated_features/validation_report.yaml` | Psychometric validation results (reliability, convergent validity). |
| `data/derived/regression_results.csv` | Coefficients, p‑values, adjusted p‑values, CIs, R² for each outcome. |
| `output/results_summary.csv` | Human‑readable summary of key findings. |
| `output/regression_plots.png` | PNG visualizations of regression relationships. |
| `validation/report.pdf` | Full validation report (methods, tables, figures). |
| `logs/run_<timestamp>.log` | Full pipeline execution log. |
| `logs/completeness_metric.json` | Proportion of expected log entries (≥ 0.95 satisfies SC‑005). |

## Configuration

* **Marker Weights** – edit `code/agency_scoring/config/agency_weights.yaml`.  
* **Regression Settings** – edit `code/config/regression_config.yaml` (confounders, FDR method, confidence level).  
* **Imputation Settings** – edit `code/config/imputation_config.yaml` (iterations, random seed).  

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **Checksum mismatch** | Corrupted download | Re‑run `download_datasets.py`; check network stability. |
| **Missing required file** (`usage_metadata.csv`, etc.) | Dataset gap not filled | Provide the missing real dataset; synthetic placeholders are for development only. |
| **Validation failed** | No external agency scale or thresholds not met | Supply a validated scale file; if thresholds still fail, revise marker set or weights. |
| **Regression timeout** | Dataset too large or model mis‑specified | Reduce dataset size, verify model formulas, check for collinearity. |
| **Logging completeness < 0.95** | Some step did not emit a log entry | Ensure all scripts import `pipeline_logger` and call `log_step()` at each major phase. |
