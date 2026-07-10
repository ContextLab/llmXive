# Quick Start Guide

## Prerequisites
- Python 3.9+
- pip

## Installation
```bash
pip install -r requirements.txt
```

## Running the Ingestion Pipeline
```bash
python code/ingest.py
```
This will:
1. Fetch FDA-approved drugs from HuggingFace.
2. Validate degradation data availability.
3. Calculate molecular descriptors.
4. Save merged dataset to `data/processed/merged_drugs.csv`.

## Running Analysis
```bash
python code/standardize.py
python code/analysis.py
```

## Visualization
```bash
python code/viz.py
python code/report.py
```
