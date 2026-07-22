import csv
import json
import logging
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.config import get_project_root, get_path, ensure_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_pilot_sample(
    data: List[Dict[str, Any]], 
    threshold: int, 
    sample_size: int = 100
) -> Dict[str, int]:
    """
    Run a pilot sample for a specific threshold.
    
    Args:
        data: Full dataset.
        threshold: Threshold value.
        sample_size: Sample size.
        
    Returns:
        Dictionary of bin counts.
    """
    sample = data[:sample_size]
    bin_counts = defaultdict(int)
    
    for record in sample:
        hop = int(record['chain_length'])
        if hop <= threshold:
            bin_counts['below'] += 1
        else:
            bin_counts['above'] += 1
            
    return dict(bin_counts)

def oversample_dataset(
    data: List[Dict[str, Any]], 
    threshold: int, 
    min_count: int = 50
) -> List[Dict[str, Any]]:
    """
    Oversample bins with fewer than min_count records.
    
    Args:
        data: Dataset to oversample.
        threshold: Threshold value.
        min_count: Minimum required records.
        
    Returns:
        Oversampled dataset.
    """
    # Placeholder for oversampling logic
    return data

def merge_bins_if_needed(
    data: List[Dict[str, Any]], 
    threshold: int
) -> List[Dict[str, Any]]:
    """
    Merge bins if necessary for small sample sizes.
    
    Args:
        data: Dataset.
        threshold: Threshold value.
        
    Returns:
        Modified dataset.
    """
    # Placeholder for merging logic
    return data

def calculate_effect_size(
    bin1_accuracy: float, 
    bin2_accuracy: float
) -> float:
    """
    Calculate effect size.
    
    Args:
        bin1_accuracy: Accuracy of first bin.
        bin2_accuracy: Accuracy of second bin.
        
    Returns:
        Effect size.
    """
    return bin1_accuracy - bin2_accuracy

def perform_threshold_sweep(
    data: List[Dict[str, Any]], 
    thresholds: List[int]
) -> List[Dict[str, Any]]:
    """
    Perform threshold sweep analysis.
    
    Args:
        data: Dataset.
        thresholds: List of threshold values.
        
    Returns:
        List of results for each threshold.
    """
    results = []
    
    for threshold in thresholds:
        # Re-bin data
        bin1_correct = 0
        bin1_total = 0
        bin2_correct = 0
        bin2_total = 0
        
        for record in data:
            hop = int(record['chain_length'])
            is_correct = record.get('correctness', 'False') == 'True'
            
            if hop <= threshold:
                bin1_total += 1
                if is_correct:
                    bin1_correct += 1
            else:
                bin2_total += 1
                if is_correct:
                    bin2_correct += 1
                    
        acc1 = bin1_correct / bin1_total if bin1_total > 0 else 0.0
        acc2 = bin2_correct / bin2_total if bin2_total > 0 else 0.0
        
        effect_size = calculate_effect_size(acc1, acc2)
        
        results.append({
            "threshold": threshold,
            "accuracy_bin1": round(acc1, 4),
            "accuracy_bin2": round(acc2, 4),
            "effect_size": round(effect_size, 4),
            "n_bin1": bin1_total,
            "n_bin2": bin2_total
        })
        
    return results

def save_results(
    results: List[Dict[str, Any]], 
    output_path: Path
) -> None:
    """
    Save sensitivity results to JSON.
    
    Args:
        results: Results list.
        output_path: Output file path.
    """
    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def run_sensitivity_analysis(
    data: List[Dict[str, Any]], 
    thresholds: List[int]
) -> List[Dict[str, Any]]:
    """
    Run full sensitivity analysis.
    
    Args:
        data: Dataset.
        thresholds: Thresholds to test.
        
    Returns:
        List of results.
    """
    return perform_threshold_sweep(data, thresholds)

def main() -> None:
    """Main entry point for sensitivity analysis."""
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "annotated_videokr.csv"
    output_path = project_root / "data" / "processed" / "sensitivity_results.json"
    
    if not input_path.exists():
        logger.error("Annotated data not found.")
        sys.exit(1)
        
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)
        
    thresholds = [2, 3, 4]
    results = run_sensitivity_analysis(data, thresholds)
    save_results(results, output_path)

if __name__ == "__main__":
    main()