import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

from utils.config import get_project_root, get_path, ensure_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_sensitivity_results(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load sensitivity results from JSON.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        List of results.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_robustness(
    results: List[Dict[str, Any]], 
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Calculate robustness metric.
    
    Args:
        results: List of results.
        alpha: Significance level.
        
    Returns:
        Dictionary with robustness metrics.
    """
    significant_count = sum(1 for res in results if res.get('p_value', 1.0) < alpha)
    total_count = len(results)
    
    return {
        "significant_count": significant_count,
        "total_count": total_count,
        "robustness_status": "PASS" if significant_count >= 2 else "FAIL"
    }

def save_stability_metric(
    metric: Dict[str, Any], 
    output_path: Path
) -> None:
    """
    Save stability metric to JSON.
    
    Args:
        metric: Metric dictionary.
        output_path: Output file path.
    """
    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metric, f, indent=2)
    logger.info(f"Stability metric saved to {output_path}")

def main() -> None:
    """Main entry point for stability metric generation."""
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "sensitivity_results.json"
    output_path = project_root / "data" / "processed" / "stability_metric.json"
    
    if not input_path.exists():
        logger.error("Sensitivity results not found.")
        sys.exit(1)
        
    results = load_sensitivity_results(input_path)
    metric = calculate_robustness(results)
    save_stability_metric(metric, output_path)

if __name__ == "__main__":
    main()