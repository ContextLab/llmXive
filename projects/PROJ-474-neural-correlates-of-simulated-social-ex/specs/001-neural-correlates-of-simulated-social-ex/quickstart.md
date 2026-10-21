# Quickstart: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

## Prerequisites
- Python 3.11 or newer
- Git
- Internet access from the CI runner (to fetch verified datasets)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd neural-correlates-social-exclusion

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r code/requirements.txt
```

## Data Setup & Full Analysis Pipeline

The complete analysis runs in three orchestrated steps:

```bash
# Step 1: Download data and run QC
python code/src/main.py --step download_qc

# Step 2: Extract ROI time-series and compute connectivity
python code/src/main.py --step extract_connectivity

# Step 3: Run statistical tests and generate visualizations
python code/src/main.py --step stats_viz
```

Or run the full pipeline at once with a specific random seed:

```bash
# Full pipeline with reproducible seed
python code/src/main.py --step download_qc && \
python code/src/main.py --step extract_connectivity && \
python code/src/main.py --step stats_viz --seed 42
```

## Pipeline Output

The pipeline generates:

1. **Data files** (under `data/`):
   - `data/raw/checksums.json` – SHA256 checksums for all downloaded NIfTI files
   - `data/processed/subject_qc_list.json` – Full QC results for all subjects
   - `data/processed/subjects_metadata.json` – Retained subjects after motion QC
   - `data/processed/raw_timeseries_*.parquet` – ROI time-series per subject/condition

2. **Results** (under `data/results/`):
   - `strength_per_subject.parquet` – Static connectivity metrics
   - `dynamic_summary.parquet` – Dynamic connectivity summary statistics
   - `statistical_result.json` – Permutation test results (primary signed metric)
   - `statistical_result_absolute.json` – Secondary absolute metric results
   - `figures/` – All visualizations (histograms, heatmaps, plots)

3. **Report**:
   - `data/results/report.md` – Auto-generated methods and results narrative

## Validation & Testing

```bash
# Run unit and integration tests
pytest code/tests/ -v

# Schema validation example
python - <<'PY'
import json, yaml, jsonschema, pathlib
schema = yaml.safe_load(open('contracts/connectivity.schema.yaml'))
data   = json.load(open('data/processed/connectivity_sample.json'))
jsonschema.validate(instance=data, schema=schema)
print("Connectivity file validates.")
PY
```

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| `Unknown step: --step` | Circular import in main.py | Update main.py (should be fixed in latest version) |
| `101897696` (Insufficient subjects) | Fewer than 10 subjects passed QC | Review `data/processed/subject_qc_list.json` and consider a less stringent motion threshold (exploratory only). |
| `MemoryError` | Attempting to load whole NIfTI into RAM | Ensure streaming mode is enabled (default). |
| Missing `subject_qc_list.json` | QC pipeline did not complete | Check logs and ensure `--step download_qc` completed successfully. |
| Missing `checksums.json` | Data loader did not complete | Verify NIfTI files exist in `data/raw/` and re-run `--step download_qc`. |

---