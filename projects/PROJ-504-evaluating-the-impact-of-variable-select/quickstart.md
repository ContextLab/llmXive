# Quickstart Guide

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

To run the full pipeline (data download, simulation, analysis, and visualization):

```bash
python code/pipeline.py
```

This will:
1. Download 10 regression datasets from OpenML
2. Generate synthetic outcomes for various SNR and sparsity levels
3. Apply variable selection methods (Forward Stepwise, Backward Elimination, LASSO)
4. Calculate empirical power metrics
5. Generate power curves and statistical comparisons
6. Save results to `data/processed/` and `results/`

## Output Files

- `data/processed/simulation_results.csv`: Main results dataframe
- `results/plots/`: Generated power curves and diagnostic plots
- `results/final_report.md`: Comprehensive analysis report

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests:
```bash
pytest tests/integration/
```