"""
src/data/validate.py
--------------------

Validation step for the processed feature matrix. It checks that the dataset
meets minimum size requirements and performs a simple statistical power
analysis. The results are written to ``data/processed/validation.log``.

FR‑009 requires a ``ValueError`` if the dataset contains fewer than 50 rows.
SC‑005 requires a warning (and power calculation) if the dataset contains
fewer than 500 rows but the pipeline should continue.
"""

import pandas as pd
from statsmodels.stats.power import TTestPower

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def main() -> None:
    """
    Perform validation on ``data/processed/features.csv``.
    - Raise ``ValueError`` if rows < 50.
    - Log a warning (and compute statistical power) if rows < 500.
    - Always write a ``validation.log`` file with the row count and power.
    """
    features_path = paths.data("processed", "features.csv")
    if not features_path.is_file():
        log.error(f"Features file not found at {features_path}")
        raise FileNotFoundError(f"{features_path} not found")

    df = pd.read_csv(features_path)
    n_rows = len(df)

    if n_rows < 50:
        raise ValueError(
            f"Dataset contains only {n_rows} rows, which is less than the required minimum of 50."
        )

    # Log basic size information
    log.info(f"Dataset size: {n_rows} rows.")

    # Simple power analysis: assume a medium effect size (Cohen's d = 0.5)
    effect_size = 0.5
    power_calculator = TTestPower()
    power = power_calculator.power(
        effect_size=effect_size, nobs=n_rows, alpha=0.05, alternative="two-sided"
    )
    power_msg = f"Statistical power (effect size {effect_size}) with n={n_rows}: {power:.3f}"

    if n_rows < 500:
        log.warning(f"Dataset contains fewer than 500 rows. {power_msg}")
    else:
        log.info(power_msg)

    # Write the validation log
    log_path = paths.data("processed", "validation.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Rows: {n_rows}\\n")
        f.write(f"{power_msg}\\n")
    log.info(f"Wrote validation log to {log_path}")

if __name__ == "__main__":
    main()