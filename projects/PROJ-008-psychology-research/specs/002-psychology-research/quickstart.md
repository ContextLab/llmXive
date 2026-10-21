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

# 3️⃣ Install pinned dependencies
pip install -r code/requirements.txt
```

## Run the Full Pipeline
```bash
# Step 1: Collect raw registry data and DOIs
python code/data/collector.py \
    --output data/raw/registry_snapshot_$(date +%Y%m%d).json

# Step 2: Supplement with PubMed article data for outcome statistics
python code/data/pubmed_fetcher.py \
    --registry data/raw/registry_snapshot_*.json \
    --output data/raw/pubmed_articles.json

# Step 3: Clean & tag studies (includes RoB2 extraction, DOI validation)
python code/data/cleaner.py \
    --input data/raw/registry_snapshot_*.json \
    --pubmed data/raw/pubmed_articles.json \
    --output data/processed/cleaned_studies.csv \
    --log data/raw/excluded_studies.log

# Step 4: Compute effect sizes (uses change scores when available)
python code/analysis/effect_sizes.py \
    --input data/processed/cleaned_studies.csv \
    --output data/processed/effect_sizes.csv

# Step 5: Meta‑analysis & subgroup models (REML + Hartung‑Knapp)
python code/analysis/meta_analysis.py \
    --input data/processed/effect_sizes.csv \
    --output data/results/meta_analysis.json \
    --plots-dir data/results/plots

# Step 6: Verify schemas & checksums
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
| `data/metadata/registry_log.json` | Registry query strings, timestamps, DOI validation status, and checksums. |
| `data/metadata/pubmed_log.json` | PubMed query logs and extracted outcome statistics. |
| `data/metadata/rob_log.json` | Risk‑of‑bias ratings per study. |

## Troubleshooting
- **API Rate Limits**: The collector implements exponential backoff; if it still fails, simply re‑run the command – it will resume from the last successful page.  
- **Missing Outcome Statistics**: Check `data/raw/excluded_studies.log` for reasons; the PubMed step often fills gaps.  
- **Abstract‑Only Tags**: Records flagged `abstract_only=True` are excluded from subgroup analyses; manually verify if needed.  
- **No Included Studies**: Review `data/raw/excluded_studies.log` for exclusion reasons (e.g., non‑RCT, no outcome, ambiguous delivery).  
- **N < 10**: The pipeline automatically skips funnel plot/Egger’s test and produces a descriptive synthesis note in `meta_analysis.json`.  

---


