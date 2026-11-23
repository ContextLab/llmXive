import os
import json
import logging
from typing import Dict, Any, Optional
from utils.logging import get_logger

logger = get_logger(__name__)

def check_sample_size_power(n_samples: int, threshold: int = 50) -> Dict[str, Any]:
    """
    Check if the sample size is sufficient for statistical power.
    
    Args:
        n_samples: The number of samples in the dataset.
        threshold: The minimum number of samples required (default 50).
        
    Returns:
        A dictionary with status information.
    """
    if n_samples < threshold:
        logger.warning(f"INSUFFICIENT_POWER: N={n_samples} < {threshold}")
        return {
            "status": "insufficient_power",
            "n_samples": n_samples,
            "threshold": threshold,
            "message": f"Sample size {n_samples} is below the required threshold of {threshold} for reliable statistical analysis."
        }
    else:
        return {
            "status": "sufficient_power",
            "n_samples": n_samples,
            "threshold": threshold,
            "message": f"Sample size {n_samples} meets the requirement of {threshold}."
        }

def write_power_analysis(
    output_path: str,
    status: str,
    n_samples: int,
    threshold: int = 50,
    message: Optional[str] = None
) -> None:
    """
    Write the power analysis results to a JSON file.
    
    Args:
        output_path: Path to the output JSON file.
        status: The power status ('sufficient_power' or 'insufficient_power').
        n_samples: The number of samples analyzed.
        threshold: The threshold used for the check.
        message: Optional detailed message.
    """
    result = {
        "status": status,
        "n_samples": n_samples,
        "threshold": threshold,
    }
    if message:
        result["message"] = message
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Power analysis results written to {output_path}")

def main():
    """
    Main entry point for the power analysis script.
    This script is typically called by the evaluation pipeline.
    """
    # Example usage - in practice, n_samples would be passed from the pipeline
    # or read from the processed data
    import sys
    if len(sys.argv) < 2:
        logger.error("Usage: python code/models/power_analysis.py <n_samples> [output_path]")
        sys.exit(1)
    
    try:
        n_samples = int(sys.argv[1])
    except ValueError:
        logger.error(f"Invalid n_samples value: {sys.argv[1]}")
        sys.exit(1)
    
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output/power_analysis.json"
    
    power_status = check_sample_size_power(n_samples)
    write_power_analysis(
        output_path=output_path,
        status=power_status["status"],
        n_samples=power_status["n_samples"],
        threshold=power_status["threshold"],
        message=power_status.get("message")
    )

if __name__ == "__main__":
    main()