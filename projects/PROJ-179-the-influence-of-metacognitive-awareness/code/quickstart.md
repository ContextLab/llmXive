# Quickstart

This document describes how to run the full analysis pipeline from a fresh
checkout. All commands are intended to be executed from the repository
root.

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Run the end‑to‑end analysis

```bash
python code/analysis.py
```

The script will:

1. Verify that a raw behavioral dataset is available (or abort).
2. Download a small, publicly‑available dataset (Iris) and rename columns
 to match the project's schema.
3. Validate the downloaded data.
4. Preprocess the data into the required trial‑level format.
5. Execute correlation, bootstrap, regression, modality filtering, and
 robustness analyses.
6. Generate JSON reports under ``data/results``.

After successful execution you should find the following artefacts:

- `data/derived/trial_data.csv`
- `data/derived/visual_trials.csv`
- `data/derived/auditory_trials.csv`
- `data/results/bootstrap_config.json`
- `data/results/primary_analysis.json`
- `data/results/regression_analysis.json`
- `data/results/robustness_analysis.json`

## 3. Verify outputs (optional)

```bash
python -m unittest discover -s code/tests
```

This will run the project's unit and integration tests to confirm that
all artefacts were produced correctly.