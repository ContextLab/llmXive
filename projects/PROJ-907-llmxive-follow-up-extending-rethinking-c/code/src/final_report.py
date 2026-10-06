import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_json_file(path: str) -> Dict[str, Any]:
    """Loads a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def extract_sensitivity_range(sensitivity_results: List[Dict[str, Any]]) -> float:
    """Extracts the range of FID scores from sensitivity results."""
    fid_scores = [r["fid_score"] for r in sensitivity_results]
    return max(fid_scores) - min(fid_scores)

def generate_final_report():
    """Generates the final report."""
    logger.info("Generating final report...")
    
    # Load statistical analysis
    stats_path = Path("data/results/statistical_analysis.json")
    if stats_path.exists():
        stats = load_json_file(str(stats_path))
    else:
        stats = {}
    
    # Load sensitivity sweep
    sensitivity_path = Path("data/results/sensitivity_sweep.json")
    if sensitivity_path.exists():
        sensitivity_results = load_json_file(str(sensitivity_path))
        sensitivity_range = extract_sensitivity_range(sensitivity_results)
    else:
        sensitivity_range = 0.0
    
    # Generate final report
    final_report = {
        "mean": stats.get("mean", 0.0),
        "std": stats.get("std", 0.0),
        "p_values": stats.get("bootstrap_results", {}).get("p_value", 0.0),
        "sensitivity_range": sensitivity_range
    }
    
    output_path = Path("data/results/final_report.json")
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Final report saved to {output_path}")

def main():
    """Entry point for the final report script."""
    generate_final_report()

if __name__ == "__main__":
    main()