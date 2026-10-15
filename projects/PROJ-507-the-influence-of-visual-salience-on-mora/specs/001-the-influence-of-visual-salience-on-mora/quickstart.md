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
# 0. Pilot power analysis (determines required N)
python code/00_pilot_power_analysis.py --config config/pilot.yaml

# 1. Ingest and filter (Phase 1)
python code/01_ingest_and_filter.py \
    --max-scenarios 30 \
    --output data/processed/candidates_filtered.csv

# 2. Simulated human coding (Phase 1)
python code/04_human_coding.py \
    --input data/processed/candidates_filtered.csv \
    --output data/processed/scenarios.csv

# 3. Generate salience variants (Phase 1)
python code/03_manipulate_stimuli.py \
    --input data/processed/scenarios.csv \
    --output data/processed/stimuli_manifest.csv

# 4. Deploy pilot survey (Phase 2)
python code/04_survey_deployment.py \
    --mode pilot \
    --participants 10 \
    --output data/processed/responses_raw.csv

# 5. Clean data (Phase 3)
python code/05_data_cleaning.py \
    --input data/processed/responses_raw.csv \
    --output data/processed/responses_cleaned.csv

# 6. Run analysis (Phase 4)
python code/06_analysis_clmm.py \
    --input data/processed/responses_cleaned.csv \
    --output data/processed/analysis_results.json
```

### GPU Off‑load (if needed)
The scripts automatically check `torch.cuda.is_available()`. If a timeout occurs, the CI runner will re‑execute the same command on a free Kaggle GPU (no code changes required).

## Validation Checklist
- **Stimulus Manifest**: `data/processed/stimuli_manifest.csv` must pass `contracts/stimulus.schema.yaml`.  
- **Responses**: `data/processed/responses_cleaned.csv` must pass `contracts/response.schema.yaml`.  
- **Analysis Output**: `data/processed/analysis_results.json` must pass `contracts/analysis_schema.yaml`.  

If any validation fails, re‑run the corresponding step; detailed logs are written to `logs/` (created automatically by the scripts).

## Troubleshooting
- **Memory errors**: Reduce `--max-scenarios` or the number of participants.  
- **CLIP/BERT timeout**: Add `--device cpu` to force CPU; the next CI run will automatically switch to Kaggle GPU.  
- **Model convergence warnings**: Check `analysis_results.json` for `fallback_method`; the script will have already applied the robust ordinal‑regression fallback.  

---

