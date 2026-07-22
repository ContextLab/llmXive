import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional

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
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def bin_hop_length(hop_count: int) -> str:
    """
    Bin the hop count into categorical labels.
    
    Args:
        hop_count: The integer hop count.
        
    Returns:
        Categorical string label.
    """
    if hop_count <= 0:
        return '0'
    elif hop_count == 1:
        return '1'
    elif hop_count == 2:
        return '2'
    else:
        return '3+'

def calculate_accuracy_by_bin(
    data: List[Dict[str, Any]]
) -> Dict[str, Dict[str, int]]:
    """
    Calculate accuracy rate for each hop bin.
    
    Args:
        data: List of annotated records.
        
    Returns:
        Dictionary mapping bins to accuracy stats.
    """
    bin_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    
    for record in data:
        chain_length = int(record.get('chain_length', 0))
        chain_bin = bin_hop_length(chain_length)
        is_correct = record.get('correctness', 'False') == 'True'
        
        bin_stats[chain_bin]["total"] += 1
        if is_correct:
            bin_stats[chain_bin]["correct"] += 1
            
    return dict(bin_stats)

def write_results(
    results: Dict[str, Any], 
    output_path: Path
) -> None:
    """
    Write accuracy results to JSON.
    
    Args:
        results: Accuracy metrics dictionary.
        output_path: Output file path.
    """
    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main() -> None:
    """Main entry point for accuracy stratification."""
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "annotated_videokr.csv"
    output_path = project_root / "data" / "processed" / "accuracy_by_bin.json"
    
    if not input_path.exists():
        logger.error("Annotated data not found. Run annotate_graph.py first.")
        sys.exit(1)
        
    data = load_annotated_data(input_path)
    bin_stats = calculate_accuracy_by_bin(data)
    
    # Calculate accuracy rates
    results = {}
    for bin_label, stats in bin_stats.items():
        accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
        results[bin_label] = {
            "accuracy": round(accuracy, 4),
            "correct": stats["correct"],
            "total": stats["total"]
        }
        
    write_results(results, output_path)

if __name__ == "__main__":
    main()