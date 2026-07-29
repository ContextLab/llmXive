import csv
import json
import logging
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

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

def calculate_effect_size(data: List[Dict], threshold: int) -> float:
    """
    Calculate effect size (accuracy drop) for a given threshold.
    Compares accuracy <= threshold vs > threshold.
    """
    left = [d['correctness'] for d in data if d['chain_length'] <= threshold]
    right = [d['correctness'] for d in data if d['chain_length'] > threshold]
    
    if not left or not right:
        return 0.0
    
    acc_left = sum(left) / len(left)
    acc_right = sum(right) / len(right)
    
    return acc_left - acc_right

def permutation_test(data: List[Dict], threshold: int, n_permutations: int = 1000) -> float:
    """
    Perform permutation test for a specific threshold.
    """
    observed_effect = calculate_effect_size(data, threshold)
    
    hops = [d['chain_length'] for d in data]
    correctness = [d['correctness'] for d in data]
    
    permuted_effects = []
    
    for _ in range(n_permutations):
        shuffled_correctness = correctness[:]
        random.shuffle(shuffled_correctness)
        
        perm_data = [{'chain_length': h, 'correctness': c} for h, c in zip(hops, shuffled_correctness)]
        
        effect = calculate_effect_size(perm_data, threshold)
        permuted_effects.append(effect)
    
    count = sum(1 for e in permuted_effects if e >= observed_effect)
    return count / n_permutations

def bonferroni_correction(p_value: float, n_tests: int) -> float:
    return min(p_value * n_tests, 1.0)

def perform_threshold_sweep(data: List[Dict], thresholds: List[int], n_permutations: int = 1000) -> List[Dict[str, Any]]:
    """
    Perform sensitivity analysis by sweeping thresholds.
    """
    results = []
    
    for threshold in thresholds:
        logger.info(f"Testing threshold: {threshold}")
        raw_p = permutation_test(data, threshold, n_permutations)
        corrected_p = bonferroni_correction(raw_p, len(thresholds))
        effect = calculate_effect_size(data, threshold)
        
        results.append({
            'threshold_hop': threshold,
            'p_value': corrected_p,
            'effect_size': effect,
            'is_significant': corrected_p < 0.05
        })
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """
    Save sensitivity results to JSON and CSV.
    """
    if output_path is None:
        output_path = get_path("data/processed/sensitivity_results.json")
    
    ensure_dir(output_path)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Also save as CSV
    csv_path = get_path("data/processed/sensitivity_thresholds.csv")
    ensure_dir(csv_path)
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['threshold_hop', 'p_value', 'effect_size', 'is_significant'])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Sensitivity results saved to {output_path} and {csv_path}")

def run_sensitivity_analysis(data: List[Dict], thresholds: List[int] = [2, 3, 4], n_permutations: int = 1000) -> List[Dict[str, Any]]:
    """
    Main function to run sensitivity analysis.
    """
    logger.info(f"Running sensitivity analysis with thresholds: {thresholds}")
    results = perform_threshold_sweep(data, thresholds, n_permutations)
    save_results(results)
    return results

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        logger.info("Loading annotated data...")
        data = load_annotated_data()
        logger.info(f"Loaded {len(data)} records.")
        
        # Prepare correctness data
        processed_data = []
        for row in data:
            try:
                hop = int(row['chain_length'])
                correct = 1 if row['correctness'].lower() in ['true', '1', 'yes'] else 0
                processed_data.append({'chain_length': hop, 'correctness': correct})
            except (ValueError, KeyError):
                continue
        
        logger.info("Running sensitivity analysis...")
        results = run_sensitivity_analysis(processed_data)
        
        logger.info(f"Results: {results}")
        logger.info("Sensitivity analysis complete.")
        
    except Exception as e:
        logger.error(f"Error in sensitivity main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
