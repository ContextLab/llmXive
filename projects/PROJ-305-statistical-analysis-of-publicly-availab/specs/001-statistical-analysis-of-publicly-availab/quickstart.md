# Quickstart: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Prerequisites
- Python 3.11+  
- Git (to clone the repository)  
- Access to a GitHub Actions runner **or** a local Linux/macOS environment with ≥ 7 GB RAM and ≥ 10 GB free disk space.

## Installation

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd <REPO_NAME>

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r src/requirements.txt
```

## Step‑by‑Step Execution

1. **Create directory tree & verification log**  
   ```bash
   python - <<'PY'
import pathlib, subprocess
pathlib.Path('logs').mkdir(exist_ok=True)
with open('logs/structure.txt', 'w') as f:
    subprocess.run(['tree', '-a', '-L', '3'], stdout=f)
PY
   ```
   *`logs/structure.txt` satisfies verification task T001.*

2. **Download the VAERS dataset**  
   ```bash
   python src/data/download.py
   ```
   - Downloads the verified full parquet from  
     `https://huggingface.co/datasets/vaers/vaers2020_2023/resolve/main/vaers_2020_2023.parquet`.  
   - Writes SHA‑256 checksum to `data/checksums.txt`.

3. **Validate the raw schema**  
   ```bash
   python src/data/validate.py
   ```
   - Exits with a clear error if any of `VAERS_ID`, `VAX_TYPE`, `SOC_CODE`, or `REPT_DATE` are absent (fulfills FR‑001 & SC‑004).

4. **Clean, map, and split the data**  
   ```bash
   python src/data/clean.py
   ```
   - Produces `data/processed/cleaned.parquet` with three groups (`COVID-19`, `Non-COVID‑Non‑Flu`, `Flu-only`).  
   - Validates the cleaned file against `contracts/cleaned_dataset.schema.yaml`.

5. **Run the full analysis pipeline**  
   ```bash
   python src/main.py
   ```
   This orchestrates:
   - Disproportionality calculations (`output/signals.csv`).  
   - Benjamini‑Hochberg correction.  
   - Signal flagging (2‑out‑of‑3 rule **plus** BH‑adjusted p‑value < 0.05 **and** hold‑out validation).  
   - Temporal profiling (canonical CSV files `output/temporal_profiles/<SOC>.csv`; optional PNG plots).  
   - Temporal‑bias robustness check (signals must survive spike‑week removal).  
   - Flu‑only sensitivity analysis (`output/sensitivity_analysis.csv`).  
   - Memory profiling and final `output/report.md`.

6. **Verify contracts**  
   ```bash
   pytest -q tests/contract/
   ```
   All JSON‑schema contracts must pass.

7. **Inspect results**  
   - `output/signals.csv` – table of ROR/PRR/IC with adjusted p‑values, hold‑out validation flag, and stability indicator.  
   - `output/temporal_profiles/` – CSV files for weekly counts (canonical) and optional PNG plots for the top signals.  
   - `output/sensitivity_analysis.csv` – Δ‑metrics vs. Flu baseline.  
   - `output/report.md` – human‑readable summary, memory usage, and limitations.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `E_SCHEMA_MISSING` from `validate.py` | Required columns absent in the downloaded parquet | Confirm the dataset URL; if missing, select a different verified VAERS parquet URL from the list. |
| MemoryError | Dataset larger than 7 GB RAM | Set `USE_CHUNKED=True` in `src/utils/config.py`; the pipeline will process the parquet in 500 k‑row chunks. |
| `logs/structure.txt` missing | Step 1 not executed or `tree` not installed | Install `tree` (`sudo apt-get install tree`) and re‑run step 1. |
| Plot functions raise `ImportError` | Placeholder code in `src/utils/plots.py` not replaced | Ensure the full implementation of `plot_weekly_counts` is present (provided in the repository). |
| Lint failures (`ruff` exit 1) | Style violations | Run `ruff check src/` locally, fix reported issues, then re‑run the lint script. |

## Next Steps
- Review `output/report.md` and incorporate the findings into the manuscript (`paper/`).  
- Run the full test suite (`pytest -q`) to ensure ongoing compliance.  
- To experiment with a larger VAERS archive, replace the download URL with the full dataset identifier; the same pipeline will handle it provided memory constraints are respected.

---

