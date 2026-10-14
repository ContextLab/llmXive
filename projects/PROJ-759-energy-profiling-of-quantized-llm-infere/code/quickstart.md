# Quickstart: Running the Energy Profiling Benchmark

This guide walks you through reproducing the full experiment on a fresh GitHub
Actions runner or a local Linux machine with similar resources.

## 1. Clone the Repository & Enter the Project
```bash
git clone <repository-url>
cd energy-profiling-quantized-llm
```

## 2. Create a Virtual Environment & Install Dependencies
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt # pins exact versions (see plan.md)
```

## 3. Verify Dataset Availability (Optional checksum)
```bash
python -c "
import hashlib, pathlib, sys
path = pathlib.Path('data/raw/wikitext2.parquet')
h = hashlib.sha256()
h.update(path.read_bytes())
print('SHA256:', h.hexdigest())
"
# Compare the output to the checksum recorded in data/raw/README.md
```

## 4. Verify Energy‑Measurement Library (pyRAPL)
Before running the full benchmark you can confirm that the energy‑measurement
library loads correctly on this runner:

```bash
python -m code.benchmark \\
 --config data/configs/gpt-neo-125M_4bit.json \\
 --dry-run
```
You should see the output:

```
pyRAPL available
```

If the command fails, ensure that the `pyRAPL` package is installed (see
`requirements.txt`) and that the runner provides access to CPU power counters.

## 5. Run the Full Benchmark
```bash
python -m code.benchmark \\
 --config data/configs/gpt-neo-125M_4bit.json \\
 --prompt-length 500 \\
 --repetitions 5 \\
 --output-dir data/results \\
 --log-dir logs
```
- The script will download the GPT‑Neo checkpoints (if not cached), quantize them,
 and execute the energy‑aware inference loop.
- Expected runtime on the CI runner: **≈ 4.5 h**.

## 6. Inspect the Results
- **Aggregated CSV**: `data/results/aggregated.csv`
- **Statistical Summary**: `data/results/summary.json`
- **Figures**: `figures/energy_vs_quantization.png`,
 `figures/energy_scaling_loglog.png`,
 `figures/cpu_freq_trace.png`

Open the CSV with any spreadsheet tool or `pandas`:
```python
import pandas as pd
df = pd.read_csv('data/results/aggregated.csv')
print(df.head())
```

## 7. Run the Unit‑Level Contract Tests (optional)
```bash
pytest -q tests/contract
```
All tests should pass, confirming that generated JSON/CSV files conform to the
schemas in `contracts/`.

## 8. Optional Edge‑Hardware Validation (Raspberry Pi 4)
If you have access to a Raspberry Pi 4, run the same command on that device.
The script will automatically detect the platform and log CPU frequency/throttling
information. Compare the resulting `aggregated.csv` with the CI results to assess
proxy fidelity.
