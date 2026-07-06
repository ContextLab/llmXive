# Quickstart: Exploring the Correlation Between Atmospheric River Frequency and Global Geopotential Height Variability

## Prerequisites
- GitHub Actions runner (or local Linux/macOS) with **Python 3.11**.
- Internet access to the Copernicus Climate Data Store and the verified HuggingFace ERA5 file.

## Setup

```bash
# 1. Clone the repository (assume you are in the project root)
git clone
cd atmospheric-river-geopotential

# 2. Create a virtual environment and install pinned dependencies
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt # pins exact versions
```

## Run the Full Analysis (single command)

```bash
# The CLI orchestrates all phases (0–9). The `--full` flag runs end‑to‑end.
python -m src.cli.run_analysis --full
```

The command will:
1. Download ERA5 IVT (and Z500 via CDS) and verify checksums.
2. Compute monthly Z500 anomalies and AR frequency per 10° band.
3. Perform correlation, FDR correction, and generate PNG maps (`figures/`).
4. Execute the threshold sensitivity sweep and produce `sensitivity_summary.csv`.
5. Validate against PNA/NAO indices and write `validation_*.json`.
6. Log runtime & memory usage in `logs/performance.yaml`.
7. Package everything into `artifacts/analysis_bundle.zip`.

## Inspect Results

```bash
# List generated artefacts
ls -R artifacts/ figures/ data/processed/

# View a sample map
display figures/corr_map_30-40N_DJF.png # on Linux/macOS with ImageMagick
```

## Re‑run a Sub‑set (e.g., only sensitivity analysis)

```bash
python -m src.cli.run_analysis --phase 6 # executes only phase 6 (sensitivity)
```

## Testing

```bash
pytest -q
# To also check contract compliance:
pytest tests/contract/test_correlation_schema.py
```

All tests must pass and the performance log must show `<6h` runtime and `<7GB` peak RAM for the full pipeline.

---
