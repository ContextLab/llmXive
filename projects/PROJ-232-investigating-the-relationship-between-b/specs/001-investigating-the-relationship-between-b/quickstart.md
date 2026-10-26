# Quickstart: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Prerequisites
- Python 3.10+  
- Adequate free disk space.  
- No GPU required (CPU‑first pipeline)

## Installation
```bash
git clone <repo-url>
cd projects/PROJ-232-investigating-the-relationship-between-b/code
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Pipeline
```bash
python src/main.py
```
The orchestrator performs the following steps:

1. **Download** all URLs listed in the Verified Datasets block and record SHA‑256 checksums.  
2. **Validation Gate** (`validate.py`).  
   - **Expected outcome (current state)**: required columns are missing, so `reports/data_gap_report.json` is written and the pipeline stops with a clear message.  
   - **If** a compliant dataset is placed manually (e.g., `data/subjects.parquet` matching `contracts/dataset.schema.yaml`), the pipeline proceeds to full analysis.  
3. **Full analysis** (when data are present): matrix reconstruction → graph‑metric extraction → PCA → partial correlations + Ridge CV → FDR → figures → `results/analysis_results.csv`.  

## Troubleshooting
| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `reports/data_gap_report.json` created | Verified sources lack required variables | This is the intended behavior; supply a compliant dataset or await spec amendment. |
| Download failure for a URL | Network issue or URL typo | The script logs the error and continues with remaining files; verify connectivity or URL correctness. |
| `MemoryError` | Attempting to load too many large matrices at once | The pipeline processes subjects sequentially; no batch flag needed. |
| Unexpected exit code from `src/main.py` | Validation gate failure or unhandled exception | Inspect `reports/data_gap_report.json` for missing variables; fix data source accordingly. |

---



