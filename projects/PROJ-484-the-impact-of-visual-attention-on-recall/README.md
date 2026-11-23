# The Impact of Visual Attention on Recall of Emotional Stimuli in Rapid Visual Sequences

**Project ID**: PROJ-484
**Branch Reference**: `main` (or relevant feature branch)

## Overview
This project investigates the relationship between visual attention metrics (specifically fixation duration), emotional valence of stimuli, and recall performance in rapid serial visual presentation (RSVP) tasks, with a focus on the moderating role of trait anxiety.

## Reproducibility Statement
This research pipeline is designed for full reproducibility. All data processing steps, including I-VT fixation extraction, stimulus mapping, and mixed-effects modeling, are implemented as deterministic scripts.

- **Data Source**: OpenNeuro dataset `ds001435` (verified).
- **Environment**: Python 3.11+ with dependencies pinned in `code/requirements.txt`.
- **Execution**: Run the full pipeline via `python code/run_pipeline.py`.
- **Artifacts**: All intermediate and final results are stored in `data/` and `artifacts/`.

## Directory Structure
- `code/`: Source code for data verification, preprocessing, modeling, and visualization.
- `data/raw/`: Raw downloaded datasets.
- `data/processed/`: Cleaned, analysis-ready CSVs.
- `artifacts/figures/`: Generated plots and visualizations.
- `artifacts/logs/`: Execution logs and diagnostic reports.
- `specs/`: Research design documents and schema contracts.

## Quick Start
1. Set up the virtual environment: `python -m venv code/venv && source code/venv/bin/activate`
2. Install dependencies: `pip install -r code/requirements.txt`
3. Run the pipeline: `python code/run_pipeline.py`

## License
Academic Research Use Only.