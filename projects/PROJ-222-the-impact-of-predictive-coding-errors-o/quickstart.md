# Quickstart Guide

This guide walks you through reproducing the entire analysis pipeline for the project
"The Impact of Predictive Coding Errors on Subjective Time Perception".

## Prerequisites

- Python 3.10+
- 7 GB RAM available
- 6 hours maximum runtime
- Internet connection for data download

## Setup

1. Clone the repository and navigate to the project directory:
 ```bash
 cd PROJ-222-the-impact-of-predictive-coding-errors-o
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Execution

Run the following commands in sequence:

### Phase 0: Gate 0 - Data Validation

```bash
python code/gate0.py
```

This validates the pre-approved datasets in `data/README.md`. If no valid dataset is found,
the pipeline halts immediately.

### Phase 1: Data Download

```bash
python code/download.py
```

Downloads datasets from OpenML/HuggingFace based on IDs in `data/README.md`.
Gate 0 validation is performed automatically before downloading.

### Phase 2: Preprocessing

```bash
python code/preprocess.py
```

Filters datasets for sequential stimuli, computes Markov surprisal, and saves
`data/processed/preprocessed.csv`.

### Phase 3: T017 - Standardized Output Generation

```bash
python code/run_t017.py
```

Generates `data/processed/standardized.csv` with SHA256 checksums and verifies
that surprisal was derived using a first-order Markov model.

**Expected output:**
- `data/processed/standardized.csv` (>= 100 rows)
- `data/processed/standardized.csv.sha256` (checksum file)
- `data/processed/exclusion_log.json` (exclusion reasons)

### Phase 4: Analysis

```bash
python code/analysis.py
```

Fits linear mixed-effects models, calculates effect sizes, and performs sensitivity analysis.
Outputs are saved to `analysis/results.json`.

### Phase 5: Visualization

```bash
python code/visualize.py
```

Generates forest plots and residual diagnostic plots in `figures/`.

## Verification

After completing all steps, verify the following files exist:

- `data/processed/standardized.csv`
- `data/processed/standardized.csv.sha256`
- `data/processed/exclusion_log.json`
- `analysis/results.json`
- `figures/forest_plot.png`
- `figures/residual_diagnostics.png`

## Troubleshooting

- **Gate 0 fails**: Check `data/README.md` for valid dataset IDs
- **Download fails**: Verify internet connection and OpenML/HuggingFace access
- **Memory issues**: The pipeline uses chunked loading for large datasets
- **Convergence issues**: LMM fallback to random-intercept-only is automatic

## Runtime & Memory

- Expected runtime: < 6 hours
- Peak memory: < 7 GB RAM
- The pipeline logs timing and memory usage to stdout
