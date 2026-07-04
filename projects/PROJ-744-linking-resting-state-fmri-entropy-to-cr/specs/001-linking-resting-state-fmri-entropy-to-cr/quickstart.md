# Quickstart: Linking Resting‑State fMRI Entropy to Creative Problem Solving

## Prerequisites

- Python 3.11+
- 8 GB RAM (recommended for full cohort processing)
- Internet access for initial dataset download (subsequent runs use local cache)

## Installation

1. **Clone and Setup Environment**
   ```bash
   cd projects/PROJ-744-linking-resting-state-fmri-entropy-to-cr
   python -m venv venv
   source venv/bin/activate
   pip install -r code/requirements.txt
   ```

2. **Verify Dependencies**
   ```bash
   python -c "import nibabel, pandas, statsmodels, numpy; print('All dependencies OK')"
   ```

## Running the Pipeline

### 1. Download Data
Fetch the HCP data from the verified OpenNeuro S3 bucket (ds000114).
```bash
python code/ingestion/download_hcp.py --batch-size 50
```
*Output*: `data/raw/hcp_fMRI.nii.gz` (or CIFTI), `data/raw/phenotypes.csv`.

### 2. Parcellation & Entropy
Extract time series and compute MSE.
```bash
python code/entropy/aggregate.py --scales 1-20 --r 0.2
```
*Output*: `data/results/entropy_metrics.csv`.

### 3. Statistical Modeling
Run RLM and BH-FDR correction.
```bash
python code/modeling/robust_regression.py --permutations 0
```
*Output*: `data/results/association_results.csv`, `reports/summary.json`.

### 4. Sensitivity Analysis (Optional)
Run the r-sweep.
```bash
python code/modeling/sensitivity.py --r-values 0.15,0.20,0.25
```

### 5. Performance Verification
Run the full benchmark on the CI runner.
```bash
bash code/benchmark/benchmark.sh
```
*Output*: `reports/benchmark_log.txt` (pass/fail status).

## Verification

Run the test suite to ensure correctness:
```bash
pytest tests/
```
*Expected*: All tests pass, including `test_mse_reference` (tolerance 1e-6) and `test_pipeline_flow`.

## Troubleshooting

- **Memory Error**: Reduce `--batch-size` in `download_hcp.py` or process subjects in smaller chunks in `aggregate.py`.
- **Missing Data**: Check `data/processed/excluded_subjects.log` for subjects dropped due to missing scores or motion.
- **NaN Entropy**: Verify that the `time_series` column in `parcel_timeseries.csv` does not contain flat lines (constant values).
- **Performance Failure**: If benchmark fails, check `reports/benchmark_log.txt` for memory/time bottlenecks and optimize batch sizes.