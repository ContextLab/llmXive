import csv
import json
import logging
import os
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

def format_p_value(p_value: float) -> str:
    """
    Format a p-value.
    
    Args:
        p_value: P-value.
        
    Returns:
        Formatted string.
    """
    return f"{p_value:.4f}"

def format_effect_size(effect_size: float) -> str:
    """
    Format an effect size.
    
    Args:
        effect_size: Effect size.
        
    Returns:
        Formatted string.
    """
    return f"{effect_size:.4f}"

def format_significance(p_value: float) -> str:
    """
    Format significance.
    
    Args:
        p_value: P-value.
        
    Returns:
        'Significant' or 'Not Significant'.
    """
    return "Significant" if p_value < 0.05 else "Not Significant"

def generate_table_markdown(
    results: List[Dict[str, Any]], 
    output_path: Path
) -> None:
    """
    Generate a markdown table of sensitivity results.
    
    Args:
        results: List of results.
        output_path: Output file path.
    """
    ensure_dir(output_path.parent)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("| Threshold | Accuracy Bin 1 | Accuracy Bin 2 | Effect Size | Significance |\n")
        f.write("|-----------|----------------|----------------|-------------|--------------|\n")
        
        for res in results:
            sig = format_significance(res.get('p_value', 0.5))
            f.write(f"| {res['threshold']} | {res['accuracy_bin1']} | {res['accuracy_bin2']} | {format_effect_size(res['effect_size'])} | {sig} |\n")
            
    logger.info(f"Markdown table saved to {output_path}")

def generate_table_csv(
    results: List[Dict[str, Any]], 
    output_path: Path
) -> None:
    """
    Generate a CSV table of sensitivity results.
    
    Args:
        results: List of results.
        output_path: Output file path.
    """
    ensure_dir(output_path.parent)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['threshold', 'accuracy_bin1', 'accuracy_bin2', 'effect_size', 'significance'])
        writer.writeheader()
        
        for res in results:
            row = res.copy()
            row['significance'] = format_significance(res.get('p_value', 0.5))
            writer.writerow(row)
            
    logger.info(f"CSV table saved to {output_path}")

def main() -> None:
    """Main entry point for table generation."""
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "sensitivity_results.json"
    md_output = project_root / "data" / "processed" / "sensitivity_table.md"
    csv_output = project_root / "data" / "processed" / "sensitivity_table.csv"
    
    if not input_path.exists():
        logger.error("Sensitivity results not found.")
        sys.exit(1)
        
    results = load_sensitivity_results(input_path)
    generate_table_markdown(results, md_output)
    generate_table_csv(results, csv_output)

if __name__ == "__main__":
    main()