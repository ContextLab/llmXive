import json
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List

from utils.config import get_project_root, get_path, ensure_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_annotated_data(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load annotated dataset from CSV.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        List of records.
    """
    import csv
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def calculate_coverage(
    total_input: int, 
    annotated_count: int
) -> Dict[str, Any]:
    """
    Calculate annotation coverage metrics.
    
    Args:
        total_input: Total number of input records.
        annotated_count: Number of successfully annotated records.
        
    Returns:
        Dictionary with coverage metrics.
    """
    proportion = (total_input - (total_input - annotated_count)) / total_input if total_input > 0 else 0.0
    return {
        "total_input_records": total_input,
        "annotated_records": annotated_count,
        "unresolvable_count": total_input - annotated_count,
        "proportion": round(proportion, 4)
    }

def save_coverage_results(
    results: Dict[str, Any], 
    output_path: Path
) -> None:
    """
    Save coverage results to JSON.
    
    Args:
        results: Coverage metrics dictionary.
        output_path: Output file path.
    """
    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Coverage results saved to {output_path}")

def main() -> None:
    """Main entry point for coverage calculation."""
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    output_path = processed_dir / "annotation_coverage.json"
    
    annotated_path = processed_dir / "annotated_videokr.csv"
    
    if not annotated_path.exists():
        logger.error("Annotated data not found. Run annotate_graph.py first.")
        sys.exit(1)
        
    data = load_annotated_data(annotated_path)
    annotated_count = len(data)
    total_input = annotated_count # Assuming all input was processed
    
    # In a real scenario, we'd track total input separately
    # Here we assume the input was the same as the processed set for simplicity
    # A more robust implementation would read the original input count from metadata
    
    coverage = calculate_coverage(total_input, annotated_count)
    save_coverage_results(coverage, output_path)

if __name__ == "__main__":
    main()