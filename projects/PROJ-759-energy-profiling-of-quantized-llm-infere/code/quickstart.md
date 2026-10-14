# Quickstart: Running the Energy Profiling Benchmark

This guide walks you through reproducing the full experiment on a fresh GitHub Actions runner or a local Linux machine with similar resources.

## 1. Clone the Repository & Enter the Project
```bash
git clone <repository-url>
cd energy-profiling-quantized-llm
```

## 2. Create a Virtual Environment & Install Dependencies
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## 3. Download the WikiText‑2 Dataset
The benchmark requires the WikiText‑2 dataset in Parquet format. Run the
data‑loader helper to fetch it and record its checksum:

```bash
python -m code.utils.data_loader
```

After the command finishes you should see a `data/raw/wikitext2.parquet` file
and a `data/raw/README.md` containing its SHA‑256 checksum.

## 4. Verify Dataset Availability (Optional checksum)
```bash
python -c "
import hashlib, pathlib, sys
path = pathlib.Path('data/raw/wikitext2.parquet')
h = hashlib.sha256()
h.update(path.read_bytes())
print('SHA256:', h.hexdigest())
"
```

## 5. Verify Energy‑Measurement Library (pyRAPL)
Before running the full benchmark you can confirm that the energy‑measurement
library loads correctly on this runner:

```bash
python -m code.benchmark \
 --config data/configs/125M_4bit.json \
 --dry-run
```
You should see the output:

```
pyRAPL available
```

## 6. Run the Full Benchmark
```bash
python -m code.benchmark \
 --config data/configs/125M_4bit.json \
 --prompt-length 500 \
 --repetitions 5 \
 --output-dir data/results \
 --log-dir logs
```
- The script will download the GPT‑Neo checkpoints (if not cached), quantize them,
 and execute the energy‑aware inference loop.
- Expected runtime on the CI runner: **≈ 4.5 h**.

## 7. Inspect the Results
- **Aggregated CSV**: `data/results/aggregated.csv`
- **Statistical Summary**: `data/results/summary.json`
- **Figures**: `figures/energy_vs_quantization.png`, `figures/energy_scaling_loglog.png`, `figures/cpu_freq_trace.png`

## 8. Run the Unit‑Level Contract Tests (optional)
```bash
pytest -q tests/contract
```