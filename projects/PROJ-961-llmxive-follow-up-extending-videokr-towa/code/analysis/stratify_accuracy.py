import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.config import get_project_root, get_path, ensure_dir

logger = logging.getLogger(__name__)

def load_annotated_data() -> List[Dict[str, Any]]:
    """
    Load annotated data from T013 output.
    """
    path = get_path("data/processed/annotated_videokr.csv")
    if not path.exists():
        raise FileNotFoundError(f"Annotated dataset not found at {path}")
    
    data = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def bin_hop_length(hop: int) -> str:
    """
    Bin hop length into categories: '1', '2', '3+'.
    """
    if hop == 1:
        return '1'
    elif hop == 2:
        return '2'
    else:
        return '3+'

def calculate_accuracy_by_bin(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate accuracy for each bin.
    Returns a dict: {bin_name: {'count': N, 'correct': M, 'accuracy': M/N}}
    """
    bins: Dict[str, Dict[str, int]] = defaultdict(lambda: {'count': 0, 'correct': 0})
    
    for row in data:
        try:
            hop = int(row['chain_length'])
            correct = 1 if row['correctness'].lower() in ['true', '1', 'yes'] else 0
            
            bin_name = bin_hop_length(hop)
            bins[bin_name]['count'] += 1
            bins[bin_name]['correct'] += correct
        except (ValueError, KeyError) as e:
            logger.warning(f"Skipping row due to error: {e}")
            continue
    
    # Calculate accuracy
    result = {}
    for bin_name, stats in bins.items():
        if stats['count'] > 0:
            result[bin_name] = {
                'count': stats['count'],
                'correct': stats['correct'],
                'accuracy': stats['correct'] / stats['count']
            }
        else:
            result[bin_name] = {
                'count': 0,
                'correct': 0,
                'accuracy': 0.0
            }
    
    return result

def write_results(accuracy_by_bin: Dict[str, Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """
    Write results to JSON and prepare bin counts for T020a.
    """
    if output_path is None:
        output_path = get_path("data/processed/bin_counts.json")
    
    # Extract counts for T020a
    bin_counts = {k: v['count'] for k, v in accuracy_by_bin.items()}
    
    ensure_dir(output_path)
    with open(output_path, 'w') as f:
        json.dump(bin_counts, f, indent=2)
    
    logger.info(f"Bin counts saved to {output_path}")
    
    # Also save detailed accuracy results
    detailed_path = get_path("data/processed/accuracy_by_bin.json")
    ensure_dir(detailed_path)
    with open(detailed_path, 'w') as f:
        json.dump(accuracy_by_bin, f, indent=2)
    logger.info(f"Accuracy results saved to {detailed_path}")

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        logger.info("Loading annotated data...")
        data = load_annotated_data()
        logger.info(f"Loaded {len(data)} records.")
        
        logger.info("Calculating accuracy by bin...")
        accuracy_by_bin = calculate_accuracy_by_bin(data)
        
        logger.info(f"Accuracy by bin: {accuracy_by_bin}")
        
        logger.info("Writing results...")
        write_results(accuracy_by_bin)
        
        logger.info("Stratify accuracy complete.")
        
    except Exception as e:
        logger.error(f"Error in stratify_accuracy main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
