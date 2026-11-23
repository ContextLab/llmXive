# Quickstart Guide

This guide outlines the steps to run the statistical analysis pipeline.

## Prerequisites
- Python 3.11+
- `pip install -r requirements.txt`

## Execution Order
The pipeline runs in the following order:

1. **Ingestion & Cleaning**
 - Downloads ADReSS dataset
 - Filters and cleans transcripts
 - Generates intermediate cleaned dataset
 - Command: `python code/ingestion.py`
 - Output: `data/interim/cleaned_adress.csv` (via T016 logic), `data/interim/filtered_adress.csv`

2. **Feature Extraction**
 - Computes linguistic features
 - Generates embeddings
 - Command: `python code/features.py`
 - Output: `data/processed/features.csv`, `data/processed/embeddings.npy`

3. **Statistical Analysis**
 - Performs Mann-Whitney U tests
 - Calculates effect sizes
 - Command: `python code/stats.py`
 - Output: `data/results/statistical_metrics.json`

4. **Modeling**
 - Trains classifiers
 - Performs cross-validation
 - Command: `python code/modeling.py`
 - Output: `data/results/model_performance.json`

5. **Main Pipeline**
 - Orchestrates all steps and measures runtime
 - Command: `python code/main.py`

## Running the Pipeline
```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python code/main.py
```

## Output Artifacts
- `data/interim/cleaned_adress.csv`: Cleaned dataset
- `data/processed/features.csv`: Feature matrix
- `data/results/metadata.json`: Metadata aggregation
- `data/results/statistical_metrics.json`: Statistical results
- `data/results/model_performance.json`: Model performance metrics