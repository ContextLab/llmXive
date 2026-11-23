# Quickstart Guide

This guide explains how to run the Solar Flare - Geomagnetic Storm Correlation Pipeline.

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
pip install -r requirements.txt
```

## Running the Pipeline

Execute the full pipeline:

```bash
python code/main.py
```

This will:
1. Verify data sources
2. Ingest GOES, Dst, and Kp data
3. Align solar events with geomagnetic storms
4. Filter non-recurrent storms
5. Perform correlation analysis

## Output Files

- `data/processed/aligned_events.csv`: All aligned events
- `data/processed/analysis_subset.csv`: Non-recurrent storm subset for analysis
- `results/metrics.json`: Correlation metrics and analysis results

## Validation

Validate the aligned events:

```bash
python code/validate.py data/processed/aligned_events.csv contracts/aligned_event.schema.yaml
```