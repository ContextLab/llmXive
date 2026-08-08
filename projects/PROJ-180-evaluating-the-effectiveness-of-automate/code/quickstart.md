# Quickstart Guide

## Prerequisites

- Python 3.9+
- Docker (for tool execution)
- GitHub Token (set in `.env` as `GITHUB_TOKEN`)

## Setup

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv code/.venv
 source code/.venv/bin/activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
4. Configure environment:
 ```bash
 cp code/.env.example code/.env
 # Edit code/.env and add your GITHUB_TOKEN
 ```

## Execution Pipeline

Run the following commands in order to execute the full research pipeline:

### 1. Data Acquisition
Clones repositories and runs static analysis tools.
```bash
python code/01_data_acquisition.py
```

### 2. Human Baseline & Annotation
Extracts PR comments, applies heuristics, and prepares samples for review.
```bash
python code/02_human_annotation.py
```

### 3. Alignment
Aligns tool issues with human-validated ground truth.
```bash
python code/03_alignment.py
```

### 4. Metrics & Statistical Analysis
Computes precision/recall and runs statistical tests.
```bash
python code/04_metrics.py
```

### 5. Regression Analysis
Fits mixed-effects models to analyze project characteristics.
```bash
python code/05_regression.py
```

## Output Artifacts

- `data/raw/`: Raw repository clones and tool reports.
- `data/processed/`: Processed datasets, aligned pairs, and ground truth.
- `results/`: Final metrics, regression summaries, and plots.

## Validation

Run the verification script to ensure all artifacts are generated correctly:
```bash
python code/utils/data_validator.py
```
