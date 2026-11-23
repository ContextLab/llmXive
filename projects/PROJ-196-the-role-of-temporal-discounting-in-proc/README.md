# The Role of Temporal Discounting in Procrastination on Cognitive Tasks

This project investigates the relationship between temporal discounting (how much individuals devalue future rewards), procrastination tendencies, and working memory performance.

## Project Structure

- `code/`: Python source modules for data generation, modeling, and robustness analysis.
- `data/raw/`: Raw input data (or generated synthetic data if real data is unavailable).
- `data/processed/`: Harmonized datasets and analysis results.
- `tests/`: Unit and integration tests.
- `state/`: Project state tracking and artifact hashes.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`

## Usage

To run the full pipeline end-to-end (data generation, harmonization, regression, and robustness checks):

```bash
python code/main.py --seed 42
```

This command will:
1. Validate DGP parameters.
2. Generate synthetic data (if real data is not present) or load real data.
3. Harmonize datasets and calculate discount rates.
4. Run OLS regression with interaction terms.
5. Perform bootstrapping and sensitivity analysis.
6. Write all results to `data/processed/`.

### Individual Modules

- **Data Ingestion**: `python code/ingestion.py --mode generate --n 500 --seed 42`
- **Modeling**: `python code/modeling.py`
- **Robustness**: `python code/robustness.py`

## Data Source

This project implements a **Data Generating Process (DGP)** to simulate participant data based on established literature parameters for delay discounting, procrastination, and working memory tasks.

**Synthetic Data Strategy**:
- **Delay Discounting**: Simulates choices between smaller-sooner and larger-later rewards using a hyperbolic discounting model ($V = A / (1 + kD)$).
- **Procrastination**: Generates scores based on the Pure Procrastination Scale (PPS) with added noise.
- **Working Memory**: Simulates n-back task performance (accuracy and reaction time) with varying load levels.

**Note**: If real data files exist in `data/raw/` (named `delay_discounting.csv`, `procrastination.csv`, `nback.csv`), the pipeline will attempt to load and validate them instead of generating synthetic data. If real data is missing or invalid, the pipeline falls back to the DGP and flags the data source in `data/processed/data_source_flag.json`.

## Reproducibility

All stochastic processes use a seed managed by `code/config.py`. Pass `--seed` to the main script to ensure reproducible results.

## License

MIT License
