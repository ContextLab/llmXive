"""
power_pre.py
-------------
Perform an a‑priori power analysis for the mixed‑effects F‑test that will be
used later in the pipeline. The script computes analytical power using
``statsmodels.stats.power.FTestPower`` with a fixed effect‑size f² = 0.05,
significance level α = 0.05 and an anticipated number of QC‑passed
subjects (default 200). The result is written as JSON to
``results/power_analysis_pre.json`` with the following fields:

- power: computed statistical power (float)
- effect_size_f2: the input effect size f² (float)
- n_subjects: number of subjects used for the calculation (int)
- alpha: significance level (float)
- underpowered: true if power < 0.80 (bool)

The script can be called directly or via the package entry point:

    python -m src.stats.power_pre [--subjects N]

If ``--subjects`` is omitted the default of 200 is used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from statsmodels.stats.power import FTestPower

from llmxive_toolkit import paths, get_logger

LOG = get_logger(__name__)

DEFAULT_SUBJECTS = 200
EFFECT_SIZE_F2 = 0.05
ALPHA = 0.05
POWER_THRESHOLD = 0.80


def compute_power(
    n_subjects: int,
    effect_f2: float = EFFECT_SIZE_F2,
    alpha: float = ALPHA,
) -> float:
    """
    Compute analytical power for a one‑way F‑test (approximation for the mixed‑effects
    test used later). The effect size ``f`` is derived from ``f²``.

    Parameters
    ----------
    n_subjects : int
        Anticipated number of QC‑passed subjects.
    effect_f2 : float
        Effect size f² (default 0.05).
    alpha : float
        Significance level (default 0.05).

    Returns
    -------
    float
        Statistical power.
    """
    # Convert f² to Cohen's f
    effect_f = np.sqrt(effect_f2)

    # Degrees of freedom: we approximate a single predictor (df1 = 1)
    df_num = 1
    # Residual degrees of freedom; conservative estimate
    df_denom = max(n_subjects - df_num - 1, 1)

    power_analysis = FTestPower()
    # ``FTestPower.power`` expects (effect_size, df_num, df_denom, alpha)
    power = power_analysis.power(
        effect_size=effect_f,
        df_num=df_num,
        df_denom=df_denom,
        alpha=alpha,
    )
    LOG.debug(
        "Power calculation input – n_subjects=%s, effect_f2=%s, alpha=%s",
        n_subjects,
        effect_f2,
        alpha,
    )
    LOG.debug(
        "Derived values – effect_f=%s, df_num=%s, df_denom=%s, power=%s",
        effect_f,
        df_num,
        df_denom,
        power,
    )
    return float(power)


def write_results(
    power: float,
    n_subjects: int,
    effect_f2: float = EFFECT_SIZE_F2,
    alpha: float = ALPHA,
    output_path: Path | None = None,
) -> None:
    """
    Serialize the power‑analysis results to JSON.

    Parameters
    ----------
    power : float
        Computed power.
    n_subjects : int
        Number of subjects used.
    effect_f2 : float
        Effect size f².
    alpha : float
        Significance level.
    output_path : pathlib.Path, optional
        Destination path. If ``None`` the default ``results/power_analysis_pre.json``
        is used via ``llmxive_toolkit.paths.results``.
    """
    if output_path is None:
        output_path = paths.results("power_analysis_pre.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "power": power,
        "effect_size_f2": effect_f2,
        "n_subjects": n_subjects,
        "alpha": alpha,
        "underpowered": power < POWER_THRESHOLD,
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)

    LOG.info("Power analysis written to %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="A‑priori power analysis for the mixed‑effects F‑test."
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=DEFAULT_SUBJECTS,
        help=f"Anticipated number of QC‑passed subjects (default: {DEFAULT_SUBJECTS}).",
    )
    args = parser.parse_args()

    LOG.info("Starting a‑priori power analysis for %s subjects.", args.subjects)
    power = compute_power(n_subjects=args.subjects)

    write_results(power=power, n_subjects=args.subjects)

    LOG.info(
        "Power analysis completed – power=%.4f, underpowered=%s",
        power,
        power < POWER_THRESHOLD,
    )


if __name__ == "__main__":
    main()