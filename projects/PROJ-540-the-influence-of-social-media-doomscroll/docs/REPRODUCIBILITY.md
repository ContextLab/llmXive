# Reproducibility Statement

This project adheres to strict reproducibility standards to ensure that results can be independently verified.

## Random Seed Management

All random operations (data sampling, model initialization) are controlled by a single random seed configured via `RANDOM_SEED` or `config.yaml`.
- The seed is validated at startup.
- The seed value is logged in `outputs/analysis.log`.
- If no seed is provided, a warning is logged, and the run may be non-reproducible.

## Data Hygiene

- **No Synthetic Data**: The pipeline is designed to fail if the real data source is unavailable. No fallback to synthetic or mock data is implemented.
- **Versioned Data**: The exact dataset URL and version used for a run should be recorded in the configuration.

## Code Integrity

- **Deterministic Execution**: Given the same input data and seed, the pipeline produces identical outputs.
- **Explicit Dependencies**: All dependencies are pinned in `requirements.txt`.
- **Linting & Formatting**: Code is formatted with Black and linted with flake8 to ensure consistency.

## Artifacts

All intermediate and final artifacts are saved to disk:
- `data/raw/parsed_data.csv`
- `data/processed/analysis_data.csv`
- `outputs/regression_results.json`
- `outputs/correlation_results.json`
- `outputs/robustness_results.json`
- `outputs/final_report.md`
- `outputs/*.png`

These artifacts allow for step-by-step verification of the analysis.

## Limitations

- **External Data Availability**: Reproducibility depends on the continued availability of the external dataset URL.
- **Computational Resources**: Large datasets may require significant memory and processing power.
