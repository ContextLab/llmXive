# Frequently Asked Questions

## Q: Why does the script fail with "Power limitation"?
A: The pipeline requires a minimum sample size of N=130 after cleaning. [UNRESOLVED-CLAIM: c_49aa4117 — status=not_enough_info] If the dataset is too small or too many rows are dropped due to missing values, the process halts to ensure statistical power.

## Q: What if the dataset URL is unreachable?
A: The pipeline is designed to fail loudly. It will not generate synthetic data. Ensure the `DATASET_URL` environment variable is correct and the network is accessible.

## Q: How are random seeds handled?
A: Seeds are set at the start of execution via `config.py` and logged. If no seed is provided, a warning is logged, and results may not be reproducible.

## Q: What is "Mathematical Coupling"?
A: It occurs when the predictor and outcome variables are derived from the same instrument or time point, leading to spurious correlations. The pipeline checks for this and halts if detected.

## Q: Can I use my own dataset?
A: Yes, provided it has the required schema (`news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`). Update the `DATASET_URL` or modify `ingest.py` to load local files.

## Q: Where are the logs stored?
A: Logs are written to `outputs/analysis.log`.
