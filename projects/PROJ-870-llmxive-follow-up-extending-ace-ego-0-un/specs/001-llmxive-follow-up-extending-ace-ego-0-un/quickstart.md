# Quickstart: llmXive static‑proxy analysis

**Feature**: `001-llmxive-static-proxy`  
**Date**: 2026‑10‑22  

This guide shows how to run the entire research pipeline on a fresh GitHub Actions runner (or locally) using only CPU resources.

## Prerequisites
```bash
# Clone the repository (assumes you are in the project root)
git clone 
cd llmxive-project

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Commands

| Step | Command | Description |
|------|---------|-------------|
| 0️⃣ | `python src/cli/run_pipeline.py --stage download` | Downloads the EPIC‑KITCHENS dataset (verified) and the RoboCasa / RoboTwin benchmark archives. |
| 1️⃣ | `python src/cli/run_pipeline.py --stage extract-static` | Extracts static features from all video segments, writes `data/static_features.csv`. |
| 2️⃣ | `python src/cli/run_pipeline.py --stage train-static-model` | Trains the Random Forest regressor, outputs `models/static_rf.pkl`, `data/static_predictions.csv`, and `data/static_residuals.csv`. |
| 3️⃣ | `python src/cli/run_pipeline.py --stage augment-temporal` | Computes optical‑flow features for brief, 3 s, 5 s, and 10 s windows; produces CSVs `data/temporal_features_{w}s.csv`. |
| 4️⃣ | `python src/cli/run_pipeline.py --stage train-vla` | Trains the three VLA variants (dynamic, uniform, static‑proxy) on the appropriate training sets. |
| 5️⃣ | `python src/cli/run_pipeline.py --stage evaluate-vla` | Runs evaluation on RoboCasa and RoboTwin, writes `results/vla_*.csv`. |
| 6️⃣ | `python src/cli/run_pipeline.py --stage analyze` | Generates all tables, plots (`figures/`), and a markdown summary (`report/summary.md`). |
| 7️⃣ | `python src/cli/run_pipeline.py --stage validate-contracts` | Runs contract validation against `contracts/*.schema.yaml`. Fails if any CSV violates the schema. |

All steps accept `--seed <int>` to enforce reproducibility (default = 42). Example:

```bash
python src/cli/run_pipeline.py --stage train-static-model --seed 123
```

## Resource Usage
- **CPU**: ≤ 2 cores (default runner).  
- **RAM**: Peaks at ~5 GB during static extraction; stays < 6 GB thereafter.  
- **Runtime**: Entire pipeline finishes within 5 h on the free tier (including VLA training on 5 k segments).

## Troubleshooting
- **Missing EPIC‑KITCHENS‑100**: If the download stage reports “no verified source”, the pipeline will stop after the initial step and print instructions for scope revision.  
- **Out‑of‑memory**: The script automatically reduces frame sampling to 0.5 fps if RAM exceeds 6 GB.  
- **Contract failures**: Review `validation_errors.log` for details; fix the offending CSV column and re‑run the `validate-contracts` stage.

Happy research!  

---

