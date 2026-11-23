# Quickstart: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Prerequisites
- Python 3.11+  
- Git  
- (Optional) Kaggle account for GPU off‑load  

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-507-the-influence-of-visual-salience-on-mora

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

## End‑to‑End Run (CPU‑first)

```bash
# Phase 0 – Pilot power analysis
python code/00_pilot_power_analysis.py --config config/pilot.yaml

# Phase 1 – Data preparation
python code/01_ingest_and_filter.py \
    --max-scenarios 30 \
    --output data/processed/candidates_filtered.csv

python code/02_prepare_human_coding_dir.py   # creates data/raw/human_coding/

python code/03_process_human_coding.py \
    --input data/processed/candidates_filtered.csv \
    --output data/processed/scenarios.csv

python code/04_manipulate_stimuli.py \
    --input data/processed/scenarios.csv \
    --output data/processed/stimuli_manifest.csv

# Phase 2 – Survey deployment (pilot with a limited number of participants)
python code/05_survey_deployment.py \
    --mode pilot \
    --participants 10 \
    --output data/processed/responses_raw.csv

# Phase 3 – Data cleaning
python code/06_data_cleaning.py \
    --input data/processed/responses_raw.csv \
    --output data/processed/responses_cleaned.csv

# Phase 4 – Statistical analysis
python code/07_analysis_clmm.py \
    --input data/processed/responses_cleaned.csv \
    --output data/processed/analysis_results.json
```

### GPU Off‑load (if required)
The scripts automatically check `torch.cuda.is_available()`. If a heavy model (CLIP/BERT) times out on CPU, the CI runner will re‑run the same command on a free Kaggle GPU (`device="cuda"`). No code changes are needed.

## Validation Checklist
| Artifact | Contract Schema | Validation Command |
|----------|----------------|--------------------|
| `data/processed/stimuli_manifest.csv` | `contracts/stimulus.schema.yaml` | `python -m jsonschema -i data/processed/stimuli_manifest.csv contracts/stimulus.schema.yaml` |
| `data/processed/responses_cleaned.csv` | `contracts/response.schema.yaml` | `python -m jsonschema -i data/processed/responses_cleaned.csv contracts/response.schema.yaml` |
| `data/processed/analysis_results.json` | `contracts/analysis_schema.yaml` | `python -m jsonschema -i data/processed/analysis_results.json contracts/analysis_schema.yaml` |

If any validation fails, re‑run the corresponding phase; detailed logs are written to `logs/`.

## Troubleshooting
- **MemoryError**: Reduce `--max-scenarios` or the number of participants.  
- **CLIP/BERT timeout**: Add `--device cpu` to force CPU; the next CI run will automatically switch to Kaggle GPU.  
- **Model convergence warnings**: Check `analysis_results.json` for `fallback_method`; the script already applied the robust ordinal fallback.  

---


