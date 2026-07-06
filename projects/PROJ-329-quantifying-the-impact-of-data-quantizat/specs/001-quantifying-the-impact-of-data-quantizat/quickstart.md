# Quickstart: Quantizing GW Signals

## Prerequisites
- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with 7 GB+ RAM).

## 1. Clone and Setup
```bash
git clone <repo-url>
cd projects/PROJ-329-quantifying-the-impact-of-data-quantizat/code/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Download Data
The noise data is fetched automatically from the verified HuggingFace source.
```bash
python src/data_generation.py --download-noise
```
*Note: This downloads the O3 noise parquet file to `data/raw/` and computes a checksum.*

## 3. Run Simulation (Pilot)
Run a pilot generation of 50 signals to verify the pipeline.
```bash
python src/data_generation.py --generate --count 50 --bit-depths 8,12,16
```
*Output: `data/processed/waveforms.h5`*

## 4. Run Inference
Run parameter estimation on the generated signals.
```bash
python src/inference_engine.py --input data/processed/waveforms.h5 --method hybrid
```
*Output: `data/results/inference_results.json`*

## 5. Analyze & Visualize
Generate the error vs. SNR plots and identify the threshold.
```bash
python src/analysis.py --input data/results/inference_results.json --plot
```
*Output: `figures/error_threshold.png`, `figures/summary_report.md`*

## 6. Verify Acceptance
Run the unit tests to ensure quantization logic and error metrics are correct.
```bash
pytest tests/
```

## Troubleshooting
- **Memory Error**: Reduce `--count` in step 3. The default pilot is 50; the full study uses batching.
- **Convergence Failed**: Check `convergence_status` in results. Low SNR signals may fail; they are recorded as "non-detections".
- **Missing Noise**: If the HuggingFace download fails, check network connectivity. The fallback is a theoretical PSD (see `utils.py`).
