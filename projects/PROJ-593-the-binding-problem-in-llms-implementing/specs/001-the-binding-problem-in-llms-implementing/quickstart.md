# Quickstart: The Binding Problem in LLMs – Synchronized Oscillations for Feature Integration

## 1. Prerequisites
- Python 3.x or newer  
- Git  
- Internet access (to download public HuggingFace datasets)  
- GitHub Actions runner **or** a local Linux/macOS environment with ≥ 7 GB RAM

## 2. Installation
```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-593-the-binding-problem-in-llms-implementing

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 3. Data Download (automated on first run)
```bash
# Fetch synthetic PLV reference (≈ a few MB)
python src/data/download_plv_reference.py   # creates data/raw/plv_reference.json

# Download CLUTRR benchmark
python src/data/download_clutrr.py          # creates data/raw/clutrr.parquet
```
*The scripts verify checksums and record them automatically.*

## 4. Running the Full Analysis Pipeline
```bash
# Main orchestration script
python src/main.py \
  --freq-sweep 30 35 40 45 50 \
  --seeds 42 123 456 789 101 \
  --config config/default.yaml
```
The command performs:
1. Model construction with oscillatory gating (FR‑001); identical hyper‑parameters for baseline and oscillatory runs (methodology‑9520a946).  
2. Forward passes, recording `ActivationTimeSeries`.  
3. Spectral analysis via Welch PSD and SNR computation (FR‑002, SC‑001).  
4. **Residual‑phase PLV** calculation between model activations (after mask subtraction) and the synthetic PLV reference (FR‑003, SC‑002).  
5. Permutation test & Bonferroni correction (FR‑004, FR‑006).  
6. Benchmark evaluation on CLUTRR and bAbI (FR‑005).  
7. Frequency‑sweep aggregation and reporting (SC‑004).  
8. Outputs are written to `data/final/` (see `data-model.md`).

### 4.1 Running Individual Sub‑tasks
- **Spectral analysis only**  
  ```bash
  python src/analysis/spectral.py --activations data/processed/activations_42.npy
  ```
- **PLV calculation for a single frequency**  
  ```bash
  python src/analysis/plv.py --activations data/processed/activations_42.npy \
    --reference data/raw/plv_reference.json --freq 40
  ```
- **Benchmark evaluation**  
  ```bash
  python src/benchmarks/clutrr_eval.py --seed 42
  python src/benchmarks/babi_eval.py   --seed 42
  ```

## 5. Verification
```bash
# Unit tests
pytest tests/unit/

# Integration tests (forward‑pass + SNR check)
pytest tests/integration/

# Contract validation (JSON schema compliance)
pytest tests/contract/
```

## 6. Expected Outputs
- `data/final/results_summary.json` – aggregated metrics per frequency.  
- `data/final/statistical_report.json` – permutation test details, corrected p‑values.  
- `plots/` – PNG/PDF figures: (a) spectral peak & SNR, (b) PLV distribution, (c) benchmark performance bar charts.  

## 7. Troubleshooting
- **Out‑of‑Memory**: Reduce `--batch-size` in `src/config.py` or increase streaming chunk size.  
- **CUDA errors**: The pipeline automatically falls back to CPU; ensure `torch` is installed without CUDA support.  
- **Missing PLV reference**: Verify internet connectivity; re‑run `download_plv_reference.py` which will re‑attempt streaming.  
- **Low SNR**: The script will log a warning and automatically report the broader 30‑50 token‑relative band, recording the fallback in `statistical_report.json`.  

---

