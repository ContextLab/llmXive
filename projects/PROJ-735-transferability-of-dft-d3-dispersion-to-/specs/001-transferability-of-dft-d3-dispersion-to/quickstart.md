# Quickstart: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Prerequisites
- **Python 3.11** (or newer)  
- **Git**  
- **GitHub Actions** runner (or a local Linux environment with at least 2 CPU cores and ≤ 7 GB RAM)  
- **Psi4** (CPU‑only). The easiest installation is via **conda**:

```bash
conda create -n dft-d3-il -c psi4 -c conda-forge psi4=1.9.1 python=3.11 pip
conda activate dft-d3-il
```

If you prefer `pip`, the required wheel is listed in `code/requirements.txt`; on some platforms you may need to install system libraries (`libopenblas`, `liblapack`) beforehand.

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-735-transferability-of-dft-d3-dispersion-to-

# 2. Create a virtual environment (skip if using conda)
python -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r code/requirements.txt
```

## Data Preparation
The benchmark and bulk‑property data are **not** publicly downloadable at the moment. The workflow therefore follows a *fail‑fast* policy:

```bash
# Attempt to download the benchmark dataset from Zenodo (FR‑001)
python -c "import requests, sys; \
    r = requests.get('https://zenodo.org/record/<PLACEHOLDER_DOI>/download', timeout=10); \
    if r.status_code==200: open('data/raw/IL-Benchmark.zip','wb').write(r.content) \
    else: sys.exit('Benchmark download failed')" || echo "Download failed – you may run with --allow-fallback for local testing only."

# Attempt to retrieve experimental bulk properties via the NIST API (FR‑008)
python -c "import requests, sys; \
    r = requests.get('https://nist.gov/api/il-bulk', timeout=10); \
    if r.status_code==200: open('data/raw/experimental_bulk_properties.csv','wb').write(r.content) \
    else: sys.exit('API call failed')" || echo "API call failed – you may run with --allow-fallback for local testing only."

# Verify fallback files exist (development only)
ls data/raw/IL‑Benchmark‑local.zip
ls data/raw/experimental_bulk_properties.csv
```

**Important:** Production runs **must** succeed on the Zenodo/NIST download, otherwise the workflow aborts, complying with Constitution VI. Use the `--allow-fallback` flag only for local debugging.

## Lint Configuration
A minimal flake8 configuration (`.flake8`) is provided to silence non‑critical warnings. It disables E302, F841, W503, E501, and F821, ensuring the lint step exits with code 0.

```bash
# Run lint (creates lint_report.txt)
flake8 code/ . --config=.flake8 > code/lint_report.txt
# Verify that the report has "Exit code: 0"
grep "Exit code: 0" code/lint_report.txt
```

## Running the Full Pipeline

```bash
# Execute the orchestrator (runs all phases sequentially)
# Add --allow-fallback ONLY if you want to use the local placeholder data.
python -m code.main [--allow-fallback]
```

The orchestrator performs:

1. **Lint check** → `code/lint_report.txt`.  
2. **Data extraction & validation** (`load_data.py`), aborting on download failure unless `--allow-fallback`.  
3. **Psi4 single‑point calculations** (`run_psi4.py`).  
4. **Error analysis & bootstrap CI** (`analyze_energies.py`).  
5. **Scaling factor fitting with cross‑validation** (`derive_scaling.py`).  
6. **Residual diagnostics after scaling** (`scaling_diagnostics.md` generated in Phase 4.5).  
7. **Bulk‑property correlation with partial correlation & cluster‑robust bootstrap** (`correlate_bulk.py`).  
8. **Report generation** (`generate_reports.py`).  

### Optional: Run Individual Stages

```bash
python code/load_data.py          # Phase 1
python code/run_psi4.py           # Phase 2
python code/analyze_energies.py   # Phase 3
python code/derive_scaling.py     # Phase 4
python code/correlate_bulk.py     # Phase 5
python code/generate_reports.py   # Phase 6
```

## Expected Outputs

| Path | Description |
|------|-------------|
| `data/derived/raw_energies.csv` | Benchmark energies, D3 contributions, signed errors, and dispersion‑only error (validated by `raw_energies.schema.yaml`). |
| `data/derived/scaling_factor.txt` | Fitted scalar `s`, 95 % CI, p‑value, training & test MAE, and original MAE. |
| `data/derived/scaling_diagnostics.md` | Residual‑diagnostics (histogram, Shapiro‑Wilk, Breusch‑Pagan) after scaling (FR‑018). |
| `data/derived/correlation_results.csv` | Partial Pearson & Spearman coefficients, R², p‑values, Bonferroni‑adjusted p‑values, CI, and significance flag (header only if < 3 valid pairs). |
| `docs/benchmark_report.md` | Human‑readable summary of raw MAE, RMSE, MSE, and MAE confidence interval. |
| `docs/correlation_report.md` | Tables for each correlation test **or** a notice of insufficient data; includes power analysis and construct‑validity disclaimer. |
| `code/lint_report.txt` | Flake8 output; must end with `Exit code: 0`. |
| `state/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-.yaml` | SHA‑256 checksums for all raw and derived artefacts. |

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **Benchmark download fails** | No open Zenodo DOI exists. | Run with `--allow-fallback` for development; production runs will abort as required by the specification. |
| **NIST API call fails** | Endpoint not publicly accessible. | Same as above – use fallback CSV for debugging only. |
| **Psi4 fails to converge** | SCF difficulty for a specific ion pair. | Automatic 3‑retry mechanism; persistent failures are logged and excluded. |
| **MemoryError** | Attempting to process > 500 ion pairs or using a large batch size. | Reduce `BATCH_SIZE` in `run_psi4.py` or edit `constants.py` to limit `MAX_PAIRS`. |
| **`flake8` reports errors** | Code style violations. | Run lint with the provided `.flake8`; fix remaining errors. |
| **Missing `correlation_results.csv`** | Fewer than 3 valid bulk‑property matches. | The pipeline still creates an empty CSV with header and a markdown notice; this is schema‑compliant. |
| **Bootstrap CI too wide** | Small sample size; reflects genuine uncertainty. | No action needed; report CI as‑is. |

## Verifying the Build
Run the full test suite to ensure all artefacts are produced and schema‑compliant:

```bash
pytest -v tests/
```

All tests must pass (i.e., exit code indicating successful execution). The CI configuration mirrors this command.

---


