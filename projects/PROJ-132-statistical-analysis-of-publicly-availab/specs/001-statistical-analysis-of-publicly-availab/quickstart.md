# Quickstart: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Prerequisites
- Python 3.11 or later
- `git`
- Access to a GitHub Actions runner **or** a local Linux/macOS machine with ≥ 7 GB RAM

## Installation
```bash
# Clone the repository
git clone https://github.com/your-org/PROJ-132-statistical-analysis-of-publicly-availab.git
cd PROJ-132-statistical-analysis-of-publicly-availab

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Configuration
Edit `src/config.py` if you wish to change defaults:
- `RANDOM_SEED` – reproducibility seed (default = 42)  
- `DATA_DIR` – root data folder (`data/` by default)  
- `GRID_RESOLUTION` – spatial resolution (fixed at 0.5° per constitution)  
- `MIN_OBSERVATIONS` – threshold for sufficient data (default = 5)

## Running the Full Pipeline
```bash
python src/cli/run_pipeline.py
```
The script executes the following stages in order:
1. **Validation & download** – **streams** eBird and PRISM datasets directly from the verified URLs; **no full raw files are persisted**, keeping disk usage well below the allocated storage limit.  
2. **Preprocessing** → `data/processed/phenology_climate.csv`.  
3. **GAMM fitting** → `data/output/gamm_results.csv`.  
4. **Trajectory & bootstrap** → `data/output/trajectory.json`.  
5. **Reporting** → `data/output/pipeline_report.json` plus figures under `data/output/figures/`.

### Expected Outputs
| File | Description |
|------|-------------|
| `data/processed/phenology_climate.csv` | Grid‑aligned phenology, effort covariates, and climate variables. |
| `data/output/gamm_results.csv` | Coefficients, p‑values, convergence status, Moran’s I, GP flag, temporal AR(1) indicator. |
| `data/output/trajectory.json` | Weekly centroids, shift vectors, block‑permutation p‑value, block‑bootstrap 95 % CI. |
| `data/output/pipeline_report.json` | Runtime, success‑criterion metrics (SC‑001 – SC‑005). |
| `data/output/figures/*.png` | Visualizations for the manuscript (phenology vs. temperature, route maps, residual diagnostics). |

## Testing
```bash
pytest tests/ -v
```
Unit tests cover data streaming, phenology calculation, effort weighting, model‑result schema validation, and block‑permutation correctness.

## Troubleshooting
- **Out‑of‑Memory** – The pipeline uses streaming; if OOM still occurs, reduce `MIN_OBSERVATIONS` or limit the species list in `src/config.py`.  
- **Lock Stale** – If `data/.pipeline.lock` persists after a crash, delete it manually: `rm data/.pipeline.lock`.  
- **Dataset Download Failure** – Verify that the URLs listed in `research.md` are reachable; the pipeline will abort with a clear error message if a checksum mismatch occurs.  
- **GPU Offload** – If the block‑bootstrap exceeds the CPU time budget, the runner will automatically re‑run that step on a Kaggle GPU. No manual intervention required.

---



## 8. Reproducibility Note
All steps are fully deterministic, use the same public URLs, and **do not write any raw eBird or PRISM files to disk**; only derived, version‑controlled artifacts are stored. This guarantees that the analysis can be reproduced on any fresh CI runner or local environment.
