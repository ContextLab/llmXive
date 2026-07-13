# Quickstart Guide

This document describes the commands required to run the full research pipeline
from raw data acquisition to final analysis artefacts.

## Prerequisites

* Python 3.11
* All dependencies installed via ``pip install -r requirements.txt``

## Execution steps

1. **Download a sample of the GitHub‑code corpus**
 ```bash
 python code/data_loader.py
 ```
 (The script is also invoked automatically by the main pipeline.)

2. **Run the complete pipeline** – this will generate the processed metrics
 and the correlation results required by the validation step.
 ```bash
 python code/main.py
 ```

3. **Validate the produced artefacts** – ensures that all expected files are
 present and non‑empty.
 ```bash
 python code/quickstart_validation.py
 ```

After step 2 finishes, you should find the following files on disk:

* `data/processed/clone_metrics.csv`
* `data/processed/perplexity_scores.csv`
* `data/analysis/correlation_results.csv`

These artefacts are used by downstream tasks and the integration tests.
