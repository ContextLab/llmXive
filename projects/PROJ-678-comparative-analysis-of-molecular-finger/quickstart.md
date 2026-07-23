# Quickstart Guide

This guide runs the full pipeline end-to-end.

## Setup

```bash
pip install -r requirements.txt
```

## Execution

Run the scripts in order:

```bash
# 1. Download Tox21 dataset
python code/download.py

# 2. Filter for organophosphates
python code/filter.py

# 3. Generate fingerprints
python code/fingerprints.py

# 4. Split data
python code/split.py

# 5. Train models
python code/train.py

# 6. Evaluate and generate report
python code/evaluate.py
```

## Outputs

- `data/processed/organophosphates_filtered.csv`: Filtered compounds
- `data/processed/research_results.md`: Final report
