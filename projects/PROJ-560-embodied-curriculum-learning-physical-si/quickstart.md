# Quickstart Guide: Embodied Curriculum Learning Analysis

## Prerequisites

- Python 3.9+
- `pip` installed

## Setup

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Analysis

### 1. Synthetic Data Generation (Pipeline Validation)

To validate the pipeline without external data, run the synthetic generator:

```bash
python -m src.cli --mode=synthetic --n=1000 --seed=42
```

This will:
- Generate a synthetic dataset at `data/synthetic/generated_dataset.csv`.
- Write a mapping log to `data/synthetic/mapping_log.json` (Constitution Principle VI).

### 2. Secondary Analysis (Public Data)

If you have a public dataset with `pre_test_score`, `post_test_score`, and `instruction_type`:

```bash
python -m src.cli --mode=secondary_analysis --input=data/raw/your_dataset.csv
```

If the input dataset is missing `instruction_type`, the system will automatically attempt to generate synthetic fallback data. If that fails, it will exit with an error.

### 3. Sensitivity Sweep

To run a sensitivity analysis on thresholds (US3):

```bash
python -m src.cli --mode=secondary_analysis --input=data/raw/your_dataset.csv --sweep_thresholds 0.01 0.05 0.10
```

### 4. Performance Verification (T039)

To verify the system meets the 600s performance goal for N=10000:

```bash
python code/src/perf_monitor.py
```

This script runs the CLI with `--n=10000` and writes the timing result to `data/processed/perf_log.json`.

## Output Files

- `data/synthetic/mapping_log.json`: Physics-to-math mapping documentation (Synthetic Mode).
- `data/synthetic/generated_dataset.csv`: Synthetic dataset.
- `data/processed/validated_fallback.csv`: Processed data with gain scores.
- `data/processed/results.json`: Full statistical analysis report.
- `data/processed/perf_log.json`: Performance benchmark results.
- `data/derivation_logs/skipped_records.log`: JSONL log of skipped records.

## Troubleshooting

- **Missing `instruction_type`**: If your public data lacks this column, the system will try to generate synthetic data. If you want to force synthetic generation, use `--mode=synthetic`.
- **Argparse Errors**: Ensure you are using the correct flags. `--n_participants` and `--effect_size` are not valid arguments; use `--n` and `--mean_diff_embodied`/`--mean_diff_static` respectively.