# The Impact of Visual Attention on Recall of Emotional Stimuli in Rapid Visual Sequences

**Project ID**: PROJ-484
**Branch**: main

This project investigates the relationship between visual attention metrics (fixation duration) and the recall of emotional stimuli in rapid visual sequences (RSVP), moderated by trait anxiety.

## Overview

- **Objective**: Determine if fixation duration on emotional stimuli predicts recall accuracy, and how this relationship is modulated by anxiety levels.
- **Methodology**: Analysis of RSVP eye-tracking data using mixed-effects logistic regression.
- **Data Source**: Publicly available eye-tracking datasets (e.g., from Hugging Face datasets repository).

## Structure

- `data/`: Raw and processed data files (excluded from version control).
- `code/`: Python scripts for data download, preprocessing, modeling, and visualization.
- `artifacts/`: Generated figures, logs, and model outputs.
- `specs/`: Research design documents and data contracts.
- `tests/`: Unit and integration tests.

## Setup

1. Clone the repository.
2. Create a virtual environment: `python3.11 -m venv code/venv`.
3. Install dependencies: `pip install -r code/requirements.txt`.
4. Run the pipeline: `python code/run_pipeline.py`.

## License

MIT License