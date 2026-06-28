# Quickstart: Assessing the Impact of Mindfulness Training on Default Mode Network Activity

## Prerequisites

- Python 3.11+ with virtual‑environment support
- R 4.3+ with `metafor` package
- Docker Engine 24.0+ (for fMRIPrep)
- OpenNeuro API access (when verified sources are available)
- Minimum 14 GB free disk space
- At least 2 CPU cores (GitHub Actions free tier)

## Setup Instructions

### 1. Clone and Initialize

```bash
git clone <repository-url>
cd projects/PROJ-103-assessing-the-impact-of-mindfulness-trai

# Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

pip install -r code/requirements.txt
```

### 2. Verify Dataset Availability (FR‑001, FR‑011)

```bash
python code/data/download_openneuro.py --verify-only
```

- The script queries the OpenNeuro API for datasets containing **pre/post mindfulness** scans.
- If ≥3 verified datasets are found, they are downloaded automatically.
- If none are found, the script logs the gap and proceeds with any available resting‑state dataset(s), issuing a clear warning that results are limited to a single‑dataset analysis.

### 3. Configure fMRIPrep (FR‑002)

Edit `code/preprocessing/docker_config.yaml`:

```yaml
fmriprep_version: "23.1.0"
nthreads: 2
omp_nthreads: 2
mem_mb: 6000
output_space: "MNI152NLin2009cAsym"
smoothing_fwhm: 6.0
bandpass_filter: [0.01, 0.1]
```

### 4. Run Preprocessing

```bash
python code/preprocessing/fmriprep_runner.py \
    --dataset dsXXXXXX \
    --output data/processed/fmriprep_outputs
```

- If the Docker run exceeds 7 GB RAM, the script automatically falls back to the **Nilearn lightweight preprocessing** pipeline (motion correction, slice timing, linear MNI registration, 6 mm smoothing, band‑pass).

### 5. DMN ROI Extraction (AAL Atlas) (FR‑003)

```bash
python code/connectivity/dmn_extraction.py \
    --input data/processed/fmriprep_outputs \
    --atlas aal \
    --nodes PCC mPFC IPL angular_gyrus
```

### 6. Connectivity & Statistical Testing (FR‑004, FR‑005)

```bash
python code/connectivity/correlation_matrix.py \
    --input data/processed/fmriprep_outputs \
    --output data/processed/connectivity_matrices

python code/connectivity/nbs_correction.py \
    --input data/processed/connectivity_matrices \
    --output data/processed/nbs_results \
    --permutations 10000 \
    --primary_threshold 3.1
```

- The script runs both **with** and **without** global signal regression; results are saved side‑by‑side.

### 7. Power Analysis (FR‑010, SC‑005)

```bash
python code/utils/power_analysis.py \
    --effect-size 0.5 \
    --alpha 0.05 \
    --power 0.80
```

- The script prints the required per‑group sample size `[deferred]` and records the calculation in `reports/power_analysis.txt`.

### 8. Meta‑Analysis (FR‑007, SC‑003)

```bash
Rscript code/meta_analysis/metafor_runner.R \
    --input data/processed/nbs_results \
    --output data/processed/meta_analysis_results \
    --model random_effects \
    --moderator scanner_site
```

- If fewer than three datasets are available, the script aborts with a clear message and skips the meta‑analysis, proceeding to generate a single‑dataset report.

### 9. Generate Final Report

```bash
python code/paper/generate_report.py \
    --input data/processed/meta_analysis_results \
    --output paper/final_report.md
```

- The report automatically includes QC figures, effect‑size tables, NBS‑corrected connectivity maps, power analysis summary, and Bayesian supplement (if sample < 30).

## Dependencies (`code/requirements.txt`)

```
nilearn==0.10.2
nibabel==5.2.1
networkx==3.2
scikit-learn==1.5.0
pandas==2.2.0
numpy==1.26.0
openneuro-py==2.0.1
statsmodels==0.14.0
pytest==8.2.0
bayesian‑testing==0.1.0   # lightweight Bayesian estimation
```

## Verification Tests

```bash
# Contract validation
pytest tests/contract/ -v

# Unit tests
pytest tests/unit/ -v

# Full pipeline (integration) – runs on a subset (≤5 subjects) to stay within CI limits
pytest tests/integration/test_full_pipeline.py -v
```

## Troubleshooting

- **fMRIPrep exceeds memory**: Reduce `nthreads` to 1 in `docker_config.yaml` or let the script switch to the Nilearn fallback.
- **No verified OpenNeuro datasets**: The pipeline will still run on any available resting‑state dataset(s); the final manuscript will contain a disclaimer about limited generalizability.
- **NBS permutation timeout**: Reduce `--permutations` to 5 000 (documented in methods) or increase parallelism if more cores become available.
- **GSR controversy**: Both GSR and non‑GSR results are generated; compare them in the report to assess sensitivity.

## Compute Constraints Reminder

- **CPU**: 2 cores max
- **RAM**: ≤7 GB peak
- **Disk**: ≤14 GB total
- **Runtime**: ≤6 h per CI job
- **GPU**: Not used

All steps are CPU‑tractable and respect the free‑tier limits.
