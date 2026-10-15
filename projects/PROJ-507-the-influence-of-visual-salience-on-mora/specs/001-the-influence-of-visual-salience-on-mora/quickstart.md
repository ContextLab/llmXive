# Quickstart: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Prerequisites
- Python 3.11 or newer  
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

## Step‑by‑Step Run (CPU‑first)

```bash
# 0. Pilot power analysis (determines required N)
python code/00_pilot_power_analysis.py --config config/pilot.yaml

# 1. Ingest and filter raw images (Phase 1)
python code/01_ingest_and_filter.py \
    --dataset_name visual_genome \
    --tags conflict social \
    --max-scenarios 30 \
    --output data/processed/candidates_filtered.csv

# 2. Human coding simulation (Phase 1)
python code/02_human_coding.py \
    --input data/processed/candidates_filtered.csv \
    --config config/human_coding.yaml \
    --output data/processed/scenarios.csv

# 3. Generate salience variants (Phase 1)
python code/03_manipulate_stimuli.py \
    --input data/processed/scenarios.csv \
    --config config/manipulation.yaml \
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
    --config config/analysis.yaml \
    --output data/processed/analysis_results.json
```

### GPU Off‑load (if CLIP/BERT extraction exceeds CPU limits)

The scripts automatically detect `torch.cuda.is_available()`. If `False`, they raise `RuntimeError`. The CI runner catches this and re‑runs the same command on a free Kaggle GPU (the platform handles the off‑load). No code changes are required.

## Validation Checklist
- **Stimulus Integrity**: Verify `stimuli_manifest.csv` passes `contracts/stimulus.schema.yaml`.  
- **Response Schema**: `responses_cleaned.csv` validates against `contracts/response.schema.yaml`.  
- **Analysis Output**: `analysis_results.json` validates against `contracts/analysis_schema.yaml`.  

If any validation fails, re‑run the corresponding step; the scripts emit detailed logs.

## Troubleshooting
- **Memory errors**: Reduce `--max-scenarios` or sample a smaller pilot (`--num-samples`).  
- **CLIP/BERT timeout**: Set `--device cpu` to force CPU; the next CI run will automatically switch to Kaggle GPU.  
- **Convergence warnings**: Check `analysis_results.json` for `fallback_method`; the script will have already applied the robust alternative.
