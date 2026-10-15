# Quickstart: Quantizing GW Signals

## Prerequisites
- Python 3.11+
- Git
- Access to a GitHub Actions runner (or a local Linux environment with ≥ 7 GB RAM)

## 1. Clone and Set Up
```bash
git clone <repo-url>
cd projects/PROJ-329-quantizing-the-impact-of-data-quantizat/code/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Download LIGO O3 Noise (Verified)
```bash
python src/data_generation.py --download-noise
```
*The script streams the parquet file from the verified Hugging Face URL and records a SHA‑256 checksum in the project state file `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`.*

## 3. Pilot Generation (All 6 Bit Depths, N=1200)
```bash
python src/data_generation.py \
  --generate \
  --count 1200 \
  --bit-depths 1,8,10,12,14,16 \
  --snr-bins 8-14,14-20,20-30,30-50
```
*Creates `data/processed/waveforms.h5` with float64 baseline and quantized groups for all 6 depths (6 depths × 4 bins × 50 signals per bin = 1200 total). A checksum is written automatically to the project state file.*

## 4. Run Inference (MCMC, CPU-only)
```bash
python src/inference_engine.py \
  --input data/processed/waveforms.h5 \
  --method mcmc \
  --nthreads 2
```
*Outputs `data/results/inference_results.json` with per-parameter MSE and Δ_k for both quantized and float64 baseline results.*

## 5. Analyse & Identify Thresholds
```bash
python src/analysis.py \
  --input data/results/inference_results.json \
  --plot-dir figures \
  --summary reports/thresholds.csv
```
*Aggregates Δ_k within SNR bins using median, generates error‑vs‑SNR curves for all six bit depths, identifies SNR crossover per bit depth (where median(Δ_k) exceeds 10% of the bin-level instrumental error), and writes a reproducibility report with a 95% confidence interval from 10 independent runs.*

## 6. Verify Resource Estimates
```bash
python scripts/compute_resource_estimate.py
```
*Shows a markdown table confirming RAM ≤ 7 GB, total CPU time ≤ 6 h, and disk usage ≤ 14 GB.*

## 7. Run the Full Reproducibility Suite
```bash
pytest tests/
```
*Tests include:*
- `test_quantization.py` (all six bit depths — 1, 8, 10, 12, 14, 16: verify 2^N levels and step‑size for each)  
- `test_pipeline.py` (end‑to‑end pilot with N=100 signals, all 6 depths)  
- `test_state_manager.py` (hashes written to `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`)

## 8. Run 10-Independent-Run Reproducibility Study
```bash
for seed in {1..10}; do
  python src/data_generation.py --generate --count 1200 --seed $seed --output-suffix _run$seed
  python src/inference_engine.py --input data/processed/waveforms_run$seed.h5 --output data/results/inference_results_run$seed.json
  python src/analysis.py --input data/results/inference_results_run$seed.json --output reports/thresholds_run$seed.csv
done
python src/analysis.py --aggregate reports/thresholds_run*.csv --output reports/thresholds_final_with_ci.csv
```
*Produces 95% confidence intervals on crossover SNR per bit depth (SC-005).*

## 9. Troubleshooting
- **MemoryError**: Reduce `--count` or increase HDF5 chunk size.  
- **ConvergenceFailed**: Check `convergence_status` in the JSON; low‑SNR signals (< 8) are recorded as `"non-detection"` per the spec.  
- **Missing Noise File**: The downloader will abort with a clear message; re-run `--download-noise`.  