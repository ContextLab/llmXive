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

## Data Acquisition (T001)

Download the verified real data (Harvard-Oxford cortical atlas, fetched
via `nilearn`) with paradigm-first verification against the OpenNeuro
API for `ds000030`:

```bash
python code/data_loader.py --output data/raw
```

This command:
1. Queries the OpenNeuro API for the dataset descriptor and a sample
   subject's `events.tsv` **before** downloading imaging data and
   verifies that both "Inclusion" and "Exclusion" trial types exist
   (FR-010; aborts with error code `101897695` in `--paradigm-mode
   strict` when markers are missing — the default `record` mode logs
   and records the outcome in the manifest, since the dataset premise
   is pending a spec amendment).
2. Streams the Harvard-Oxford atlas NIfTI into `data/raw/` with
   integrity verification (opens with `nibabel`, size > 0).
3. Computes SHA-256 checksums for every downloaded NIfTI and writes
   `data/raw/checksums.json`.
4. Writes `data/processed/dataset_manifest.json`.

Network fetches retry with exponential backoff (1 s -> 2 s -> 4 s,
3 attempts, FR-013); on final failure the loader raises
`DataUnavailableError` (`ERR_DATA_UNAVAILABLE`).

## Full Analysis Pipeline

The complete analysis runs in three orchestrated steps:

```bash
# Step 1: Download data and run QC
python code/src/main.py --step download_qc

# Step 2: Extract ROI time-series and compute connectivity
python code/src/main.py --step extract_connectivity

# Step 3: Run statistical tests and generate visualizations
python code/src/main.py --step stats_viz --seed 42
```

## Pipeline Output

The pipeline generates:

1. **Data files** (under `data/`):
- `data/raw/checksums.json` – SHA256 checksums for all downloaded NIfTI files
- `data/processed/dataset_manifest.json` – Dataset manifest with paradigm verification status
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
# Run unit tests for the data loader
python -m pytest code/tests/test_data_loader.py -v
```

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| `101897695` (Missing event markers) | Dataset lacks Inclusion/Exclusion markers | Run with `--paradigm-mode record` to record the outcome, or point `--dataset` at a verified Cyberball dataset |
| `101897696` (Insufficient subjects) | Fewer than 10 subjects passed QC | Review `data/processed/subject_qc_list.json` |
| `ERR_DATA_UNAVAILABLE` | Network fetch failed after 3 backoff attempts | Check internet access and re-run `python code/data_loader.py --output data/raw` |
| Missing `checksums.json` | Data loader did not complete | Re-run `python code/data_loader.py --output data/raw` |