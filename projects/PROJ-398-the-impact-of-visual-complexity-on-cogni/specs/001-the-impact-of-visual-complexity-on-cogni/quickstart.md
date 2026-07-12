# Quickstart: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local CPU environment)

## Installation

1. **Clone and Setup**:
   ```bash
   git checkout 001-visual-complexity-cognitive-load
   cd projects/PROJ-398-the-impact-of-visual-complexity-on-cogni/code/
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Verify Dependencies**:
   Ensure `ultralytics` (YOLOv8n) and `statsmodels` are installed.
   ```bash
   python -c "import ultralytics; import statsmodels; print('OK')"
   ```

## Running the Pipeline

### Step 1: Generate/Prepare Stimuli (if not present)
If `data/stimuli/` is empty, place a set of background images there.
```bash
# Example: Download sample images (replace with actual source)
# mkdir -p ../../data/stimuli
# cp /path/to/public/images/*.jpg ../../data/stimuli/
```

### Step 2: Extract Visual Metrics (FR-001)
Run the CPU-compatible metric extraction.
```bash
python -m metrics.extract_visual --input ../../data/stimuli --output ../../data/processed/stimulus_metrics.json
```
*Expected*: JSON file with `entropy`, `color_variance`, `object_count` for each image.

### Step 3: Run Pilot Study (US-0)
Start the Streamlit app for human ratings.
```bash
streamlit run study/app.py -- --mode pilot
```
*Action*: Recruit a cohort of participants to rate images 1-10.
*Output*: `data/raw/pilot_ratings.json`.

### Step 4: Validate Pilot Metrics (FR-006)
Check correlation between human ratings and automated metrics.
```bash
python -m metrics.validate_pilot --ratings ../../data/raw/pilot_ratings.json --metrics ../../data/processed/stimulus_metrics.json
```
*Success*: Correlation $r > 0.5$. If not, flag for review.

### Step 5: Run Main Study (US-2)
Start the main experiment interface.
```bash
streamlit run study/app.py -- --mode main
```
*Action*: Participants view clips, complete NASA-TLX and RT tasks.
*Output*: `data/raw/participant_logs/*.json`.

### Step 6: Statistical Analysis (US-3)
Run the full analysis pipeline.
```bash
python -m analysis.models --input ../../data/processed/analysis_dataset.parquet --output ../../data/analysis/model_results.json
```
*Includes*: LMM, VIF check, Benjamini-Hochberg correction, Sensitivity Analysis.

### Step 7: Null Simulation (FR-007)
Validate the pipeline with synthetic data.
```bash
python -m utils.synthetic_data --run_null_sim --output ../../data/analysis/null_sim_results.json
```
*Success*: Observed FWER $\approx$ 0.05.

## Testing

Run the contract tests:
```bash
pytest tests/contract/ -v
```

## Troubleshooting

- **YOLOv8n too slow?** Ensure you are not accidentally loading a GPU model. Check `ultralytics` logs for `device='cpu'`.
- **Memory Error?** Reduce the batch size in `extract_visual.py`.
- **Missing Data?** The pipeline flags records with missing NASA-TLX or RT for exclusion (do not impute).
