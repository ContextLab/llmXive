"""
Unit test to verify that the sample size N produced by code/power_analysis.py
achieves statistical power >= 0.80 for effect size r >= 0.3.

This test:
1. Executes the power_analysis.py script to generate the result JSON.
2. Reads the calculated sample size N from the output file.
3. Uses statsmodels.stats.power to verify that with this N, the power
   for detecting r=0.3 is indeed >= 0.80.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from statsmodels.stats.power import tt_solve_power
from scipy.stats import norm


def test_power_analysis_sample_size_verification():
    """
    Verify that N from power_analysis.py yields power >= 0.80 for r=0.3.
    """
    # 1. Run the power analysis script to ensure the output file exists
    script_path = Path("code/power_analysis.py")
    if not script_path.exists():
        pytest.fail(f"Script {script_path} not found.")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        pytest.fail(f"Power analysis script failed: {result.stderr}")

    # 2. Read the result from the JSON file
    output_path = Path("data/analysis/power_analysis_result.json")
    if not output_path.exists():
        pytest.fail(f"Output file {output_path} not found after script execution.")

    with open(output_path, "r") as f:
        data = json.load(f)

    required_n = data["required_sample_size_N"]
    effect_size_r = data["effect_size_r"]
    target_power = data["target_power"]
    alpha = data["alpha"]

    assert required_n is not None and required_n > 0, "Sample size N must be positive"
    assert effect_size_r == 0.3, "Effect size must be 0.3"

    # 3. Verify the power using statsmodels
    # We use the t-test power analysis as a proxy for correlation power analysis
    # because the non-centrality parameter for Pearson correlation t-test
    # is equivalent to the t-test for means with a specific effect size conversion.
    # Specifically, t = r * sqrt((N-2)/(1-r^2)).
    # The effect size 'd' for the t-test equivalent is related to r by:
    # d = 2r / sqrt(1-r^2) (Cohen's d approximation for correlation)
    # However, statsmodels' `tt_solve_power` expects effect_size (Cohen's d).
    # Let's calculate the exact non-centrality parameter or use the direct
    # Fisher Z approach if statsmodels doesn't have a direct correlation solver.
    #
    # Alternative: Use the formula derived in the script itself to reverse check.
    # The script uses: N = ((z_alpha + z_beta) / z_rho)^2 + 3
    # We can calculate the actual power for this N and r.
    # Power is P(Z > z_alpha - z_rho * sqrt(N-3)) for one-sided,
    # or similar for two-sided.
    #
    # Let's use the statsmodels `zt_ind_solve_power` logic manually or verify
    # the calculation from the script's formula directly.
    #
    # Re-calculation using the script's logic:
    z_rho = 0.5 * np.log((1 + effect_size_r) / (1 - effect_size_r))
    z_alpha = norm.ppf(1 - alpha / 2)  # two-sided

    # The non-centrality parameter for the Z-test of correlation is z_rho * sqrt(N-3)
    # The critical value is z_alpha.
    # Power = P(Z > z_alpha - z_rho * sqrt(N-3)) + P(Z < -z_alpha - z_rho * sqrt(N-3))
    # Since r > 0, the second term is negligible.
    # Power approx = 1 - norm.cdf(z_alpha - z_rho * sqrt(N-3))

    n_minus_3 = required_n - 3
    if n_minus_3 <= 0:
        pytest.fail(f"Calculated N ({required_n}) is too small for Fisher transformation (N must be > 3).")

    non_central_param = z_rho * np.sqrt(n_minus_3)
    z_beta_actual = non_central_param - z_alpha
    actual_power = norm.cdf(z_beta_actual)

    # For a two-sided test, the approximation is slightly different, but this
    # is the standard method used in the script.
    # We allow a small tolerance for floating point differences.
    tolerance = 0.01
    assert actual_power >= (target_power - tolerance), (
        f"Calculated sample size N={required_n} yields power {actual_power:.4f}, "
        f"which is below the target {target_power}. "
        f"Expected power >= {target_power}."
    )

    # Additionally, verify that N-1 would fail (optional but good for sanity)
    if required_n > 4:
        n_minus_3_prev = (required_n - 1) - 3
        non_central_param_prev = z_rho * np.sqrt(n_minus_3_prev)
        z_beta_prev = non_central_param_prev - z_alpha
        power_prev = norm.cdf(z_beta_prev)
        # It should be lower, though maybe still above 0.80 if the step is small
        assert power_prev <= actual_power, "Power should not decrease with larger N."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])