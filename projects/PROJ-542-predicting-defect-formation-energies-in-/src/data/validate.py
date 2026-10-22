"""
src/data/validate.py
--------------------

Validate the processed feature matrix and compute statistical power.

The script checks that the feature matrix contains at least 50 rows (FR‑009)
and computes the statistical power to detect a ΔRMSE = 0.1 eV given an
assumed σ ≈ 0.3 eV, α = 0.05.  The result is written to
``data/processed/validation.log``.
"""

import pandas as pd
from statsmodels.stats.power import TTestPower
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def main() -> None:
    features_path = paths.data("processed", "features.csv")
    log_path = paths.data("processed", "validation.log")

    df = pd.read_csv(features_path)

    row_count = len(df)
    if row_count < 50:
        raise ValueError("FR-009: Dataset must contain at least 50 rows for validation.")

    # Power analysis parameters
    effect_size = 0.1 / 0.3  # ΔRMSE / σ
    alpha = 0.05
    power_analysis = TTestPower()
    # Solve for required sample size to achieve 80% power
    required_n = power_analysis.solve_power(effect_size=effect_size, alpha=alpha, power=0.8, alternative='two-sided')
    required_n = int(required_n) + 1  # round up

    power = power_analysis.power(effect_size=effect_size, nobs=row_count, alpha=alpha, alternative='two-sided')

    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"Row count: {row_count}\\n")
        f.write(f"Statistical power (α=0.05, ΔRMSE=0.1 eV, σ≈0.3 eV): {power:.3f}\\n")
        if row_count < required_n:
            f.write(f"Warning: Sample size below recommended {required_n} for 80% power.\\n")
        else:
            f.write("Sample size sufficient for 80% power.\\n")

    log.info(f"Validation completed. Log written to {log_path}")
