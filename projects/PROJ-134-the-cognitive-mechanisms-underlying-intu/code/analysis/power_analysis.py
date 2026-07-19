import os
import sys
import math
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import yaml
import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants from plan.md
N_PARTICIPANTS = 200
N_VIGNETTES = 50
SIGMA = 1.0  # Standard deviation
ALPHA = 0.05  # Significance level
POWER_TARGET = 0.80  # Target power (standard)

def calculate_standard_error(n: int, m: int, sigma: float) -> float:
    """
    Calculate the standard error of the fixed effect estimate in a mixed-effects model.
    
    For a simple random intercept model with balanced design:
    SE(beta) = sigma / sqrt(N * J) * sqrt(1 + (J * sigma_u^2) / sigma^2)
    
    For estimation purposes assuming negligible random slope variance and
    focusing on the fixed effect of a binary predictor (salience) with equal groups:
    SE ≈ sigma / sqrt(N * J / 2) * sqrt(2) = sigma * 2 / sqrt(N * J)
    
    However, a more robust approximation for the standard error of a fixed effect
    in a mixed model with N subjects and J items is:
    SE ≈ sigma / sqrt(N * J) * sqrt(2) (for binary predictor with 50/50 split)
    
    We use the simplified formula: SE = sigma * sqrt(2 / (N * J))
    This assumes the variance is dominated by residual error and balanced design.
    
    Args:
        n: Number of participants
        m: Number of vignettes
        sigma: Residual standard deviation
        
    Returns:
        Standard error of the effect estimate
    """
    if n <= 0 or m <= 0:
        raise ValueError("n and m must be positive")
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    
    # Standard error for a fixed effect in a balanced mixed model
    # SE = sigma * sqrt(2 / (N * J)) for a binary predictor
    se = sigma * math.sqrt(2.0 / (n * m))
    return se

def calculate_mdes(se: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """
    Calculate the Minimum Detectable Effect Size (MDES).
    
    MDES = (Z_(1-alpha/2) + Z_(power)) * SE
    
    Args:
        se: Standard error of the estimate
        alpha: Significance level
        power: Target statistical power
        
    Returns:
        Minimum Detectable Effect Size
    """
    # Z-scores for standard normal distribution
    z_alpha = 1.96  # Approximate Z for 0.05/2 two-tailed
    z_power = 0.84  # Approximate Z for 0.80 power
    
    # More precise calculation using scipy if available, else use approximations
    try:
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha / 2)
        z_power = norm.ppf(power)
    except ImportError:
        logger.warning("scipy not available, using approximate Z-scores")
    
    mdes = (z_alpha + z_power) * se
    return mdes

def run_power_analysis(
    n: int = N_PARTICIPANTS,
    m: int = N_VIGNETTES,
    sigma: float = SIGMA,
    alpha: float = ALPHA,
    power: float = POWER_TARGET
) -> Dict[str, Any]:
    """
    Run the full power analysis calculation.
    
    Args:
        n: Number of participants
        m: Number of vignettes
        sigma: Residual standard deviation
        alpha: Significance level
        power: Target power
        
    Returns:
        Dictionary containing analysis results
    """
    logger.info(f"Running power analysis with N={n}, M={m}, sigma={sigma}")
    
    se = calculate_standard_error(n, m, sigma)
    mdes = calculate_mdes(se, alpha, power)
    
    result = {
        "parameters": {
            "n_participants": n,
            "n_vignettes": m,
            "residual_sd": sigma,
            "alpha": alpha,
            "target_power": power
        },
        "results": {
            "standard_error": se,
            "minimum_detectable_effect_size": mdes,
            "z_alpha": 1.96 if 'scipy' not in sys.modules else None, # Placeholder, updated in actual run
            "z_power": 0.84 if 'scipy' not in sys.modules else None
        },
        "interpretation": {
            "sample_size_adequate": mdes < 0.5, # Heuristic: MDES < 0.5 is often acceptable
            "recommendation": "Proceed with simulation if ground_truth > MDES"
        }
    }
    
    return result

def validate_ground_truth_effect(
    mdes: float,
    ground_truth_effect: float
) -> Tuple[bool, str]:
    """
    Validate if the ground truth effect is above the MDES threshold.
    
    Args:
        mdes: Minimum Detectable Effect Size
        ground_truth_effect: The known effect size in the simulation
        
    Returns:
        Tuple of (is_valid, message)
    """
    if ground_truth_effect > mdes:
        return True, f"Ground truth effect ({ground_truth_effect:.4f}) > MDES ({mdes:.4f}). Validation is statistically meaningful."
    else:
        return False, f"Ground truth effect ({ground_truth_effect:.4f}) <= MDES ({mdes:.4f}). Validation may lack statistical power."

def generate_report(results: Dict[str, Any], output_path: Path) -> None:
    """
    Generate a YAML report of the power analysis.
    
    Args:
        results: Dictionary containing analysis results
        output_path: Path to write the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try to import scipy for precise Z values if not already done
    z_alpha_val = 1.96
    z_power_val = 0.84
    try:
        from scipy.stats import norm
        z_alpha_val = norm.ppf(1 - 0.05 / 2)
        z_power_val = norm.ppf(0.80)
    except ImportError:
        pass
    
    # Update results with precise Z values if available
    results["results"]["z_alpha"] = z_alpha_val
    results["results"]["z_power"] = z_power_val
    
    report_content = {
        "title": "Power Analysis Report: Mixed-Effects Model",
        "description": "Calculates MDES for N=200 participants, 50 vignettes, SD=1.0",
        "methodology": "Standard error approximation for balanced mixed model with binary predictor",
        **results
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(report_content, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Report written to {output_path}")

def main():
    """Main entry point for power analysis."""
    logger.info("Starting Power Analysis (Task T045)")
    
    # Ensure directories exist
    ensure_directories()
    
    # Run analysis
    results = run_power_analysis()
    
    # Define output path
    output_path = get_path("state", "mdes_report.yaml")
    
    # Generate report
    generate_report(results, output_path)
    
    # Print summary
    print(f"\n=== Power Analysis Summary ===")
    print(f"Participants (N): {results['parameters']['n_participants']}")
    print(f"Vignettes (M): {results['parameters']['n_vignettes']}")
    print(f"Residual SD (sigma): {results['parameters']['residual_sd']}")
    print(f"Standard Error: {results['results']['standard_error']:.6f}")
    print(f"Minimum Detectable Effect Size (MDES): {results['results']['minimum_detectable_effect_size']:.6f}")
    print(f"Report saved to: {output_path}")
    print("==============================\n")
    
    return results

if __name__ == "__main__":
    main()