# Quickstart Guide

This guide outlines the steps to run the full pipeline for the **Neural Correlates of Predictive Error Signals** project.

## Prerequisites

- Python 3.11+
- Virtual environment activated (`.venv`)
- Dependencies installed (`pip install -r requirements.txt`)

## Execution Steps

The pipeline is executed in stages. Each stage produces intermediate artifacts required by the next.

### 1. Data Ingestion
Fetches and validates the dataset.
```bash
python code/src/data/ingest.py
```
*Output*: `data/validation_report.json`, raw data files (processed in memory or temp)

### 2. Preprocessing
Filters, ICA, and epochs the data.
```bash
python code/src/data/preprocess.py
```
*Output*: `data/excluded_subjects.csv`, preprocessed epochs

### 3. Behavioral Binning (T021)
Calculates accuracy over configurable blocks.
```bash
python code/src/data/align.py --task bin
```
*Output*: `data/accuracy_blocks.csv`

### 4. Lagged Alignment (T022)
Aligns MMN signals to subsequent accuracy blocks.
```bash
python code/src/data/align.py --task lag
```
*Output*: `data/interim_lagged_mmns.csv`

### 5. Finalization (T024)
Merges data, applies exclusion filters, and writes the final aligned dataset.
```bash
python code/src/data/finalize.py
```
*Output*: `data/aligned_data.csv`

### 6. Statistical Modeling (T027-T031)
Fits LME models and runs permutation tests.
```bash
python code/src/analysis/model.py
```
*Output*: `analysis/results/model_output.json`, `analysis/results/permutation_stability_log.json`

## Verification

After running the full sequence, verify the existence of the following key artifacts:
- `data/validation_report.json`
- `data/excluded_subjects.csv`
- `data/accuracy_blocks.csv`
- `data/interim_lagged_mmns.csv`
- `data/aligned_data.csv`
- `analysis/results/model_output.json`

If any step fails, check the logs in `logs/pipeline.log` for detailed error messages.
