"""
Power analysis script.
Implements T048.
"""
import os
import sys
import json
import logging
import numpy as np
from statsmodels.stats.power import GofChisquarePower
from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("power_analysis")

def calculate_power_f2(effect_size_f2: float = 0.15, alpha: float = 0.05, target_power: float = 0.80, n: int = 500) -> dict:
    """Calculate power for mixed-effects logistic regression approximation."""
    # Using GofChisquarePower as an approximation
    power_analysis = GofChisquarePower()
    # nobs = n * k (where k is number of observations per user, e.g., weeks)
    # Approximate with total N
    nobs = n * 10 # Assume 10 weeks
    
    try:
        power = power_analysis.solve_power(effect_size=effect_size_f2, nobs1=nobs, alpha=alpha, alternative='larger')
    except Exception:
        power = 0.0
        
    status = "low" if power < target_power else "sufficient"
    
    return {
        "estimated_power": float(power),
        "effect_size": effect_size_f2,
        "sample_size": n,
        "power_status": status
    }

def main():
    """Main entry point."""
    result = calculate_power_f2()
    
    output_path = "data/processed/power_analysis_report.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    if result['power_status'] == 'low':
        logger.warning("Power < 0.80 detected. Study proceeds with exploratory caveats.")
    else:
        logger.info("Power analysis complete.")

if __name__ == "__main__":
    main()
