# Quickstart: The Impact of Incidental Music on Autobiographical Memory Retrieval

## Prerequisites
- Python 3.11 or newer  
- `git`  

## Installation
```bash
# 1️⃣ Clone the repository
git clone <repo-url>
cd projects/PROJ-200-the-impact-of-incidental-music-on-autobi

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r requirements.txt
```

## Running the Full Pipeline
```bash
# One‑command end‑to‑end run
python code/main.py --full-run
```
The command executes the following verified steps (each writes a real file and updates `state.yaml`):
1. **Download** raw MSD JSONL files (`data/raw/`).  
2. **Simulate** AMT cues & ratings (`data/simulated_amt.parquet`).  
3. **Ingest** → `data/processed/ingested_cohort.parquet`.  
4. **Match** across thresholds → `matched_thr{n}.parquet`.  
5. **Aggregate** → `user_track_pairs_thr{n}.parquet`.  
6. **Model** → `regression_summary_thr{n}.csv`.  
7. **Sensitivity** → `sensitivity_analysis.csv`.  
8. **Permutation** → `permutation_results.csv` + diagnostic plots.  
9. **Verify** checksums and update `state.yaml`.

## Individual Step Commands (for debugging)

| Step | Command |
|------|---------|
| Download raw MSD | `python code/main.py --step download` |
| Simulate AMT | `python code/main.py --step simulate` |
| Ingest & merge | `python code/main.py --step ingest` |
| Match (all thresholds) | `python code/main.py --step match` |
| Aggregate (all thresholds) | `python code/main.py --step aggregate` |
| Fit models (all thresholds) | `python code/main.py --step model` |
| Sensitivity summary | `python code/main.py --step sensitivity` |
| Permutation test (default threshold = 3) | `python code/main.py --step permutation` |
| Verify & update state | `python code/main.py --step verify` |

## Expected Outputs
- `data/processed/ingested_cohort.parquet`  
- `data/processed/user_track_pairs_thr{n}.parquet` (multiple files)  
- `data/final/regression_summary_thr{n}.csv` (multiple files)  
- `data/final/sensitivity_analysis.csv`  
- `data/final/permutation_results.csv`  
- `data/final/plots/` (PDF/PNG diagnostics)  
- Updated `state.yaml` with SHA‑256 hashes.

## Troubleshooting
- **Missing Birth Years**: If > 50 % of `birth_year` are null, the log will contain *“Global Exposure fallback triggered”*; the pipeline continues using the proxy only for sensitivity.  
- **Low Match Rate**: If any threshold yields `< 0.80` match rate, a warning is logged but execution proceeds (SC‑004).  
- **Memory Errors**: Ensure `datasets` streaming is active (handled automatically in `download.py`).  
- **Permutation Too Slow**: Reduce `--perm-iterations` flag; the pipeline will note the reduced power.  
- **Checksum Mismatch**: Run `python code/main.py --step verify` to recompute and compare hashes.
