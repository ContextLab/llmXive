# Quickstart: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## Prerequisites
- Python 3.11+, Git, internet access
- ≤7 GB RAM, 2 CPU cores (GitHub Actions free tier or equivalent)

## Installation

```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
PIP_CONFIG_FILE=code/pip.conf pip install -r code/requirements.txt
```
`code/pip.conf` contains `--extra-index-url https://download.pytorch.org/whl/cpu` so the CPU-only `torch` wheel installs deterministically.

## Running the Full Pipeline

```bash
# 1) Ingest raw data (hardcoded verified URL in code/config.py)
python code/main.py --step ingest

# 2) Preprocess, linkage gate, derive missing scores
python code/main.py --step preprocess

# 3) VIF pre-check + LME fit with optimizer fallback
python code/main.py --step model

# 4) PDF report (always produced, even on data-gap halt)
python code/main.py --step report

# One-shot
python code/main.py --run-all
```

**Expected current behavior**: given the dataset-variable audit (research.md §2), the `ingest` step halts at core-column validation with `Data Gap: Schema Mismatch`, and `report` produces `reports/final_report.pdf` containing the data-gap report. When a valid IAT dataset URL is supplied in `code/config.py` (`PRIMARY_DATASET_URL`) and added to `data/verified_sources.json`, the full analysis runs end-to-end.

## Expected Outputs

| Step | File(s) |
|------|---------|
| `ingest` | `data/raw/iat.parquet`, `state/artifact_hashes.json`, `code/logs/pipeline.log` (created by this first CLI run) |
| `preprocess` | `data/processed/ingest_metrics.json`, `metadata_mapping.csv`, `linked_trials.csv`, `state/linkage_status.json`, `state/analysis_scope.json` |
| `model` | `state/vif_flag.json`, `state/model_results.json`, `state/model_convergence_metrics.json` |
| `report` | `reports/final_report.pdf`, `reports/interaction_plot.png`, `reports/sensitivity_analysis.csv`, `reports/pii_scan.json` |

## Verification Checklist
- `code/logs/pipeline.log` contains timestamped entries from each executed step (verify by running `python code/main.py --step ingest` and checking the file exists and is non-empty).
- `pytest -m contract` passes all JSON/YAML contract validations.
- `reports/final_report.pdf` exists and contains either (a) interaction plot, coefficient table, sensitivity summary, caution/limitation notes (SC-003, full run), or (b) the data-gap report (halt path).
- Power-limitation note present if the post-filter dataset is below the a-priori target.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---|---|---|
| `Data Gap: Schema Mismatch` at ingest | Verified dataset lacks `response_time`/`participant_id`/`stimulus_id` (current state) | Supply a verified open IAT dataset URL in `code/config.py` + `data/verified_sources.json`; scope revision flagged in plan.md |
| `Data Gap: Image files missing for >10% of trials` | Source missing many stimulus files | Pipeline halts as required (US-1); verify the stimulus repository |
| Model convergence failure | Complex random effects or collinearity | Check `state/vif_flag.json`; pipeline already retries 3 optimizers and suggests simplifying random effects |
| Missing `pipeline.log` | CLI not yet executed | Run any `--step`; logging configures on first run |
| `torch` installs CUDA build | `pip.conf` not picked up | Set `PIP_CONFIG_FILE=code/pip.conf` explicitly |
