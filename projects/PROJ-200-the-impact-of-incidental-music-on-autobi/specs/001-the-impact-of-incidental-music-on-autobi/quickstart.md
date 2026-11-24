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

## Preparing Input Data
1. **Million Song Dataset (MSD)** – will be streamed automatically; no manual step required.  
2. **Autobiographical Memory Test (AMT)** – not in the verified list, so you must provide it yourself: place a file named `amt.parquet` in `data/raw/` that conforms to `contracts/user_track_pair.schema.yaml`. If you do not have such a file, the pipeline will abort with a clear instruction.

## Running the Full Pipeline
```bash
# One‑command end‑to‑end execution
python code/main.py --full-run
```
The command executes all verified steps in order, writes real files, and updates `state.yaml`.

## Individual Step Commands (for debugging)

| Step | Command |
|------|---------|
| Download MSD (stream) | `python code/main.py --step download` |
| Validate AMT file | `python code/main.py --step validate-amt` |
| Ingest & merge | `python code/main.py --step ingest` |
| Match (all thresholds) | `python code/main.py --step match` |
| Aggregate (all thresholds) | `python code/main.py --step aggregate` |
| Fit models (all thresholds) | `python code/main.py --step model` |
| Sensitivity summary | `python code/main.py --step sensitivity` |
| Permutation test (default threshold = 3) | `python code/main.py --step permutation` |
| Power analysis | `python code/main.py --step power` |
| Verify & update state | `python code/main.py --step verify` |

## Expected Outputs
- `data/raw/msd_*.jsonl` (streamed MSD shards) – **Note:** MSD lacks per‑user timestamps; a placeholder exposure metric will be used unless you supply an external listening‑history dataset.  
- `data/raw/amt.parquet` (user‑provided AMT file)  
- `data/processed/ingested_cohort.parquet`  
- `data/processed/matched_thr{n}.parquet` (five files)  
- `data/processed/user_track_pairs_thr{n}.parquet` (five files)  
- `data/final/regression_summary_thr{n}.csv` (five files)  
- `data/final/sensitivity_analysis.csv`  
- `data/final/permutation_results.csv`  
- `data/final/power_report.txt` (contains required N and post‑hoc power)  
- `data/final/plots/` (diagnostic PDFs/PNGs)  
- Updated `state.yaml` with SHA‑256 hashes.

## Troubleshooting
- **Missing AMT file**: The pipeline will stop with an explicit error; place a conforming `amt.parquet` in `data/raw/`.  
- **Low Match Rate**: If any threshold yields `< 0.80` match rate, a warning is logged but execution proceeds (SC‑004).  
- **Memory Errors**: Streaming is active automatically in `download.py`.  
- **Permutation Too Slow**: Use `--perm-iterations <N>` to reduce iterations; the reduced iteration count will be noted in `power_report.txt`.  
- **Checksum Mismatch**: Run `python code/main.py --step verify` to recompute and compare hashes; mismatches indicate corrupted artifacts.  

---

