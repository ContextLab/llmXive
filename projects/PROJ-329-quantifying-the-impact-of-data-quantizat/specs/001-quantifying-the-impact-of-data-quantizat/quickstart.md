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
*Streams the parquet file from the verified Hugging Face URL and records a SHA‑256 checksum in `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`.*

## 3. Pilot Generation (All 6 Bit Depths, N = 1 200)
```bash
python src/data_generation.py \
  --generate \
  --count 1200 \
  --bit-depths 1,8,10,12,14,16 \
  --snr-bins 8-14,14-20,20-30,30-50 \
  --seed 42
```
*Creates `data/processed/waveforms.h5` with a float64 baseline and quantized groups for each of the six depths (6 × 4 × 50 = 1 200 signals). Checksums are written automatically.*

## 4. Run Inference (MCMC, CPU‑only)
```bash
python src/inference_engine.py \
  --input data/processed/waveforms.h5 \
  --method mcmc \
  --nthreads 2
```
*Produces `data/results/inference_results.json` containing posterior means, per‑parameter MSE, Δₖ, and convergence status.*

## 5. Analyse & Identify Thresholds
```bash
python src/analysis.py \
  --input data/results/inference_results.json \
  --plot-dir figures \
  --summary reports/crossover_thresholds.csv
```
*Aggregates Δₖ within SNR bins, fits LOWESS error‑vs‑SNR curves for each bit depth, identifies the SNR where median Δₖ > 10 % of the instrumental error, and writes diagnostic plots plus a CSV with 95 % confidence intervals (from 10 independent runs).*

## 6. Verify Resource Estimates
```bash
python scripts/compute_resource_estimate.py
```
*Shows a markdown table confirming RAM ≤ 7 GB, total CPU time ≤ 6 h, and disk usage ≤ 14 GB (see `reports/resource_estimate.md`).*

## 7. Run the Full Reproducibility Suite
```bash
pytest tests/
```
*Tests include:*
- `test_quantization.py` – verifies that each bit depth yields exactly `2**N` unique amplitude levels and correct step size (including 1‑bit and 16‑bit edge cases).  
- `test_pipeline.py` – end‑to‑end pilot on a reduced subset (100 signals, all depths) and checks that a state‑manager entry exists for each artifact.  
- `test_state_manager.py` – confirms SHA‑256 hashes are recorded in the project‑state YAML.

## 8. Perform the 10‑Run Reproducibility Study (SC‑005)
```bash
for seed in {1..10}; do
  python src/data_generation.py --generate --count 1200 --seed $seed --output-suffix _run$seed
  python src/inference_engine.py --input data/processed/waveforms_run${seed}.h5 --output data/results/inference_results_run${seed}.json
  python src/analysis.py --input data/results/inference_results_run${seed}.json --output reports/thresholds_run${seed}.csv
done
python src/analysis.py --aggregate reports/thresholds_run*.csv --output reports/crossover_thresholds_final.csv
```
*Produces `reports/crossover_thresholds_final.csv` with the median crossover SNR per bit depth and a 95 % confidence interval across the 10 runs (fulfills SC‑005).*

## 9. Troubleshooting
- **MemoryError**: Reduce `--count` or increase HDF5 chunk size.  
- **ConvergenceFailed**: Inspect the `convergence_status` field in the JSON; low‑SNR signals (< 8) are recorded as `"non-detection"` per the spec.  
- **Missing Noise File**: The downloader aborts with a clear error; re‑run `--download-noise`.  

---
