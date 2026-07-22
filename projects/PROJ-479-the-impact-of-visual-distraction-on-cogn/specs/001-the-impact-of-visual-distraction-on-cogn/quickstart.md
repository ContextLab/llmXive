# Quickstart Guide

## Data Source Selection

### Real Dataset Path
The pipeline attempts to download a real linked dataset from HuggingFace or OpenML first.
If a valid linked dataset is found, it is used. Otherwise, the pipeline falls back to synthetic generation.

### Synthetic Data Path
If no real dataset is found, synthetic data is generated using `Pillow` for images and `numpy` for cognitive metrics.
The synthetic data generation ensures independence between predictors and outcomes.

## Interpretation of Results

### Real Dataset Interpretation
Findings from real data are associational. No causal claims are made.

### Synthetic Data Interpretation
Findings from synthetic data are illustrative and should be interpreted with caution.
The synthetic data is generated to test the pipeline, not to draw scientific conclusions.
