import json
import sys
import math
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import yaml

# Ensure we can import from the project root if running as script
# The task assumes the script is run from the project root or code/
# We will resolve paths relative to the project root structure

def get_project_root() -> Path:
    """Returns the root of the llmXive project."""
    # Assuming standard structure: code/analysis/power_analysis.py
    # Root is 2 levels up from this file
    return Path(__file__).resolve().parent.parent.parent

def load_config() -> Dict[str, Any]:
    """Loads the config.yaml from the code directory."""
    config_path = get_project_root() / "code" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}. "
                                "Run T000_CONFIG and T001 first.")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def compute_effect_size(effect_size_cohen_d: float = 0.5) -> float:
    """
    Returns the effect size (Cohen's d) to be used for power analysis.
    Default is 0.5 (medium effect size).
    """
    return effect_size_cohen_d

def perform_power_analysis(
    effect_size: float,
    alpha: float = 0.05,
    power_target: float = 0.80,
    num_groups: int = 2,
    seeds_per_group: int = 5
) -> Tuple[float, int]:
    """
    Performs a statistical power analysis to determine if the planned number of seeds
    is sufficient to detect the given effect size with the target power.

    Uses the standard formula for power in a two-sample t-test (approximate for ANOVA contexts
    in experimental design of multiple seeds).
    
    Formula:
    n = 2 * ((Z_alpha + Z_beta) / d)^2
    
    Where:
    - n is the sample size per group
    - d is Cohen's d (effect size)
    - Z_alpha is the critical value for significance level (one-tailed or two-tailed)
    - Z_beta is the critical value for power (1 - beta)

    Returns:
        Tuple[calculated_power, required_seeds_per_group]
    """
    # Z-scores for standard normal distribution
    # For alpha = 0.05 (two-tailed), Z_alpha/2 = 1.96
    z_alpha = 1.96 
    # For target power = 0.80, beta = 0.20, Z_beta = 0.84
    z_beta_target = 0.84

    # Calculate required sample size per group for the target power
    # n = 2 * ((Z_alpha + Z_beta) / d)^2
    if effect_size <= 0:
        raise ValueError("Effect size must be positive.")
    
    n_required = 2 * math.pow((z_alpha + z_beta_target) / effect_size, 2)
    required_seeds = int(math.ceil(n_required))
    
    # If the planned seeds (seeds_per_group) is less than required, calculate actual power
    # Actual power Z_beta = (d * sqrt(n/2)) - Z_alpha
    # power = Phi(Z_beta)
    
    planned_n = seeds_per_group
    if planned_n <= 0:
        raise ValueError("Number of seeds must be positive.")

    # Calculate Z_beta for the planned sample size
    z_beta_planned = (effect_size * math.sqrt(planned_n / 2)) - z_alpha
    
    # Calculate actual power using cumulative distribution function (CDF) of normal distribution
    # Using scipy.stats.norm.cdf would be ideal, but to avoid extra deps if not strictly needed,
    # we can use math.erf or assume scipy is available (it is in requirements.txt).
    # Given requirements.txt includes scipy, we use it for accuracy.
    from scipy.stats import norm
    actual_power = norm.cdf(z_beta_planned)

    return actual_power, required_seeds

def main():
    """
    Main entry point for Power Analysis.
    
    Logic:
    1. Read 'regime' and 'token_target' from code/config.yaml.
    2. Use a fixed effect size (Cohen's d = 0.5).
    3. Assume 5 seeds per group (AR vs MDM) as per project plan.
    4. Compute statistical power.
    5. Write data/artifacts/power_analysis.json.
    6. Raise FatalError if power < 0.8.
    """
    project_root = get_project_root()
    artifacts_dir = project_root / "data" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = artifacts_dir / "power_analysis.json"

    try:
        config = load_config()
        regime = config.get("regime")
        token_target = config.get("token_target")
        
        if regime is None:
            raise ValueError("Config missing 'regime'.")
        if token_target is None:
            raise ValueError("Config missing 'token_target'.")

        # Constants
        EFFECT_SIZE = 0.5
        ALPHA = 0.05
        TARGET_POWER = 0.80
        SEEDS_PER_GROUP = 5
        NUM_GROUPS = 2 # AR vs MDM

        # Perform analysis
        calculated_power, required_seeds = perform_power_analysis(
            effect_size=EFFECT_SIZE,
            alpha=ALPHA,
            power_target=TARGET_POWER,
            num_groups=NUM_GROUPS,
            seeds_per_group=SEEDS_PER_GROUP
        )

        status = "PASS" if calculated_power >= TARGET_POWER else "FAIL"
        
        result = {
            "status": status,
            "power_value": float(calculated_power),
            "effect_size_used": float(EFFECT_SIZE),
            "required_seeds": required_seeds,
            "planned_seeds": SEEDS_PER_GROUP,
            "regime": regime,
            "token_target": token_target,
            "alpha": ALPHA,
            "target_power": TARGET_POWER
        }

        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)

        print(f"Power analysis complete. Output written to {output_path}")
        print(f"Calculated Power: {calculated_power:.4f} (Target: {TARGET_POWER})")
        print(f"Status: {status}")

        if calculated_power < TARGET_POWER:
            # FatalError as per task requirement
            raise SystemExit(f"FATAL: Statistical power ({calculated_power:.4f}) is below threshold ({TARGET_POWER}). "
                             f"Required seeds per group: {required_seeds}, Planned: {SEEDS_PER_GROUP}.")
            
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(1)
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    sys.exit(main())