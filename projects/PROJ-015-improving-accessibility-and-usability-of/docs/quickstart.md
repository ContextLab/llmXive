# Quickstart Guide

## Running the Analysis Pipeline

To execute the full analysis pipeline, run the following command from the project root:

```bash
python code/analysis.py --input data/raw --output data/processed --mode full
```

### Options
- `--input`: Directory containing raw session data (default: `data/raw`)
- `--output`: Directory for processed results (default: `data/processed`)
- `--mode`: Analysis mode (`full`, `pilot`, or `dev`). Use `pilot` for small-scale validation.
- `--dev-mode`: (Optional) Allow simulated data for development testing.

### Example: Pilot Study
```bash
python code/analysis.py --input data/raw --output data/processed --mode pilot
```

### Example: Full Analysis with Real Data
```bash
python code/analysis.py --input data/raw --output data/processed --mode full
```

**Note**: The script `code/analysis.py` is a wrapper that invokes the core logic defined in `code/analysis/run_analysis.py`. Ensure `data/raw` contains valid session data matching `contracts/session.schema.yaml` before running in `full` mode.