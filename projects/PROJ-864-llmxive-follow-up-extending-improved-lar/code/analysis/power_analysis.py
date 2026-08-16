"""
Power Analysis Module for llmXive Follow-up Project.

Performs a priori power analysis to determine if the chosen experimental regime
(1M or 10M tokens) provides sufficient statistical power (>= 0.8) for the
planned Mixed-Model Repeated-Measures ANOVA.

Traceability: Spec FR-009
Depends on: T001 (config.yaml generation)
"""

import json
import sys
import math
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from statsmodels.stats.power import FTestAnovaPower, TTestIndPower

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logging import get_logger, info, error, warning

logger = get_logger(__name__)


def compute_effect_size(
    regime: str,
    expected_gap_autoregressive: float = 0.05,
    expected_gap_diffusion: float = 0.04,
    expected_std: float = 0.02,
    n_seeds: int = 5
) -> float:
    """
    Compute the expected effect size (Cohen's f) for the ANOVA.

    The effect size depends on the expected difference in generalization gap
    between AR and Diffusion models, and the expected variance.

    Args:
        regime: The token regime ('1M' or '10M').
        expected_gap_autoregressive: Expected mean gap for AR model.
        expected_gap_diffusion: Expected mean gap for Diffusion model.
        expected_std: Expected standard deviation of the gap.
        n_seeds: Number of seeds per model.

    Returns:
        Cohen's f effect size.
    """
    # Adjust expectations based on regime
    # With more tokens (10M), we expect smaller gaps and potentially smaller variance
    if regime == "10M":
        # Larger dataset -> smaller gaps, potentially smaller variance
        # But we keep the relative difference assumption
        expected_gap_autoregressive *= 0.6
        expected_gap_diffusion *= 0.6
        expected_std *= 0.7
    elif regime == "1M":
        # Smaller dataset -> larger gaps, potentially larger variance
        expected_gap_autoregressive *= 1.2
        expected_gap_diffusion *= 1.2
        expected_std *= 1.3

    # Effect size for ANOVA: f = sigma_m / sigma
    # sigma_m = sqrt(sum((mu_i - mu_overall)^2) / k)
    mu_ar = expected_gap_autoregressive
    mu_diff = expected_gap_diffusion
    mu_overall = (mu_ar + mu_diff) / 2.0

    # Variance of means
    sigma_m_sq = ((mu_ar - mu_overall)**2 + (mu_diff - mu_overall)**2) / 2.0
    sigma_m = math.sqrt(sigma_m_sq)

    # Cohen's f
    if expected_std == 0:
        logger.warning("Expected standard deviation is zero, using fallback.")
        expected_std = 0.01

    f = sigma_m / expected_std

    info(f"Computed effect size (Cohen's f) for {regime} regime: {f:.4f}")
    return f


def perform_power_analysis(
    effect_size: float,
    alpha: float = 0.05,
    power_target: float = 0.80,
    n_groups: int = 2,
    n_repeats: int = 10,  # Approximate number of epochs/measures
    n_seeds: int = 5
) -> Dict[str, Any]:
    """
    Perform a priori power analysis for the Mixed-Model Repeated-Measures ANOVA.

    Since statsmodels doesn't have a direct "Mixed Model" power calculator,
    we use FTestAnovaPower as a conservative approximation for the main effect
    (Model Type) in a repeated measures design. This is a standard approach
    when exact mixed-model power calculators are unavailable.

    Args:
        effect_size: Cohen's f effect size.
        alpha: Significance level.
        power_target: Target power.
        n_groups: Number of between-subject groups (Model Types: AR, Diffusion).
        n_repeats: Number of repeated measures (epochs).
        n_seeds: Number of subjects (seeds) per group.

    Returns:
        Dictionary with power analysis results.
    """
    total_subjects = n_groups * n_seeds

    # Use FTestAnovaPower for the main effect of Model Type
    # This approximates the power to detect a difference between AR and Diffusion
    power_analyzer = FTestAnovaPower()

    # Calculate power for the given parameters
    # We assume the repeated measures increase the effective sample size slightly,
    # but we use the number of subjects for a conservative estimate.
    try:
        calculated_power = power_analyzer.solve_power(
            effect_size=effect_size,
            nobs1=total_subjects,
            alpha=alpha,
            power=None,
            ratio=1.0
        )
    except ValueError as e:
        logger.error(f"Power calculation failed: {e}")
        # If effect size is too small or parameters are invalid, power might be NaN or fail
        calculated_power = 0.0

    # Determine if power is sufficient
    is_sufficient = calculated_power >= power_target

    results = {
        "regime": "1M",  # Will be overwritten by caller
        "effect_size": effect_size,
        "alpha": alpha,
        "target_power": power_target,
        "calculated_power": calculated_power,
        "is_sufficient": is_sufficient,
        "total_subjects": total_subjects,
        "groups": n_groups,
        "seeds_per_group": n_seeds,
        "repeated_measures": n_repeats,
        "recommendation": "PASS" if is_sufficient else "FAIL"
    }

    return results


def main() -> int:
    """
    Main entry point for power analysis.

    1. Reads regime from code/config.yaml.
    2. Performs a priori power analysis.
    3. If power < 0.8, HALT with error.
    4. Otherwise, logs success and exits.

    Returns:
        0 on success, 1 on failure.
    """
    # Determine project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    config_path = project_root / "code" / "config.yaml"

    if not config_path.exists():
        error(f"Config file not found: {config_path}")
        error("Please run T001 (generate_config.py) first.")
        return 1

    # Load config
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        error(f"Failed to load config: {e}")
        return 1

    regime = config.get("regime", "1M")
    token_target = config.get("token_target", 1000000)

    info(f"Starting Power Analysis for regime: {regime} ({token_target:,} tokens)")

    # Perform power analysis
    # Parameters can be adjusted based on domain knowledge
    # For now, we use reasonable defaults
    effect_size = compute_effect_size(regime=regime)

    power_results = perform_power_analysis(
        effect_size=effect_size,
        n_seeds=5,  # As per plan
        n_groups=2, # AR and Diffusion
        n_repeats=10 # Approximate epochs
    )
    power_results["regime"] = regime
    power_results["token_target"] = token_target

    # Log results
    info(f"Calculated Power: {power_results['calculated_power']:.4f}")
    info(f"Target Power: {power_results['target_power']}")
    info(f"Effect Size: {power_results['effect_size']:.4f}")

    # Save results to artifacts
    artifacts_dir = project_root / "data" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifacts_dir / "power_analysis_results.json"

    try:
        with open(output_path, 'w') as f:
            json.dump(power_results, f, indent=2)
        info(f"Power analysis results saved to: {output_path}")
    except Exception as e:
        error(f"Failed to save power analysis results: {e}")
        return 1

    # Check power threshold
    if not power_results["is_sufficient"]:
        error(f"Power analysis FAILED. Calculated power ({power_results['calculated_power']:.4f}) is below target ({power_results['target_power']}).")
        error("The chosen regime does not provide sufficient statistical power.")
        error("Recommendation: Increase token target, increase number of seeds, or reconsider effect size assumptions.")
        return 1

    info("Power analysis PASSED. The chosen regime provides sufficient statistical power.")
    return 0


if __name__ == "__main__":
    sys.exit(main())