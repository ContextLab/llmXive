# PROJ-062: Quantifying the Impact of Code Ownership on Software Quality

## Project Overview
This project investigates the relationship between code ownership (measured via Gini coefficient) and software quality (measured via bug density).

## Structure
- `data/raw/`: Raw cloned repositories and git history
- `data/intermediate/`: Processed CSVs (ownership, churn, complexity)
- `data/results/`: Final analysis outputs (JSON, plots)
- `code/`: Python implementation modules
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and design docs

## Usage
Run the full pipeline:
```bash
python code/main.py
```

Run specific stages:
```bash
python code/data_collection.py
python code/metrics_calc.py
python code/statistical_analysis.py
```
