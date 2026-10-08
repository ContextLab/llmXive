# Quickstart Guide

This guide outlines the steps to run the molecular conductivity prediction pipeline.

## Prerequisites

- Python 3.8+
- pip

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Execution

Run the full pipeline and validation steps:

```bash
python code/run_descriptor_pipeline.py
python code/run_training.py
python code/run_sensitivity_analysis.py
python code/run_analysis.py
python code/run_analysis_summary.py
python code/run_validation_task.py
```

## Output Artifacts

The pipeline produces the following artifacts:
- `data/processed/descriptors.csv`
- `data/processed/model_results.json`
- `data/processed/analysis_summary.json`
- `data/processed/sensitivity_analysis.json`
- `data/processed/feature_importance.csv`