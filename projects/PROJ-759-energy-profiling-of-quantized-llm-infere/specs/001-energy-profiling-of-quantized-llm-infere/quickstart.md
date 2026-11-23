# Quickstart: Energy Profiling Benchmark

## 1. Clone and enter the environment

```bash
git clone <repository-url>
cd <repository>
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

## 2. Check the energy‑measurement backend (optional)

The benchmark performs this check internally; to run it manually:

```bash
python - <<'PY'
import pyRAPL
pyRAPL.setup()
print('pyRAPL available')
PY
```

If this fails, the benchmark will fall back to the external INA series power monitor (Pi 4) or to the sysfs powercap interface; otherwise it proceeds with CI‑level measurements.

## 3. Dry‑run sanity check

```bash
python -m code.benchmark --config data/configs/125M_4bit.json --dry-run
```

Expected: the model loads (or is skipped with a logged reason), the energy backend is probed, and the process exits successfully.

## 4. Run the pyRAPL availability test

```bash
pytest -q tests/test_pyrapl_load.py
```

This test verifies the `pyRAPL` import/init path and passes when the fallback chain engages correctly.

## 5. Run the full benchmark

```bash
python -m code.benchmark \
  --prompt-length several hundred \
  --repetitions multiple \
  --output-dir data/results \
  --log-dir logs
```

Downloads WikiText‑2 and model checkpoints, quantizes (torchao INT8/INT4), and executes multiple seeded runs per configuration. Expected CI runtime is on the order of several hours.

## 6. Inspect results

- `data/results/aggregated.csv` — per‑config mean ± std  
- `data/results/summary.json` — exponents, Bonferroni‑corrected p‑values, flags, achieved power, measurement‑authority labels  
- `figures/energy_vs_quantization.png`, `figures/energy_scaling_loglog.png`, `figures/cpu_freq_trace.png`

```python
import pandas as pd
df = pd.read_csv("data/results/aggregated.csv")
print(df.head())
```

## 7. Contract validation tests

```bash
pytest -q tests/contract
```

## 8. Raspberry Pi 4 (authoritative energy measurement)

On a Pi 4 equipped with an INA219 I²C power monitor:

```bash
python -m code.benchmark \
  --prompt-length 500 \
  --repetitions 12 \
  --output-dir data/results_pi4 \
  --log-dir logs \
  --platform pi4
```

Logs (including CPU frequency/throttling logs) are written to `logs/pi*_*.log`; these readings are the authoritative energy measurements per FR‑002.  
