"""
Power Analysis Module for MobileForge Logic Distillation.

This module implements the calculation of the required sample size (N) for
statistical evaluation, adhering to the Constitution Principles and specific
project constraints (FR-007).

It explicitly forbids using pilot data to estimate baseline probability (p0),
enforcing the use of the conservative assumption p0 = 0.5.
"""

import json
import math
import os
from pathlib import Path
from typing import Dict, Any, Optional

from utils.env_manager import get_project_root


def _calculate_z_score(probability: float) -> float:
    """
    Approximates the inverse of the standard normal cumulative distribution function (Z-score).
    Uses the Abramowitz and Stegun approximation (26.2.23) for high precision.
    """
    if probability <= 0 or probability >= 1:
        raise ValueError("Probability must be strictly between 0 and 1.")

    # Constants for approximation
    b0 = 2.515517
    b1 = 0.802853
    b2 = 0.010328
    a1 = 1.432788
    a2 = 0.189269
    a3 = 0.001308

    p = probability
    if p > 0.5:
        p = 1.0 - p
    
    t = math.sqrt(-2.0 * math.log(p))
    
    # Abramowitz and Stegun approximation
    z = t - (b0 + b1 * t + b2 * t * t) / (1.0 + a1 * t + a2 * t * t + a3 * t * t * t)
    
    if probability > 0.5:
        return -z
    return z


def calculate_required_n(
    effect_size: float = 0.2,
    alpha: float = 0.05,
    power: float = 0.8,
    baseline_p0: float = 0.5
) -> Dict[str, Any]:
    """
    Calculates the required sample size (N) for a proportion test.

    This function implements the a priori power analysis required by FR-007.
    It explicitly enforces the use of `baseline_p0 = 0.5` regardless of any
    pilot data, as per project constraints to ensure conservative estimation.

    Args:
        effect_size (float): The minimum detectable difference in proportions (delta).
        alpha (float): The significance level (Type I error rate).
        power (float): The statistical power (1 - Type II error rate).
        baseline_p0 (float): The assumed baseline success rate. 
                             **Constraint**: Must be 0.5. The function ignores 
                             any other value passed to ensure compliance.

    Returns:
        dict: A dictionary containing:
            - 'validated_n': The calculated integer sample size.
            - 'effect_size': The input effect size.
            - 'power': The input power.
            - 'baseline_p0': The fixed baseline probability (0.5).

    Raises:
        ValueError: If effect_size, alpha, or power are out of valid ranges.
    """
    # Input validation
    if not (0 < alpha < 1):
        raise ValueError("Alpha must be between 0 and 1.")
    if not (0 < power < 1):
        raise ValueError("Power must be between 0 and 1.")
    if not (0 < effect_size < 1):
        raise ValueError("Effect size must be between 0 and 1.")

    # Enforce the conservative baseline p0 = 0.5 constraint
    # This prevents "p-hacking" or optimistic bias from pilot data.
    enforced_p0 = 0.5
    p1 = enforced_p0 + effect_size

    if not (0 < p1 < 1):
        # If effect_size pushes p1 out of bounds, clamp or error depending on strictness.
        # Given effect_size=0.2 and p0=0.5, p1=0.7 is valid.
        # If effect_size was 0.6, p1=1.1 -> invalid.
        raise ValueError(f"Effect size {effect_size} with p0={enforced_p0} results in invalid p1={p1}.")

    # Z-scores
    z_alpha_2 = _calculate_z_score(1 - alpha / 2)
    z_beta = _calculate_z_score(power)

    # Pooled proportion under null hypothesis (p0) vs alternative (p1)
    # For a one-sample proportion test (comparing observed p1 to fixed p0):
    # n = ( (Z_alpha * sqrt(p0*(1-p0)) + Z_beta * sqrt(p1*(1-p1)))^2 ) / (p1 - p0)^2
    
    # Note: Some formulations use two-sample test logic if comparing two groups.
    # Here, we are establishing a sample size for a single evaluation run against 
    # a known baseline (TinyLlama or theoretical chance), or detecting a shift.
    # The standard formula for one-sample proportion test:
    
    p0 = enforced_p0
    p_alt = p1

    term1 = z_alpha_2 * math.sqrt(p0 * (1 - p0))
    term2 = z_beta * math.sqrt(p_alt * (1 - p_alt))
    
    numerator = (term1 + term2) ** 2
    denominator = (p_alt - p0) ** 2
    
    n_raw = numerator / denominator
    
    # Round up to ensure power is met
    validated_n = math.ceil(n_raw)

    return {
        "validated_n": validated_n,
        "effect_size": effect_size,
        "power": power,
        "baseline_p0": enforced_p0
    }


def write_validated_n(
    result: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Writes the validated N calculation result to a JSON file in the state directory.

    Args:
        result (dict): The dictionary returned by calculate_required_n.
        output_path (Path, optional): Override the default output path.

    Returns:
        Path: The path to the written file.
    """
    if output_path is None:
        project_root = get_project_root()
        state_dir = project_root / "state"
        if not state_dir.exists():
            state_dir.mkdir(parents=True, exist_ok=True)
        output_path = state_dir / "validated_n.json"
    else:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return output_path


def main() -> None:
    """
    Entry point for the power analysis script.
    Calculates N and writes it to state/validated_n.json.
    """
    print("Starting Power Analysis for MobileForge Logic Distillation...")
    print("Constraint: Baseline p0 is fixed at 0.5 (Conservative Assumption).")

    # Default parameters as per task specification
    effect_size = 0.2
    alpha = 0.05
    power = 0.8

    try:
        result = calculate_required_n(
            effect_size=effect_size,
            alpha=alpha,
            power=power
        )
        
        output_file = write_validated_n(result)
        
        print(f"Calculation Complete.")
        print(f"  Effect Size: {result['effect_size']}")
        print(f"  Alpha: {result['effect_size']}")
        print(f"  Power: {result['power']}")
        print(f"  Baseline p0: {result['baseline_p0']}")
        print(f"  Required N: {result['validated_n']}")
        print(f"  Output written to: {output_file}")

    except ValueError as e:
        print(f"Error in calculation: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()