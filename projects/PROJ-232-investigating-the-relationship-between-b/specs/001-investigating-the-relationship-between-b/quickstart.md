# Quickstart: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Prerequisites
- Python 3.10+
- ~2 GB free disk
- No GPU required

## Installation
```bash
git clone <repo-url>
cd projects/PROJ-232-investigating-the-relationship-between-b/code
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Run the pipeline
```bash
python src/main.py
```
The orchestrator:
1. **Downloads** the verified URLs and records SHA‑256 checksums.
2. **Runs the validation gate**. **Expected current outcome**: the files do not contain the required variables (`subject_id`, `age`, `sex`, `fd_mean`, `fc_upper_tri`, MER score), so `reports/data_gap_report.json` is written and the primary analysis halts with a clear message. This is the correct, honest behavior — no data is fabricated.
3. If a conformant dataset is supplied (e.g., authorized HCP access placed at `data/subjects.parquet` matching `contracts/dataset.schema.yaml`), the same command runs the full analysis: connectivity reconstruction → graph metrics → PCA → partial correlations + Ridge CV with FDR → figures and `results/analysis_results.csv`.

## Troubleshooting
| Symptom | Cause | Remedy |
|---|---|---|
| `reports/data_gap_report.json` written | Verified sources lack required variables | Expected; see **Data‑Gap Report** for details. |
| Download failure for one URL | Network/URL issue | Script logs and continues with remaining files (per edge‑case spec). |
| `MemoryError` | Loading too many matrices at once | Process subjects in batches (the pipeline processes subjects sequentially; no batch flag is needed). |

