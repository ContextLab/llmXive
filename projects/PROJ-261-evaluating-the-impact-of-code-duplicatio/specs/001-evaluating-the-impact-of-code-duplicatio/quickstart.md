# Quickstart Guide

This document outlines the steps required to run the full analysis pipeline
for the *Evaluating the Impact of Code Duplication on LLM Code Understanding*
project.

## Prerequisites

* Python 3.11
* All dependencies installed via `pip install -r requirements.txt`

## Execution Steps

1. **Download a sample of the GitHub code corpus**

 ```bash
 python -m code.data_loader
 ```

2. **Run the full pipeline**

 ```bash
 python code/main.py
 ```

The pipeline will:
* Stream the dataset (if not already present) and write `data/raw/github-code-sample.csv`.
* Scan for PII (handled internally).
* Compute clone density and write `data/processed/clone_metrics.csv`.
* Load the language model, compute perplexity scores, and write the corresponding CSV.
* Perform downstream analysis, generate figures, and produce checksum manifests.

## Validation

After the pipeline finishes, you can run the validation suite:

```bash
pytest -q
```

This will verify that all expected artefacts are present and conform to the
contract schemas defined in `specs/001-evaluate-code-duplication-llm-understanding/contracts/`.

## Notes

* The data download is performed in streaming mode; only a small subset
 (default 1 000 rows) is materialised to keep runtime modest.
* Subsequent runs are fast because the CSV artefact is cached; delete
 `data/raw/github-code-sample.csv` to force a fresh download.