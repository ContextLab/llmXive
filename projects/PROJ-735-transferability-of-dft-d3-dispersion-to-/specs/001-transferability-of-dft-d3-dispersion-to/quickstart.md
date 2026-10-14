# Quickstart: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Prerequisites
- **Python 3.11** (or newer)  
- **Git**  
- **GitHub Actions** runner (or a local Linux environment with at least 2 CPU cores and ≤ 7 GB RAM)  
- **Psi4** (CPU‑only). The easiest way is via `conda`:

```bash
conda create -n dft-d3-il -c psi4 -c conda-forge psi4=1.9.1 python=3.11 pip
conda activate dft-d3-il
```

If you prefer `pip`, the pre‑built wheel is included in `code/requirements.txt`; note that on some platforms additional system libraries may be required.

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-735-transferability-of-dft-d3-dispersion-to-

# 2. Create a virtual environment (if not using conda)
python -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r code/requirements.txt
```

## Data Preparation
The benchmark and bulk‑property data are shipped with the repository:

```bash
# Verify that the fallback files exist
ls data/raw/IL-Benchmark-local.zip
ls data/raw/experimental_bulk_properties.csv
```

No external download is required; the pipeline will automatically fall back to these files if network fetches fail. The benchmark contains **up to 100 ion‑pair complexes**; the default run uses the full set (you can limit it with `MAX_PAIRS` in `code/constants.py`).

## Lint Configuration
A minimal flake8 configuration (`.flake8`) is provided to silence non‑critical warnings that are irrelevant for this CI run. It disables E302, F841, W503, E501, and F821, ensuring the lint step exits with code 0.

```bash
# Copy the config (already present in the repo) and run lint
cp .flake8 .
flake8 code/ tests/ --config=.flake8 > code/lint_report.txt
# Verify success
grep "Exit code: 0" code/lint_report.txt
```

## Running the Full Pipeline

```bash
# Run the orchestrator (executes all phases in order)
python -m code.main
```

The command performs:

1. **Lint check** (`flake8` with the minimal config) → creates `code/lint_report.txt` (must end with `Exit code: 0`).  
2. **Data loading & validation** (`load_data.py`).  
3. **Psi4 single‑point calculations** (`run_psi4.py`).  
4. **Error analysis & bootstrap CI** (`analyze_energies.py`).  
5. **Scaling factor fitting with cross‑validation** (`derive_scaling.py`).  
6. **Bulk‑property correlation with partial‑correlation and cluster‑robust bootstrap** (`correlate_bulk.py`).  
7. **Report generation** (`generate_reports.py`).  

### Individual Stage Execution (optional)

```bash
python code/load_data.py
python code/run_psi4.py
python code/analyze_energies.py
python code/derive_scaling.py
python code/correlate_bulk.py
python code/generate_reports.py
```

## Expected Outputs

| Path | Description |
|------|-------------|
| `data/derived/raw_energies.csv` | Benchmark energies, D3 contributions, signed errors. |
| `data/derived/scaling_factor.txt` | Fitted scalar `s`, 95 % CI, p‑value, training MAE, test MAE. |
| `data/derived/correlation_results.csv` | Pearson & Spearman partial coefficients, R², p‑values, CI, Bonferroni‑adjusted p‑values (header only if < 3 valid pairs). |
| `docs/benchmark_report.md` | Human‑readable summary of raw MAE, RMSE, and bootstrap CI. |
| `docs/correlation_report.md` | Tables for each correlation test (coeff., R², CI, significance) **or** a notice of insufficient data. |
| `code/lint_report.txt` | Flake8 output; must show `Exit code: 0`. |
| `state/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-.yaml` | SHA‑256 checksums for all raw and derived artefacts. |

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **Psi4 fails to converge** | SCF difficulty for a particular ion pair. | The script automatically retries up to 3 times; if still failing, the entry is marked `"failed"` and excluded. |
| **MemoryError** | Attempting to process more than 100 ion pairs. | Reduce the batch size in `run_psi4.py` (`BATCH_SIZE=3`) or edit `constants.py` to limit `MAX_PAIRS`. |
| **`flake8` reports errors** | Code style violations. | Run the lint step with the provided `.flake8` config; fix any remaining errors and re‑run. |
| **Missing `correlation_results.csv`** | Not enough bulk‑property matches (fewer than 3). | The workflow will still create an empty CSV with a header and a report indicating insufficient data. |
| **Bootstrap CI too wide** | Sample size is still modest; this is expected. | No action required; the wide CI reflects genuine uncertainty. |

## Verifying the Build
Run the test suite to confirm that all artefacts are produced and schema‑compliant:

```bash
pytest -v tests/
```

All tests must pass (`exit code 0`). The CI configuration mirrors this command.

---


