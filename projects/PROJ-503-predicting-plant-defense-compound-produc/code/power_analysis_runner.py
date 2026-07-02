"""
Power Analysis Runner for T015.

Executes the power analysis utility defined in T009 to determine the required
sample size (n) for detecting an effect size of r=0.5 with alpha=0.05 and power=0.8.

If the calculated n is less than 28, the script aborts with E-POWER error code
as per Plan T009/T015 and FR-009.
If n >= 28, it logs the result to logs/power_analysis.json and exits successfully.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from code.power_analysis import calculate_required_n, run_power_analysis
from code.exceptions import E_POWER
from code.error_handler import raise_power_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'power_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for T015.
    Runs power analysis and enforces the n >= 28 abort condition.
    """
    logger.info("Starting Power Analysis for T015...")
    
    # Parameters per spec
    effect_size = 0.5
    alpha = 0.05
    power = 0.8
    
    try:
        # Calculate required n
        n_required = calculate_required_n(effect_size, alpha, power)
        
        logger.info(f"Calculated required sample size (n): {n_required}")
        
        # Abort condition: n < 28
        if n_required < 28:
            logger.error(f"Power analysis failed: Required n ({n_required}) is less than minimum threshold (28).")
            logger.error("Aborting project with E-POWER error code.")
            
            # Raise the specific power error which handles logging and exit
            raise_power_error(
                reason=f"Required sample size ({n_required}) is below minimum threshold (28) for effect size r={effect_size}.",
                effect_size=effect_size,
                alpha=alpha,
                power=power,
                required_n=n_required,
                threshold=28
            )
            # raise_power_error exits the program, but we keep this for safety
            sys.exit(1)
        
        # Success path: n >= 28
        logger.info(f"Power analysis passed: Required n ({n_required}) meets threshold (>= 28).")
        
        # Prepare output data
        output_data: Dict[str, Any] = {
            "task_id": "T015",
            "parameters": {
                "effect_size_r": effect_size,
                "alpha": alpha,
                "power": power
            },
            "result": {
                "required_sample_size_n": n_required,
                "threshold_met": True,
                "threshold_value": 28
            },
            "status": "PASS",
            "message": f"Required sample size n={n_required} is sufficient (>= 28). Proceeding to T016."
        }
        
        # Ensure logs directory exists
        logs_dir = project_root / 'logs'
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = logs_dir / 'power_analysis.json'
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Power analysis results written to {output_path}")
        logger.info("T015 completed successfully. Ready for T016.")
        
    except Exception as e:
        logger.error(f"Unexpected error during power analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
