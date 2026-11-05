"""
Unit test to verify that the sample size N produced by the power analysis script
achieves the required statistical power (≥ 0.80) for detecting a correlation
of at least r = 0.3.

The test runs the ``code/power_analysis.py`` script, extracts the calculated
sample size ``N`` from its stdout, and then uses ``statsmodels.stats.power``
utilities to recompute the achieved power. The test asserts that the power
meets or exceeds the target threshold.
"""

import re
import subprocess
import sys
import math

import pytest
from statsmodels.stats.power import tt_solve_power

SCRIPT_PATH = "code/power_analysis.py"
EFFECT_SIZE_R = 0.3
ALPHA = 0.05
TARGET_POWER = 0.80
TOLERANCE = 0.01  # allow small numerical differences


def _run_power_analysis_script():
    """Execute the power analysis script and capture its stdout."""
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH],
        capture_output=True,
        text=True,
        check=False,  # we'll handle errors explicitly
    )
    if result.returncode != 0:
        pytest.fail(
            f"Power analysis script failed with exit code {result.returncode}.\n"
            f"Stderr: {result.stderr}"
        )
    return result.stdout


def _extract_sample_size(stdout: str) -> int:
    """
    Parse the script's stdout to find the reported sample size ``N``.
    The script prints a line like:
        Result: A sample size of N = 85 is required.
    """
    match = re.search(r"Result:\s+A sample size of N\s*=\s*(\d+)", stdout)
    if not match:
        pytest.fail(
            "Could not find the sample size in the script output. "
            "Expected a line matching 'Result: A sample size of N = <int>'."
        )
    return int(match.group(1))


def _correlation_to_cohens_d(r: float) -> float:
    """
    Convert Pearson correlation coefficient ``r`` to Cohen's d,
    which is the effect size used by ``statsmodels``'s ``tt_solve_power``.
    The relationship is::

        d = 2r / sqrt(1 - r^2)

    This conversion is standard for approximating the power of a
    correlation test via a two‑sample t‑test.
    """
    return 2 * r / math.sqrt(1 - r ** 2)


def test_output_power():
    """
    Verify that the sample size N reported by ``code/power_analysis.py``
    yields a statistical power of at least 0.80 for detecting a
    correlation of r = 0.3.
    """
    # 1. Run the script and capture its output
    stdout = _run_power_analysis_script()

    # 2. Extract the calculated sample size N
    required_n = _extract_sample_size(stdout)

    # Sanity check on the extracted value
    assert required_n > 0, "Sample size N must be a positive integer"

    # 3. Convert the target correlation to Cohen's d for the t‑test power function
    d = _correlation_to_cohens_d(EFFECT_SIZE_R)

    # 4. Compute the achieved power using statsmodels
    achieved_power = tt_solve_power(
        effect_size=d,
        nobs=required_n,
        alpha=ALPHA,
        alternative="two-sided",
    )

    # 5. Assert the power meets the required threshold (allowing a tiny tolerance)
    assert achieved_power >= TARGET_POWER - TOLERANCE, (
        f"Achieved power {achieved_power:.4f} is below the target "
        f"{TARGET_POWER:.2f} for sample size N = {required_n}"
    )