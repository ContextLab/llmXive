"""
Power Analysis Utilities for MobileForge Logic Distillation.

This module implements A priori power analysis to determine the required
sample size (N) for statistical tests (specifically McNemar's test for
paired binary outcomes) to achieve a desired statistical power.

It adheres to the Constitution Principle I (Environment Variables) for
configuration and Constitution Principle III (State Management) for
artifact versioning.
"""

import json
import math
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Import project root helper from env_manager to ensure consistent pathing
from utils.env_manager import get_project_root


def calculate_required_n(effect_size: float, alpha: float = 0.05, power: float = 0.80) -> Dict[str, Any]:
    """
    Calculate the required sample size (N) for a paired proportions test (McNemar's).

    This function performs an A priori power analysis. It estimates the number
    of subjects (tasks) needed to detect a specified effect size with a given
    significance level (alpha) and statistical power.

    For McNemar's test on paired binary data, the effect size is often represented
    by the difference in discordant proportions or an odds ratio. This implementation
    uses a normal approximation for the sample size calculation based on the
    difference in proportions (p1 - p2) where p1 and p2 are the success rates
    of the two conditions (Distilled vs Baseline).

    Formula (Normal Approximation for Paired Proportions):
    N = ( (Z_alpha * sqrt(2*P_bar*(1-P_bar)) + Z_beta * sqrt(P_diff)) )^2 / (P_diff)^2
    *Simplified for general power analysis context where effect_size is Cohen's h or similar.*

    Here, we implement a standard approximation for detecting a difference in proportions
    assuming a balanced design and using the standard normal distribution.

    Args:
        effect_size (float): The expected effect size (e.g., Cohen's h or difference in proportions).
        alpha (float): Significance level (default 0.05).
        power (float): Desired statistical power (default 0.80).

    Returns:
        dict: A dictionary containing:
            - 'validated_n': int (The calculated minimum sample size, rounded up)
            - 'effect_size': float (The input effect size)
            - 'power': float (The input power)
            - 'alpha': float (The input alpha)
            - 'method': str (Description of the method used)

    Raises:
        ValueError: If inputs are out of valid ranges.
    """
    if not (0 < alpha < 1):
        raise ValueError(f"Alpha must be between 0 and 1, got {alpha}")
    if not (0 < power < 1):
        raise ValueError(f"Power must be between 0 and 1, got {power}")
    if effect_size <= 0:
        raise ValueError(f"Effect size must be positive, got {effect_size}")

    # Z-scores
    # Z_alpha for two-tailed test (standard for McNemar's)
    z_alpha = abs(math.erfcinv(alpha) * math.sqrt(2))
    # Z_beta for power (1 - beta)
    z_beta = abs(math.erfcinv(2 * (1 - power)) * math.sqrt(2))

    # Calculation for difference in proportions (approximation)
    # N = ( (Z_alpha + Z_beta)^2 * (p1*(1-p1) + p2*(1-p2)) ) / (p1 - p2)^2
    # Since we are given an abstract 'effect_size', we treat it as the standardized
    # difference (Cohen's h) or a direct proportion difference for the approximation.
    # Using the standard formula for sample size given effect size (h):
    # N = ( (Z_alpha + Z_beta) / effect_size )^2
    # This is a conservative estimate for the number of pairs needed.

    numerator = (z_alpha + z_beta) ** 2
    n = numerator / (effect_size ** 2)

    # Round up to the nearest integer
    validated_n = math.ceil(n)

    return {
        'validated_n': validated_n,
        'effect_size': effect_size,
        'power': power,
        'alpha': alpha,
        'method': 'A priori power analysis (Normal Approximation for Paired Proportions)'
    }


def write_validated_n(result: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Write the power analysis result to the state directory.

    Args:
        result (dict): The dictionary returned by calculate_required_n.
        output_path (Optional[Path]): Explicit path to write the file. If None,
            defaults to state/validated_n.json within the project root.

    Returns:
        Path: The path to the written JSON file.

    Raises:
        IOError: If the file cannot be written.
    """
    if output_path is None:
        project_root = get_project_root()
        state_dir = project_root / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        output_path = state_dir / "validated_n.json"
    else:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        return output_path
    except IOError as e:
        raise IOError(f"Failed to write validated_n.json to {output_path}: {e}")


def main() -> None:
    """
    Main entry point for the power analysis script.

    Reads configuration from environment variables or uses defaults:
    - POWER_EFFECT_SIZE: Expected effect size (default 0.3, medium effect)
    - POWER_ALPHA: Significance level (default 0.05)
    - POWER_POWER: Desired power (default 0.80)

    Calculates N and writes to state/validated_n.json.
    """
    import os

    # Default values
    default_effect_size = 0.3
    default_alpha = 0.05
    default_power = 0.80

    # Load from environment if set
    effect_size = float(os.getenv('POWER_EFFECT_SIZE', default_effect_size))
    alpha = float(os.getenv('POWER_ALPHA', default_alpha))
    power = float(os.getenv('POWER_POWER', default_power))

    print(f"Running A priori power analysis...")
    print(f"  Effect Size: {effect_size}")
    print(f"  Alpha: {alpha}")
    print(f"  Power: {power}")

    try:
        result = calculate_required_n(effect_size, alpha, power)
        output_path = write_validated_n(result)
        print(f"Calculation complete.")
        print(f"  Required N: {result['validated_n']}")
        print(f"  Output written to: {output_path}")
    except ValueError as e:
        print(f"Error: Invalid input parameters. {e}")
        raise
    except IOError as e:
        print(f"Error: Failed to write output. {e}")
        raise


if __name__ == "__main__":
    main()
