# Quickstart: Running the Energy Profiling Benchmark

This guide walks you through reproducing the full experiment on a fresh GitHub Actions runner or a local Linux machine with comparable resources.

## 1. Clone the Repository & Enter the Project
```bash
git clone https://github.com/your-org/energy-profiling-quantized-llm.git
cd energy-profiling-quantized-llm
```

## 2. Create a Virtual Environment & Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions (see plan.md)
```

## 3. Verify the Energy‑Measurement Backend (optional)
The benchmark script performs an internal pyRAPL initialization check.  
If you wish to run the check manually:

```bash
python -c "import pyRAPL; pyRAPL.setup(); print('pyRAPL available')"
```

If this command fails, the script will automatically fall back to `powerstat`, or log “Energy measurement unavailable”.

## 4. Run the Full Benchmark
```bash
python -m code.benchmark \
  --prompt-length 500 \
  --repetitions 10 \
  --output-dir data/results \
  --log-dir logs
```

- The script downloads the GPT‑Neo checkpoints (if not cached), quantizes them, and executes the energy‑aware inference loop.  
- Expected runtime on the CI runner: **≈ 4.5 h**.

## 5. Dry‑Run Mode (sanity check)
You can perform a quick dry‑run that loads a model and performs the pyRAPL availability check without full inference:

```bash
python -m code.benchmark --config data/configs/125M_4bit.json --dry-run
```

You should see a line like `pyRAPL available` (or the fallback message) and then exit with status 0.

## 6. Inspect the Results
- **Aggregated CSV**: `data/results/aggregated.csv`  
- **Statistical Summary**: `data/results/summary.json`  
- **Figures**: `figures/energy_vs_quantization.png`, `figures/energy_scaling_loglog.png`, `figures/cpu_freq_trace.png`  

Example to view the CSV with pandas:
```python
import pandas as pd
df = pd.read_csv('data/results/aggregated.csv')
print(df.head())
```

## 7. Run Contract Validation Tests (optional but recommended)
```bash
pytest -q tests/contract
```
All tests should pass, confirming that generated JSON/CSV files conform to the schemas in `contracts/`.

## 8. Optional Edge‑Hardware Validation (Raspberry Pi 4)
If you have a Raspberry Pi 4 available, run the same command on that device. The script auto‑detects the platform, logs CPU frequency/throttling, and produces a separate set of logs under `logs/pi4_*.log`. Compare the resulting `aggregated.csv` with the CI results to assess proxy fidelity.

---



