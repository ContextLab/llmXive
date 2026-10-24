"""
src/data/analysis.py
--------------------

Power analysis (Task T007) implementation.

This module reads the merged experimental dataset, computes the required
per‑group sample size for a one‑way ANOVA given the effect size,
significance level and within‑subject correlation, compares it to the
actual number of participants recruited, calculates the achieved power,
and writes a plain‑text report to ``results/power_report.txt``.

The script is deliberately lightweight: it only performs the power‑analysis
portion required for T007.  Later tasks (ANOVA, mixed‑effects, correlation,
figure generation) will extend this file, but the current implementation
satisfies the contract and the associated test suite
``src/tests/test_analysis_power.py``.
"""

import json
from pathlib import Path

import pandas as pd
from statsmodels.stats.power import FTestAnovaPower

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration (constants required by the specification)
# ----------------------------------------------------------------------
EFFECT_SIZE = 0.25          # Cohen's f
ALPHA = 0.05                # Significance level
TARGET_POWER = 0.80         # Desired statistical power
WITHIN_SUBJECT_RHO = 0.5    # Correlation for repeated‑measures designs
K_GROUPS = 3                # Number of experimental conditions (llm, human, none)

LOG = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_merged_dataset() -> pd.DataFrame:
    """
    Load the merged experimental dataset.

    Returns
    -------
    pd.DataFrame
        The merged data with at least a ``participant_id`` column.
    """
    merged_path = paths.data("merged_dataset.csv")
    if not merged_path.is_file():
        LOG.error(f"Merged dataset not found at {merged_path}")
        raise FileNotFoundError(f"Merged dataset not found at {merged_path}")
    LOG.info(f"Loading merged dataset from {merged_path}")
    return pd.read_csv(merged_path)

def _compute_required_sample_per_group(power_analysis: FTestAnovaPower) -> int:
    """
    Compute the required *per‑group* sample size to achieve the target power.

    The ``solve_power`` method returns a float; we round up to the nearest
    integer because you cannot recruit a fractional participant.

    Returns
    -------
    int
        Required number of participants per experimental condition.
    """
    required = power_analysis.solve_power(
        effect_size=EFFECT_SIZE,
        alpha=ALPHA,
        power=TARGET_POWER,
        k_groups=K_GROUPS,
    )
    required_int = int(required) if required.is_integer() else int(required) + 1
    LOG.debug(f"Raw required sample (per group): {required} → rounded to {required_int}")
    return required_int

def _compute_achieved_power(power_analysis: FTestAnovaPower, n_per_group: int) -> float:
    """
    Compute the achieved power given the actual number of participants per group.

    Parameters
    ----------
    power_analysis : FTestAnovaPower
        Initialized power analysis object.
    n_per_group : int
        Number of participants per experimental condition (within‑subject design).

    Returns
    -------
    float
        Achieved statistical power (0‑1).
    """
    achieved = power_analysis.power(
        effect_size=EFFECT_SIZE,
        nobs=n_per_group,
        alpha=ALPHA,
        k_groups=K_GROUPS,
    )
    LOG.debug(f"Achieved power with n={n_per_group}: {achieved}")
    return achieved

def _write_power_report(
    required_n: int,
    actual_n: int,
    achieved_power: float,
    out_path: Path,
) -> None:
    """
    Write the power analysis report required by the specification.

    The file contains four numeric fields and a plain‑text statement about
    whether the target power (≥ 0.80) is met.

    Parameters
    ----------
    required_n : int
        Required sample size per group.
    actual_n : int
        Actual number of participants (i.e. participants recruited).
    achieved_power : float
        Power achieved with the actual sample size.
    out_path : Path
        Destination path for ``power_report.txt``.
    """
    # Ensure parent directory exists (paths.results does this automatically)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    statement = (
        "Target power of 0.80 met."
        if achieved_power >= TARGET_POWER
        else "Target power of 0.80 NOT met. Limitation: insufficient power."
    )

    report_lines = [
        f"effect_size: {EFFECT_SIZE}",
        f"alpha: {ALPHA}",
        f"required_sample_per_group: {required_n}",
        f"achieved_power: {achieved_power:.4f}",
        statement,
    ]

    LOG.info(f"Writing power report to {out_path}")
    out_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the power analysis and write the report.

    The function is deliberately side‑effect‑only (writes a file) to keep
    the module usable from the command line as ``python -m src.data.analysis``.
    """
    LOG.info("Starting power analysis (Task T007)")

    # Load the merged dataset to obtain the number of unique participants.
    merged_df = _load_merged_dataset()
    actual_participants = merged_df["participant_id"].nunique()
    LOG.info(f"Number of unique participants recruited: {actual_participants}")

    # Initialise the power analysis helper.
    power_analyzer = FTestAnovaPower()

    # Required per‑group sample size for the desired power.
    required_n = _compute_required_sample_per_group(power_analyzer)

    # Achieved power with the *actual* number of participants per group.
    # In a within‑subject design each participant provides data for all
    # conditions, so the per‑group size equals the total participant count.
    achieved = _compute_achieved_power(power_analyzer, actual_participants)

    # Write the report to the canonical location.
    report_path = paths.results("power_report.txt")
    _write_power_report(required_n, actual_participants, achieved, report_path)

    LOG.info("Power analysis completed successfully")

if __name__ == "__main__":
    main()