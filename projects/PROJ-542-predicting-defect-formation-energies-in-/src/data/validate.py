"""
src/data/validate.py
---------------------

Perform validation on ``data/processed/features.csv``.
- Raise ``ValueError`` if rows < 50.
- Log a warning (and compute statistical power) if rows < 210.
- Always write a ``validation.log`` file with the row count and power.
"""

import pandas as pd
from statsmodels.stats.power import TTestPower
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def main() -> None:
    """
    Validate the processed feature matrix and compute statistical power.
    """
    features_path = paths.data("processed", "features.csv")
    if not features_path.is_file():
        raise FileNotFoundError(f"Features file not found: {features_path}")

    df = pd.read_csv(features_path)

    row_count = len(df)
    log.info(f"Feature matrix contains {row_count} rows.")

    if row_count < 50:
        raise ValueError("Dataset must contain at least 50 rows for cross‑validation (FR‑009).")

    # Power analysis: detect ΔRMSE = 0.1 eV with σ ≈ 0.3 eV, α = 0.05.
    effect_size = 0.1 / 0.3  # Cohen's d equivalent
    alpha = 0.05
    power_analysis = TTestPower()
    required_n = power_analysis.solve_power(effect_size=effect_size, alpha=alpha, power=0.8, alternative='two-sided')
    required_n = int(required_n) + 1  # round up

    if row_count < required_n:
        log.warning(
            f"Statistical power is insufficient (N={row_count} < required {required_n})."
        )
    else:
        log.info(f"Statistical power sufficient (N={row_count} ≥ required {required_n}).")

    # Write validation log.
    validation_log_path = paths.data("processed", "validation.log")
    validation_log_path.parent.mkdir(parents=True, exist_ok=True)
    with validation_log_path.open("w", encoding="utf-8") as f:
        f.write(f"row_count: {row_count}\\n")
        f.write(f"required_n_for_power_0.8: {required_n}\\n")
        f.write(f"power_sufficient: {row_count >= required_n}\\n")

    log.info(f"Validation log written to {validation_log_path}")