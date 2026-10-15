# Quickstart: Mindfulness Components and Delivery Formats in ASD Social Skills

## Prerequisites
- Python 3.11 or newer
- `git`  
- CPU‑only environment (≤ 7 GB RAM)

## Setup
```bash
# 1️⃣ Clone the repository
git clone <REPO_URL>
cd projects/PROJ-008-psychology-research

# 2️⃣ Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3️⃣ Install dependencies (pinned in requirements.txt)
pip install -r code/requirements.txt
```

## Run the Full Pipeline
```bash
# Step 1: Collect raw registry data
python code/data/collector.py \
    --output data/raw/registry_snapshot_$(date +%Y%m%d).json

# Step 2: Clean & tag studies
python code/data/cleaner.py \
    --input data/raw/registry_snapshot_*.json \
    --output data/processed/cleaned_studies.csv \
    --log data/raw/excluded_studies.log

# Step 3: Compute effect sizes
python code/analysis/effect_sizes.py \
    --input data/processed/cleaned_studies.csv \
    --output data/processed/effect_sizes.csv

# Step 4: Meta‑analysis & subgroup models
python code/analysis/meta_analysis.py \
    --input data/processed/effect_sizes.csv \
    --output data/results/meta_analysis.json \
    --plots-dir data/results/plots

# Step 5: Verify schemas & checksums
pytest tests/
```

## Expected Outputs
| Path | Description |
|------|-------------|
| `data/processed/cleaned_studies.csv` | Standardized study table (validated against `contracts/cleaned_study.schema.yaml`). |
| `data/processed/effect_sizes.csv` | Hedges’ g per study (validated against `contracts/effect_size.schema.yaml`). |
| `data/results/meta_analysis.json` | Pooled effect, heterogeneity, subgroup results. |
| `data/results/plots/forest.png` | Forest plot with study CIs and pooled diamond. |
| `data/results/plots/funnel.png` | Funnel plot (only if N ≥ 10). |
| `data/*.sha256` | SHA‑256 checksums for reproducibility (Principle III). |

## Troubleshooting
- **API Rate Limits**: The collector implements exponential backoff; if it still fails, re‑run the command – it will resume from the last successful page.  
- **No Included Studies**: Check `data/raw/excluded_studies.log` for reasons (e.g., age mismatch, missing outcome).  
- **N < 10**: The pipeline will automatically skip funnel plot/Egger’s test and produce a descriptive synthesis note in `meta_analysis.json`.  

---
