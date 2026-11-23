# Quickstart: Running the Visual Complexity ↔ Cognitive Load Pipeline

These instructions assume a fresh GitHub Actions runner or a local Linux/macOS environment with Python 3.11.

## 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-org/visual-complexity-cogload.git
cd visual-complexity-cogload
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins all versions
```

## 2. Generate Background Stimuli
```bash
python -m src.metrics.generate_stimuli --count <desired_number> --output data/stimuli/raw/
# Generates a set of PNGs and writes per‑image metadata to data/stimuli/metadata/frames.csv
```

## 3. Run Pilot Human Rating Collection (US‑0)
- Deploy the lightweight rating UI (Flask) locally or on a free hosting service.
- Collect a sufficient set of ratings, then download the CSV to `data/measurements/pilot_ratings.csv`.
- Validate metrics:
```bash
python -m src.metrics.validate --ratings data/measurements/pilot_ratings.csv \
    --metrics data/stimuli/metadata/frames.csv \
    --output data/derived/individual_metric_correlations.csv
```
- Inspect `individual_metric_correlations.csv`. If any Pearson r < 0.7, edit `src/metrics/compute.py` and repeat.

## 4. Full Participant Study (US‑2)
### 4.1 Recruit Participants
```bash
python -m src.experiment.recruit --n <target sample size> --platform prolific
# Generates a list of participant IDs saved under data/measurements/participants.json
```

### 4.2 Run Sessions (one participant at a time)
```bash
python -m src.experiment.run_session --participant-id <PID> \
    --stimuli-dir data/stimuli/raw/ \
    --output-dir data/measurements/participant_sessions/
```
- The script presents the baseline RT task, then each clip with a counterbalanced background, collects NASA‑TLX and post‑task RT, records a **familiarity_score** at the start of the session, and writes a JSON session file.

### 4.3 Aggregate & Flag Missing Data
```bash
python -m src.experiment.utils.aggregate_sessions \
    --input-dir data/measurements/participant_sessions/ \
    --output data/processed/metrics.csv
# Invalid or missing TLX/RT rows are excluded and logged; `rt_valid` flag set to false where appropriate.
```

## 5. Statistical Analysis (US‑3 & US‑4)
### 5.1 Pipeline Validation (Synthetic Data)
```bash
python -m src.analysis.null_simulation --synthetic-size [appropriate synthetic size]
    --output data/derived/null_simulation_report.json
```

### 5.2 Power Simulation (LMM)
```bash
python -m src.analysis.power_simulation --target-effect <desired_effect> --samples 5000 \
    --output data/metadata/power_report.json
```

### 5.3 Fit Linear Mixed‑Effects Model
```bash
python -m src.analysis.lmm --data data/processed/metrics.csv \
    --output data/derived/analysis_results.json
```

### 5.4 Sensitivity Sweep
```bash
python -m src.analysis.sensitivity --data data/processed/metrics.csv \
    --alphas 0.01 0.05 0.1 \
    --output data/derived/analysis_results.json   # updates the same file
```

## 6. Contract Validation
```bash
pytest -m test_schemas.py   # validates analysis_results.json against contracts/analysis_result.schema.yaml
```

## 7. Generate Report & Figures
```bash
python -m src.reporting.generate_report \
    --analysis data/derived/analysis_results.json \
    --output paper/report.md
```
Figures (scatter plots, VIF bar, sensitivity curves) are saved under `paper/figures/`.

## 8. Run Full CI Check (optional)
```bash
pytest -vv
# Includes contract validation, lint checks, and end‑to‑end pipeline test.
```

All steps are fully reproducible; re‑running from step 2 on a clean runner yields identical outputs (random seeds are fixed in `src/utils/io.py`).  
