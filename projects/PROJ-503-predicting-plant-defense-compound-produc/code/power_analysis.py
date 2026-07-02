"""
Power analysis utility for Phase 0.

Calculates required sample size for detecting a correlation effect size (r)
with specified alpha and power. Aborts with E-POWER if required n < 28.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Import from project API surface
from exceptions import E_POWER
from error_handler import raise_power_error

# Setup logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent.parent / 'logs' / 'power_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / 'logs'
OUTPUT_FILE = LOGS_DIR / 'power_analysis.json'

def calculate_required_n(effect_size: float = 0.5, alpha: float = 0.05, power: float = 0.8) -> int:
    """
    Calculate required sample size for Pearson correlation test.
    
    Uses the approximation:
    n = (Z_alpha + Z_beta)^2 / (0.5 * ln((1+r)/(1-r)))^2 + 3
    
    Where:
    - Z_alpha is the critical value for the significance level (one-tailed)
    - Z_beta is the critical value for the desired power
    - r is the effect size (correlation coefficient)
    
    Parameters:
    -----------
    effect_size : float
        Expected correlation coefficient (r). Default 0.5.
    alpha : float
        Significance level. Default 0.05.
    power : float
        Desired statistical power (1 - beta). Default 0.8.
        
    Returns:
    --------
    int
        Required sample size n.
    """
    from scipy import stats
    
    # Calculate Z values
    z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    
    # Fisher's z-transformation of correlation
    # z_r = 0.5 * ln((1+r)/(1-r))
    # Variance of z_r is approximately 1/(n-3)
    # n = (z_alpha + z_beta)^2 / z_r^2 + 3
    
    if abs(effect_size) >= 1.0:
        raise ValueError("Effect size must be between -1 and 1 (exclusive)")
        
    z_r = 0.5 * ((1 + effect_size) / (1 - effect_size)).__float__()
    # Proper calculation using log
    import math
    z_r = 0.5 * math.log((1 + effect_size) / (1 - effect_size))
    
    # Calculate n
    numerator = (z_alpha + z_beta) ** 2
    denominator = z_r ** 2
    n = (numerator / denominator) + 3
    
    return int(math.ceil(n))

def run_power_analysis(
    effect_size: float = 0.5,
    alpha: float = 0.05,
    power: float = 0.8,
    min_required_n: int = 28
) -> Dict[str, Any]:
    """
    Run power analysis and enforce minimum sample size constraint.
    
    Parameters:
    -----------
    effect_size : float
        Target effect size (r).
    alpha : float
        Significance level.
    power : float
        Desired power.
    min_required_n : int
        Minimum required sample size (default 28 per plan.md).
        
    Returns:
    --------
    Dict[str, Any]
        Analysis results including calculated n and status.
        
    Raises:
    -------
    E_POWER
        If calculated n < min_required_n.
    """
    logger.info(f"Running power analysis: effect_size={effect_size}, alpha={alpha}, power={power}")
    
    required_n = calculate_required_n(effect_size, alpha, power)
    
    logger.info(f"Calculated required sample size: n = {required_n}")
    
    result = {
        "effect_size": effect_size,
        "alpha": alpha,
        "power": power,
        "calculated_n": required_n,
        "min_required_n": min_required_n,
        "status": "PASS",
        "message": "Sample size sufficient for planned analysis"
    }
    
    if required_n < min_required_n:
        result["status"] = "FAIL"
        result["message"] = f"Insufficient sample size: calculated n={required_n} < min_required_n={min_required_n}"
        
        # Prepare error details
        error_details = {
            "code": "E-POWER",
            "message": f"Power analysis failed: required n={required_n} is below minimum threshold of {min_required_n}",
            "parameters": {
                "effect_size": effect_size,
                "alpha": alpha,
                "power": power,
                "calculated_n": required_n,
                "min_required_n": min_required_n
            }
        }
        
        logger.error(error_details["message"])
        
        # Ensure logs directory exists
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Write partial results before raising
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(result, f, indent=2)
        
        raise_power_error(
            message=error_details["message"],
            details=error_details
        )
    
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write results to JSON
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Power analysis results written to {OUTPUT_FILE}")
    
    return result

def main():
    """Main entry point for power analysis."""
    try:
        result = run_power_analysis(
            effect_size=0.5,
            alpha=0.05,
            power=0.8,
            min_required_n=28
        )
        
        print(f"Power analysis completed successfully.")
        print(f"Required sample size: n = {result['calculated_n']}")
        print(f"Status: {result['status']}")
        print(f"Output: {OUTPUT_FILE}")
        
        return 0
        
    except E_POWER as e:
        print(f"Power analysis failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during power analysis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
