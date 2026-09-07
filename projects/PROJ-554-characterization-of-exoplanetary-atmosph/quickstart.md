# Quickstart Guide

This guide describes how to run the full pipeline for the Characterization of Exoplanetary Atmospheres project.

## Prerequisites

- Python 3.9+
- Virtual environment activated

## Installation

```bash
pip install -r requirements.txt
```

## Execution

Run the following commands in order to execute the full pipeline:

1. **Setup Directories**:
 ```bash
 python code/setup_directories.py
 ```

2. **Download Data**:
 ```bash
 python code/download.py --output data/raw
 ```

3. **Run Retrieval**:
 ```bash
 python code/retrieval.py --input data/raw --output data/processed
 ```

4. **Run Analysis**:
 ```bash
 python code/analysis.py --input data/processed/analysis_dataset.csv --output results
 ```

5. **Generate Detection Limit Analysis (Task T051)**:
 ```bash
 python code/detection_limit_analysis.py
 ```

6. **Aggregate Results**:
 ```bash
 python code/aggregate_results.py
 ```

## Outputs

- `data/processed/metadata.csv`: Downloaded and processed metadata.
- `data/processed/retrieval_results.csv`: Retrieval results including water abundance and MDC.
- `data/processed/analysis_results.json`: Aggregated analysis results.
- `results/detection_limit_separation.md`: Statistical report for T051.
- `results/plots/detection_limit_scatter.png`: Scatter plot for T051.