"""
Ceiling Effect Detection Module.

Implements logic to detect and report a 'ceiling effect' if the
Random Forest Baseline R-squared exceeds a defined threshold (0.95).
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from evaluation.report_generator import load_baseline_metrics

logger = logging.getLogger(__name__)

# Default threshold for ceiling effect
DEFAULT_CEILING_THRESHOLD = 0.95

def load_baseline_r2(metrics_path: Optional[str] = None) -> float:
    """
    Loads the R-squared value from the baseline metrics file.
    
    Args:
        metrics_path: Optional path to the baseline metrics JSON. 
                      If None, defaults to 'results/baseline_metrics.json'.
                      
    Returns:
        float: The R-squared value.
    
    Raises:
        FileNotFoundError: If the metrics file does not exist.
        KeyError: If 'r2' is missing from the metrics.
    """
    if metrics_path is None:
        metrics_path = str(project_root / "results" / "baseline_metrics.json")
    
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Baseline metrics file not found at {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    if 'r2' not in data:
        raise KeyError("Baseline metrics file missing 'r2' key.")
    
    return float(data['r2'])

def detect_ceiling_effect(r2_value: float, threshold: float = DEFAULT_CEILING_THRESHOLD) -> Dict[str, Any]:
    """
    Determines if a ceiling effect is present based on R-squared.
    
    Args:
        r2_value: The R-squared value of the baseline model.
        threshold: The threshold above which a ceiling effect is detected (default 0.95).
        
    Returns:
        A dictionary containing the detection result and details.
    """
    is_ceiling = r2_value > threshold
    
    result = {
        "detected": is_ceiling,
        "baseline_r2": r2_value,
        "threshold": threshold,
        "message": ""
    }
    
    if is_ceiling:
        result["message"] = (
            f"Ceiling effect detected: Baseline R² ({r2_value:.4f}) exceeds "
            f"threshold ({threshold}). The baseline model performance is near-perfect, "
            f"leaving little room for the GNN to demonstrate improvement."
        )
    else:
        result["message"] = (
            f"No ceiling effect detected: Baseline R² ({r2_value:.4f}) is below "
            f"threshold ({threshold})."
        )
        
    logger.info(result["message"])
    return result

def save_ceiling_report(report: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """
    Saves the ceiling effect detection report to a JSON file.
    
    Args:
        report: The dictionary containing the detection result.
        output_path: Optional path for the output file. Defaults to 'results/ceiling_effect.json'.
    """
    if output_path is None:
        output_path = str(project_root / "results" / "ceiling_effect.json")
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=4)
    
    logger.info(f"Ceiling effect report saved to {output_path}")

def main():
    """
    Entry point for the ceiling effect detection script.
    """
    parser = argparse.ArgumentParser(description="Detect ceiling effect in baseline model performance.")
    parser.add_argument(
        "--metrics-path", 
        type=str, 
        default=None,
        help="Path to baseline_metrics.json (default: results/baseline_metrics.json)"
    )
    parser.add_argument(
        "--output-path", 
        type=str, 
        default=None,
        help="Path for output report (default: results/ceiling_effect.json)"
    )
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=DEFAULT_CEILING_THRESHOLD,
        help=f"R² threshold for ceiling effect (default: {DEFAULT_CEILING_THRESHOLD})"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        logger.info("Loading baseline R-squared...")
        r2 = load_baseline_r2(args.metrics_path)
        
        logger.info(f"Baseline R²: {r2:.4f}")
        
        logger.info(f"Checking for ceiling effect (threshold: {args.threshold})...")
        report = detect_ceiling_effect(r2, args.threshold)
        
        save_ceiling_report(report, args.output_path)
        
        print(report["message"])
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except KeyError as e:
        logger.error(f"Invalid metrics format: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()