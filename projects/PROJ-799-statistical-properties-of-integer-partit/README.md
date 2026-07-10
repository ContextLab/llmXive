# Statistical Properties of Integer Partitions Into Distinct Prime Summands

## Project Overview
This project investigates the statistical properties of $p_{\mathcal{P}}(n)$, the number of partitions of an integer $n$ into distinct prime summands. We compare exact computations against asymptotic baselines derived from the distinct-partition variant of Meinardus' theorem.

## Directory Structure
- `code/`: Python implementation modules
- `data/raw/`: Generated partition data
- `data/processed/`: Processed features and model results
- `data/schemas/`: Data validation schemas
- `tests/`: Unit and integration tests
- `docs/`: Documentation
- `state/`: Project state tracking

## Requirements
Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage
Run the pipeline:
```bash
python code/generate_partitions.py
python code/feature_engineering.py
python code/regression_model.py
python code/visualize_results.py
```
