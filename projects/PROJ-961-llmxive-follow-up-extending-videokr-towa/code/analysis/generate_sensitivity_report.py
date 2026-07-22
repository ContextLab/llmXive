import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

from utils.config import get_project_root, get_path, ensure_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_sensitivity_json(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load sensitivity results from JSON.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        List of results.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_markdown_report(
    results: List[Dict[str, Any]], 
    output_path: Path
) -> None:
    """
    Generate a markdown report of sensitivity analysis.
    
    Args:
        results: List of results.
        output_path: Output file path.
    """
    ensure_dir(output_path.parent)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Sensitivity Analysis Report\n\n")
        f.write("## Threshold Sweep Results\n\n")
        f.write("| Threshold | Accuracy Bin 1 | Accuracy Bin 2 | Effect Size | n Bin 1 | n Bin 2 |\n")
        f.write("|-----------|----------------|----------------|-------------|---------|---------|\n")
        
        for res in results:
            f.write(f"| {res['threshold']} | {res['accuracy_bin1']} | {res['accuracy_bin2']} | {res['effect_size']} | {res['n_bin1']} | {res['n_bin2']} |\n")
            
        f.write("\n## Robustness Conclusion\n\n")
        
        # Count significant thresholds (p < 0.05)
        # Placeholder: assuming effect_size > 0.1 is significant
        significant_count = sum(1 for res in results if abs(res['effect_size']) > 0.1)
        
        if significant_count >= 2:
            f.write("Robust\n")
        else:
            f.write("Not Robust\n")
            
    logger.info(f"Report saved to {output_path}")

def main() -> None:
    """Main entry point for report generation."""
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "sensitivity_results.json"
    output_path = project_root / "data" / "processed" / "sensitivity_report.md"
    
    if not input_path.exists():
        logger.error("Sensitivity results not found.")
        sys.exit(1)
        
    results = load_sensitivity_json(input_path)
    generate_markdown_report(results, output_path)

if __name__ == "__main__":
    main()