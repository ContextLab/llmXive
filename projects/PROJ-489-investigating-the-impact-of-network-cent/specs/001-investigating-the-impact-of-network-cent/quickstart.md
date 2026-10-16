# Quickstart: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Prerequisites
- Python 3.11 or newer
- Internet access (to download the dataset)
- 2 CPU cores, ≤ 7 GB RAM (standard GitHub Actions runner)

## Installation
```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd specs/001-network-centrality-sleep-synchrony

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline
```bash
# 1️⃣ Download and verify the dataset (FR‑001)
python code/download.py

# 2️⃣ Preprocess EEG (filter, ICA, epoch) (FR‑002)
python code/main.py --stage preprocess

# 3️⃣ Build waking connectivity & centrality (FR‑003, FR‑004)
python code/main.py --stage connectivity
python code/main.py --stage centrality

# 4️⃣ Compute sleep‑stage PLI (FR‑005)
python code/main.py --stage pli

# 5️⃣ Aggregate metrics into SubjectMetrics.csv (new step)
python code/main.py --stage aggregate

# 6️⃣ Global VIF diagnostics across subjects (FR‑009)
python code/main.py --stage vif

# 7️⃣ Validate aggregated metrics file against schema
python code/validate.py

# 8️⃣ Statistical analysis with covariate adjustment (FR‑006‑FR‑012)
python code/main.py --stage analysis

# 9️⃣ Generate final report (FR‑008, FR‑011)
python code/main.py --stage report
```

Each stage writes its output under `data/` and logs progress to `logs/pipeline.log`. After the final step, you will find:
- `data/metrics/SubjectMetrics.csv` – one row per subject per sleep stage.  
- `data/results/analysis_results.json` – all correlation statistics.  
- `report.md` – human‑readable summary with tables, VIF diagnostics, and limitation notes.

## Verification
- **Schema validation**: `pytest tests/unit/test_schema_validation.py` checks that `SubjectMetrics.csv` conforms to `contracts/dataset.schema.yaml` and that `analysis_results.json` conforms to `contracts/analysis.schema.yaml`.  
- **Unit tests**: `pytest tests/unit/` must all pass (`exit code 0`).  
- **Integration test**: `pytest tests/integration/test_pipeline.py` runs the pipeline on a 3‑subject subset and checks that the final JSON contains the expected keys.

If any test fails, examine `logs/pipeline.log` for detailed error messages.
