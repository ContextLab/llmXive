# Quickstart: Quantifying the Impact of Data Resolution on Gravitational Wave Parameter Estimation

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution) or local environment with 7GB+ RAM.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-465-quantifying-the-impact-of-data-resolutio
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `gwpy`, `bilby`, `dynesty`, `scipy`, `numpy`, `pandas`, `h5py`.*

## Running the Pipeline

### Step 1: Download Data
Fetch the GW150914 strain data from GWOSC.
```bash
python code/download.py --event GW150914 --output data/raw/GW150914.h5
```
*Output*: `data/raw/GW150914.h5` (checksum verified).

### Step 2: Process Data (Downsample & Quantize)
Generate derived datasets for different resolutions.
```bash
python code/process.py \
  --input data/raw/GW150914.h5 \
  --rates 4096 2048 1024 \
  --bit-depths 16 32 \
  --output-dir data/derived/
```
*Output*: `data/derived/GW150914_2048Hz_16bit.h5`, etc.

### Step 3: Run Inference
Execute the `bilby` pipeline with `dynesty` for a specific configuration.
```bash
python code/infer.py \
  --input data/derived/GW150914_2048Hz_16bit.h5 \
  --waveform IMRPhenomPv2 \
  --max-iterations 10000 \
  --dlogz-threshold 0.1 \
  --output results/posteriors/GW150914_2048Hz_16bit.h5
```
*Output*: Posterior file with `convergence_status` (converged/inconclusive) and `dlogz` value.

### Step 4: Calculate Metrics
Compute divergence and consistency deviation.
```bash
python code/metrics.py \
  --posterior results/posteriors/GW150914_2048Hz_16bit.h5 \
  --ground-truth GW150914 \
  --output results/metrics/GW150914_2048Hz_16bit.json
```

### Step 5: Aggregate Results
Identify resolution trends.
```bash
python code/aggregate.py \
  --metrics-dir results/metrics/ \
  --output results/summary_report.csv
```

## Verification

Run the test suite to ensure contract compliance:
```bash
pytest tests/contract/ -v
```
*Expected*: All schema validation tests pass.

## Troubleshooting

- **Memory Error**: Reduce `--max-iterations` or use a smaller time window in `process.py`.
- **Convergence Failure**: The run will be marked "inconclusive" if `dlogz` > 0.1 after max iterations. Check logs for `dlogz` statistics.
- **GWOSC Timeout**: Ensure network connectivity; `gwpy` has built-in retries.
- **Sampler Issues**: Ensure `dynesty` is installed and compatible with `bilby` version.