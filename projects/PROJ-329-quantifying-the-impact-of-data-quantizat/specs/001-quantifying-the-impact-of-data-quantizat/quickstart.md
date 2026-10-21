# Quickstart: Quantizing GW Signals

## Prerequisites
- Python 3.11+
- Git
- Access to a GitHub Actions runner (or a local Linux environment with ≥ 7 GB RAM)

## 1. Clone and Set Up
```bash
git clone <repo-url>
cd projects/PROJ-329-quantizing-the-impact-of-data-quantizat/code/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Download LIGO O3 Noise (Verified)
```bash
python src/data_generation.py --download-noise
```
*Streams the parquet file from the verified Hugging  Face URL and records a SHA‑256 checksum in `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml` (the project’s Single Source of Truth).*

## 3. Pilot Generation (All examined bit depths, N = 2 400)
```bash
# Split the full workload into four CI jobs (each handles a large number of signals)
for JOB in 0 1 2 3; do
  python src/data_generation.py \
    --generate \
    --count 2400 \
    --bit-depths 1,8,10,12,14,16 \
    --snr-bins 8-14,14-20,20-30,30-50 \
    --seed 42 \
    --job-index $JOB \
    --output-suffix _job${JOB}
done
```
*Creates `data/processed/waveforms.h5` (baseline + quantized groups) and writes per‑waveform JSON metadata files that conform to `contracts/waveform.schema.yaml`. Checksums are written automatically.*

## 4. Run Inference (MCMC, CPU‑only)
```bash
# Run the same four‑job split for inference
for JOB in 0 1 2 3; do
  python src/inference_engine.py \
    --input data/processed/waveforms_job${JOB}.h5 \
    --method mcmc \
    --nthreads 2 \
    --job-index $JOB \
    --output-suffix _job${JOB}
done
```
*Produces `data/results/inference_results_job${JOB}.json` containing posterior means, per‑parameter MSE, Δₖ, and convergence status. Each result is validated against `contracts/result.schema.yaml`.*

## 5. Analyse & Identify Thresholds
```bash
python src/analysis.py \
  --input data/results/inference_results_job*.json \
  --plot-dir figures \
  --summary reports/crossover_thresholds.csv
```
*Aggregates Δₖ within SNR bins, fits LOWESS error‑vs‑SNR curves for each bit depth, identifies the SNR where median Δₖ > 10 % of the instrumental error, and writes diagnostic plots plus a CSV with 95 % confidence intervals (from a multi‑run reproducibility study).*

## 6. Verify Resource Estimates
```bash
python scripts/compute_resource_estimate.py
```
*Benchmarks the **full pipeline** (generation + quantization + inference + analysis) and writes `reports/resource_estimate.md`, confirming RAM ≤ 5 GB, CPU time ≤ 5.5 h per CI job, and disk usage ≤ 14 GB.*

## 7. Run the Full Reproducibility Suite (SC‑005)
```bash
for SEED in {1..10}; do
  python src/data_generation.py --generate --count 2400 --seed $SEED --output-suffix _run${SEED} --job-index 0
  python src/inference_engine.py --input data/processed/waveforms_run${SEED}.h5 --output data/results/inference_results_run${SEED}.json --job-index 0
  python src/analysis.py --input data/results/inference_results_run${SEED}.json --output reports/thresholds_run${SEED}.csv
done
python src/analysis.py --aggregate reports/thresholds_run*.csv --output reports/crossover_thresholds_final.csv
```
*Produces `reports/crossover_thresholds_final.csv` with the median crossover SNR per bit depth and a 95 % confidence interval across multiple runs (fulfills SC‑005).*

## 8. Troubleshooting
- **MemoryError**: Reduce `--count` or increase HDF5 chunk size.  
- **ConvergenceFailed**: Inspect the `convergence_status` field in the JSON; low‑SNR signals (< 8) are recorded as `"non-detection"` per the spec.  
- **Missing Noise File**: The downloader aborts with a clear error; re‑run `--download-noise` to fetch the file again.
