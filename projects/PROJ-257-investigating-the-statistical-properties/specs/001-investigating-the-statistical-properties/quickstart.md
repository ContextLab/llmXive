# Quickstart: Statistical Properties of Simulated Black Hole Mergers

## Prerequisites
- Python 3.11+  
- Git  
- Access to a GitHub Actions free‑tier runner (or equivalent local environment)

## Installation
```bash
git clone <repo-url>
cd <repo>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Full Pipeline
```bash
python -m src.main               # Executes all phases in order
```

### Optional Flags
| Flag | Description |
|------|-------------|
| `--download-only` | Perform only the download & checksum steps (T001, T002). Abort on failure. |
| `--skip-download` | Assume raw GWTC and simulation files already exist in `data/raw/`. |
| `--seed <int>` | Override the pinned random seed (debugging only). |
| `--samples-per-event <int>` | Number of posterior draws per GWTC event (default = 500). |
| `--bootstrap-iterations <int>` | Hierarchical bootstrap repetitions for KS p‑value (default = 1000). |
| `--mc-power-iterations <int>` | Monte‑Carlo power‑analysis iterations (default = 500). |
| `--measure-performance` | Record runtime, peak memory, and disk usage (writes `performance_metrics.json`). |
| `--use-analytic-efficiency` | Force use of the analytic detection‑efficiency model even if official curves are present. |
| `--require-simulation` | **Abort** if official IllustrisTNG/EAGLE simulation data cannot be downloaded or lacks required fields (enforces Constitution Principle VI). |
| `--alpha-sweep-start 0.01 --alpha-sweep-end 0.10 --alpha-sweep-step 0.01` | Customize the sensitivity‑analysis α range (default 0.01–0.10). |
| `--skip-power-analysis` | Skip the optional Monte‑Carlo power analysis (useful for tight CI budgets). |

## Expected Outputs
- `data/results/data_availability.json` – download status; pipeline aborts if any source is `"unavailable"` (or checksum verification fails).  
- `data/processed/obs_catalog.csv` – observational point‑estimate catalog (≥ 100 valid rows).  
- `data/processed/sim_catalog.csv` – official simulation catalog (must meet schema; otherwise pipeline aborts).  
- `data/processed/selection_weights.csv` – inverse‑probability weights.  
- `data/results/ks_results.json` – weighted KS statistics, Bonferroni‑adjusted p‑values, sensitivity flags, Monte‑Carlo MDES (deferred), power‑limitation note.  
- `performance_metrics.json` – runtime, peak memory, peak disk (if `--measure-performance`).  
- `outputs/figures/*.png` – ≥2 KDE plots with divergence shading, PNG ≥300 DPI.  
- `data/results/final_report.md` – summary, tables, figures, performance metrics, and “Limitations” section.

## Verification
```bash
pytest tests/contract
```
Contract tests validate every artifact against the schemas in `specs/.../contracts/`.

## Troubleshooting
- **Download failures**: three exponential‑backoff retries (starting at a short interval and doubling each subsequent wait). Persistent failure aborts with an explicit message in `data_availability.json`.  
- **Insufficient observational events**: if < 100 valid rows remain after filtering, the run aborts with error code 1.  
- **Simulation data missing**: if the official releases cannot be fetched or lack required fields, the pipeline aborts with a clear limitation note (see SC‑007).  
- **Memory pressure**: the pipeline processes ≤ 500 rows; if OOM occurs, reduce `--bootstrap-iterations` or `--mc-power-iterations`.  

--- 
