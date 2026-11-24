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
# Install with CPU‑only Torch wheel
PIP_CONFIG_FILE=code/pip.conf pip install -r code/requirements.txt
```
`code/pip.conf` contains:
```
--extra-index-url https://download.pytorch.org/whl/cpu
```
This guarantees deterministic installation of `torch==2.3.0+cpu`.

## Running the Full Pipeline
```bash
# 1) Ingest raw data (hard‑coded URL in code/config.py, pointing to the verified OpenIAT dataset)
python code/main.py --step ingest

# 2) Preprocess, compute linkage metrics, and derive missing scores
python code/main.py --step preprocess

# 3) VIF check, derived‑score validation, power check, and confound diagnostics
python code/main.py --step checks   # runs T010, T020, T021, T022 sequentially

# 4) Model fitting (includes random intercept + random slope) and FDR correction
python code/main.py --step model

# 5) Generate the PDF report (always produced)
python code/main.py --step report

# One‑shot execution
python code/main.py --run-all
```

**Current expected behavior** (given the verified OpenIAT dataset):
- All required columns are present, so ingestion proceeds.
- If any validation metric falls below thresholds, the report will contain a clear caution note.
- If the post‑filter trial count is below the power target, the pipeline halts with a “Power Limitation” message in the PDF.
- `reports/final_report.pdf` is always generated, satisfying SC‑003.

When a different IAT dataset is needed, update `code/config.py` **and** `data/verified_sources.json` with the new URL, then re‑run the pipeline.

## Expected Outputs
| Step | Files Produced |
|------|----------------|
| `ingest` | `data/raw/iat.parquet`, `state/artifact_hashes.json`, `code/logs/pipeline.log` |
| `preprocess` | `data/processed/metadata_mapping.csv`, `data/processed/ingest_metrics.json`, `state/linkage_status.json`, `data/processed/ambiguity_scores.csv`, `data/processed/valence_scores.csv`, `data/processed/linked_trials.csv`, `state/analysis_scope.json` |
| `checks` | `state/vif_flag.json`, `state/score_validation.json`, `state/power_check.json`, `state/confound_check.json` |
| `model` | `state/model_results.json`, `state/model_convergence_metrics.json`, `state/fdr_results.json` |
| `report` | `reports/final_report.pdf`, `reports/interaction_plot.png`, `reports/sensitivity_analysis.csv`, `reports/pii_scan.json` |

## Verification Checklist
- `code/logs/pipeline.log` exists and contains timestamped entries for each executed step.  
- `pytest -m contract` passes all contract tests.  
- `reports/final_report.pdf` exists and contains either (a) the full analysis artifacts **or** (b) the data‑gap report (SC‑003).  
- If the post‑filter dataset size is below the a‑priori power target, the PDF includes a “Power Limitation” note (SC‑002).  

## Troubleshooting
| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `Data Gap: Schema Mismatch` at ingest | Dataset URL points to a file lacking required columns (should not happen with the verified OpenIAT source) | Verify `data/verified_sources.json` contains the correct OpenIAT entry; update `code/config.py` if needed. |
| `Data Gap: Image files missing >10%` | Too many stimulus images missing from the source repository | Verify the stimulus repository; the pipeline will halt as required. |
| Model fails to converge | Severe collinearity or overly complex random‑effects structure | Check `state/vif_flag.json`; if VIF > 5, consider simplifying the model. |
| Validation correlation < 0.6 | Derived scores may be noisy; the report will flag this. No code change needed. |
| No `pipeline.log` file | CLI not yet executed or `PIP_CONFIG_FILE` not set during install | Run any `--step`; the first run creates the log file. |
| `torch` installs CUDA wheel | `pip.conf` not being read | Ensure `PIP_CONFIG_FILE=code/pip.conf` is set as shown in the install command. |
| Streaming verification fails | Synthetic test file < 7 GB | The verification task (T017) automatically creates a >7 GB temporary Parquet file; ensure the runner has enough disk space. |

---

