# Quickstart: llmXive follow‑up Correlation Study

This guide walks a new contributor through setting up the environment and reproducing the full analysis on the GitHub Actions runner (or locally).

## Prerequisites
- Python 3.11 installed (or use the provided `setup.sh` which creates a virtualenv).
- `git` and internet access (to download the Edit‑Compass dataset).
- At least 7 GB free RAM and ~10 GB disk space.

## Setup Steps
```bash
# 1. Clone the repository (if not already)
git clone
cd llmxive-followup

# 2. Create a virtual environment and install pinned dependencies
python -m venv.venv
source.venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt # pins exact versions, CPU‑only

# 3. Verify the environment
python -c "import torch; assert not torch.cuda.is_available()"
```

## Run the Full Pipeline
```bash
# Execute the end‑to‑end pipeline (downloads, filtering, scoring, analysis)
python -m src.cli.main run_all
```
The command will:
1. Download `Edit‑Compass` (checksum verified).
2. Filter to the two target categories.
3. Compute logic & fidelity scores in batches (default batch size = 32).
4. Perform independence check, regression, and BH correction.
5. Write `outputs/report.md` and `outputs/regression_summary.json`.

## Inspect Results
```bash
# View the markdown report
cat outputs/report.md

# Load the regression JSON in Python (optional)
python - <<'PY'
import json, pprint
with open('outputs/regression_summary.json') as f:
 data = json.load(f)
pprint.pprint(data)
PY
```

## Running a Sub‑sample (CI Quick Check)
For CI speed, you can process only a subset of the filtered instances:
```bash
python -m src.cli.main run_all --max_instances 200
```
The same schema validation and reporting steps apply.

## Troubleshooting
- **Download fails**: The script exits with error code 1 and logs the missing URL. Verify network access.
- **VLM timeout**: Instances where the VLM does not return a description within 30 s are logged to `logs/vlm_timeout.log` and excluded.
- **Missing Human Score**: Rows lacking `human_judgment_score` are omitted; count reported at the end of the run.

All logs are written to `logs/` for reproducibility.

---
