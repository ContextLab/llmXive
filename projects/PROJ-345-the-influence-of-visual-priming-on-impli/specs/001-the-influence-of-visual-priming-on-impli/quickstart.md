# Quickstart: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## Prerequisites
- Python 3.11+, Git, internet access  
- ≤7 GB RAM, 2 CPU cores (GitHub Actions free tier or equivalent)

## Installation
```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
PIP_CONFIG_FILE=code/pip.conf pip install -r code/requirements.txt
```
`code/pip.conf` contains:
```
--extra-index-url https://download.pytorch.org/whl/cpu
```
ensuring the CPU‑only Torch wheel installs deterministically.

## Running the Full Pipeline
```bash
# 1) Ingest raw data (hard‑coded URL in code/config.py)
python code/main.py --step ingest

# 2) Preprocess, compute linkage metrics, and derive missing scores
python code/main.py --step preprocess

# 3) VIF check and LME fitting (includes optimizer fallback)
python code/main.py --step model

# 4) Generate the PDF report (always produced)
python code/main.py --step report

# One‑shot execution
python code/main.py --run-all
```

**Current expected behavior** (given the verified‑datasets audit):  
- `ingest` will halt with `Data Gap: Schema Mismatch` because the default dataset lacks `response_time`, `participant_id`, and `stimulus_id`.  
- `report` will still produce `reports/final_report.pdf` containing a clear data‑gap narrative.  

When a valid IAT dataset URL is added to `code/config.py` **and** to `data/verified_sources.json`, the pipeline will run end‑to‑end and produce the full scientific report.

## Expected Outputs
| Step | Files Produced |
|------|----------------|
| `ingest` | `data/raw/iat.parquet`, `state/artifact_hashes.json`, `code/logs/pipeline.log` |
| `preprocess` | `data/processed/metadata_mapping.csv`, `data/processed/ingest_metrics.json`, `state/linkage_status.json`, `data/processed/ambiguity_scores.csv`, `data/processed/valence_scores.csv`, `data/processed/linked_trials.csv`, `state/analysis_scope.json` |
| `model` | `state/vif_flag.json`, `state/model_results.json`, `state/model_convergence_metrics.json`, `state/fdr_results.json` |
| `report` | `reports/final_report.pdf`, `reports/interaction_plot.png`, `reports/sensitivity_analysis.csv`, `reports/pii_scan.json` |

## Verification Checklist
- `code/logs/pipeline.log` exists and contains timestamped entries for each executed step.  
- `pytest -m contract` passes all contract tests.  
- `reports/final_report.pdf` exists and contains either (a) the full analysis artifacts **or** (b) the data‑gap report.  
- If the post‑filter dataset size is below the a‑priori power target, the PDF includes a “Power Limitation” note (SC‑002).  

## Troubleshooting
| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `Data Gap: Schema Mismatch` at ingest | Default dataset lacks required columns (as audited) | Add a verified open IAT dataset URL to `code/config.py` **and** to `data/verified_sources.json`. |
| `Data Gap: Image files missing >10%` | Too many stimuli images missing from the source repository | Verify the stimulus repository; the pipeline will halt as required. |
| Model fails to converge | Severe collinearity or overly complex random‑effects structure | Check `state/vif_flag.json`; simplify the random effects or drop the interaction term as suggested in the log. |
| No `pipeline.log` file | CLI not yet executed or `PIP_CONFIG_FILE` not set during install | Run any `--step`; the first run creates the log file. |
| `torch` installs CUDA wheel | `pip.conf` not being read | Ensure `PIP_CONFIG_FILE=code/pip.conf` is set as shown in the Quickstart install command. |
| Streaming verification fails | Synthetic test file < 7 GB | The verification task (T014) automatically creates a >7 GB temporary Parquet file; ensure the runner has enough disk space. |

---
