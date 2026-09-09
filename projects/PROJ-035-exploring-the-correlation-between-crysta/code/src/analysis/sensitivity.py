import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np

# Import seed utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.seed_manager import init_seed, add_seed_argument

def setup_logger_module(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger_module(__name__)

def run_sensitivity_analysis(correlation_results: Dict, thresholds: List[float] = [0.01, 0.05, 0.1], seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Run sensitivity analysis on p-value thresholds.
    Returns headline rates for each threshold.
    """
    init_seed(seed)
    results = {}
    for threshold in thresholds:
        significant_count = 0
        total_count = 0
        
        for class_name, data in correlation_results.items():
            p_vals = data.get('p_values', {})
            for p in p_vals.values():
                total_count += 1
                if p < threshold:
                    significant_count += 1
        
        rate = significant_count / total_count if total_count > 0 else 0.0
        results[str(threshold)] = {
            "significant_count": significant_count,
            "total_count": total_count,
            "rate": rate
        }
    return results

def save_sensitivity_report(results: Dict, output_path: Path) -> None:
    """Save sensitivity report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Sensitivity report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Sensitivity Analysis")
    add_seed_argument(parser)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    
    init_seed(args.seed)
    
    import json
    with open(args.input, 'r') as f:
        correlation_results = json.load(f)
    
    results = run_sensitivity_analysis(correlation_results, seed=args.seed)
    save_sensitivity_report(results, args.output)

if __name__ == "__main__":
    main()
