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
# One‑command end‑to‑end execution
python code/main.py --full-run
```
The command executes the verified steps in order, writes real files, and updates `state.yaml`.

## Individual Step Commands (for debugging)

| Step | Command |
|------|---------|
| Download raw datasets | `python code/main.py --step download` |
| Ingest & merge | `python code/main.py --step ingest` |
| Match (all thresholds) | `python code/main.py --step match` |
| Aggregate (all thresholds) | `python code/main.py --step aggregate` |
| Fit models (all thresholds) | `python code/main.py --step model` |
| Sensitivity summary | `python code/main.py --step sensitivity` |
| Permutation test (default threshold = 3) | `python code/main.py --step permutation` |
| Verify & update state | `python code/main.py --step verify` |

## Expected Outputs
- `data/raw/msd_*.jsonl` (streamed MSD shards) – **Note:** MSD does not contain per‑user listening timestamps; a placeholder exposure metric will be used unless an external listening‑history dataset is provided.  
- `data/raw/amt.jsonl` (AMT cues & ratings)  
- `data/processed/ingested_cohort.parquet`  
- `data/processed/matched_thr{n}.parquet` (multiple files)  
- `data/processed/user_track_pairs_thr{n}.parquet` (multiple files)  
- `data/final/regression_summary_thr{n}.csv` (several files)  
- `data/final/sensitivity_analysis.csv`  
- `data/final/permutation_results.csv`  
- `data/final/plots/` (diagnostic PDFs/PNGs)  
- Updated `state.yaml` with SHA‑256 hashes.

## Troubleshooting
- **Missing Birth Years**: If > 50 % of `birth_year` are null, the log will contain *“Global Exposure fallback triggered”*; the pipeline continues using the proxy only for sensitivity checks.  
- **Low Match Rate**: If any threshold yields `< 0.80` match rate, a warning is logged but execution proceeds (SC‑004).  
- **Memory Errors**: Ensure streaming is active (handled automatically in `download.py`).  
- **Permutation Too Slow**: Reduce the `--perm-iterations` flag; the pipeline will note the reduced power in `permutation_results.csv`.  
- **Checksum Mismatch**: Run `python code/main.py --step verify` to recompute and compare hashes; mismatches indicate corrupted artifacts.

---


