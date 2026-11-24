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
2. **Validation Gate** (`validate.py`) –  
   - **Expected outcome (current state)**: required columns are missing **and** the pipeline writes `reports/data_gap_report.json` then stops.  
   - **If** a compliant **open** dataset (matching the `contracts/dataset.schema.yaml` schema) **exists**, the pipeline will proceed to full analysis, including fMRIPrep preprocessing, graph‑theoretic metric computation, partial correlation, Ridge regression with cross‑validation, FDR correction, and figure generation.  
   - **If** the validation gate fails, the pipeline automatically runs a **simulated‑data validation** that executes the complete analysis workflow on synthetic connectivity matrices and MER scores, producing a proof‑of‑concept result set (`reports/simulated_validation.json`).  

3. **Resource‑Usage Report** (`reports/resource_usage.json`) summarizing peak RAM, total CPU time, and wall‑clock time is generated after the pipeline completes (or after the simulated‑data validation).  

*Note*: The pipeline is designed to run on the GitHub Actions free tier; all steps are CPU‑first and respect the 7 GB RAM / 6 h runtime limits.

---



