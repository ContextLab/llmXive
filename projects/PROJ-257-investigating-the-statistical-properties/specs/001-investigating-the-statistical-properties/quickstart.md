# Quickstart: Statistical Properties of Simulated Black Hole Mergers

## Prerequisites
- Python 3.11+  
- Git  
- `git`‑available CI runner (GitHub Actions free tier)

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
python -m src.main               # executes all phases
```

### Optional Flags
| Flag | Description |
|------|-------------|
| `--download-only` | Only perform T001/T002/T004 (download & checksum). Pipeline aborts on failure. |
| `--skip-download` | Assume raw GWTC and simulation files already exist in `data/raw/`. |
| `--seed <int>` | Override the pinned random seed (debugging only). |
| `--samples-per-event <int>` | Number of posterior draws per GWTC event (default = 100). |
| `--bootstrap-iterations <int>` | Hierarchical bootstrap repetitions for KS p‑value (default = 1000). |
| `--mc-power-iterations <int>` | Monte‑Carlo power‑analysis iterations (default = 500). |
| `--measure-performance` | Record runtime, peak memory, and disk usage (writes `performance_metrics.json`). |
| `--efficiency-model` | Force use of the analytic detection‑efficiency model (fallback) even if curves are available. |

## Expected Outputs
- `data/results/data_availability.json` – download status (pipeline aborts if any source is `unavailable`).  
- `data/processed/obs_catalog.csv` – observational point‑estimate catalog (≥ 100 valid events).  
- `data/processed/sim_catalog.csv` – **derived BBH catalog from IllustrisTNG/EAGLE releases** (or aborts if releases unavailable).  
- `data/processed/selection_weights.csv` – event‑level weights.  
- `data/results/ks_results.json` – KS statistics, joint Energy‑distance, Bonferroni‑adjusted p‑values, sensitivity flags, Monte‑Carlo MDES, power‑limitation note.  
- `performance_metrics.json` – runtime, peak memory, peak disk usage (if `--measure-performance`).  
- `outputs/figures/*.png` – ≥300 DPI KDE and joint density plots with divergence shading.  
- `data/results/final_report.md` – summary, tables, figures, performance metrics, and “Limitations” section.

## Verification
```bash
pytest tests/contract
```
Contract tests validate every artifact against the schemas in `specs/.../contracts/`.

## Troubleshooting
- **Download failures**: three exponential‑backoff retries; persistent failure aborts with a clear message in `data_availability.json`.  
- **Memory pressure**: the pipeline processes < 500 rows; if you encounter OOM, reduce `--bootstrap-iterations` or `--mc-power-iterations`.  
- **Insufficient observational events**: if < 100 valid rows remain after filtering, the run aborts with error code 1.  

---



