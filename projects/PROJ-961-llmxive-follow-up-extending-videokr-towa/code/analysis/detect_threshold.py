import json
import logging
import os
import sys
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from utils.config import get_project_root, get_path, ensure_dir

logger = logging.getLogger(__name__)

def load_raw_annotated_data() -> List[Dict[str, Any]]:
    """
    Load the raw annotated data from T013 output.
    """
    path = get_path("data/processed/annotated_videokr.csv")
    if not path.exists():
        raise FileNotFoundError(f"Annotated dataset not found at {path}")
    
    data = []
    with open(path, 'r') as f:
        header = f.readline().strip().split(',')
        try:
            hop_idx = header.index('chain_length')
            correct_idx = header.index('correctness')
        except ValueError:
            raise ValueError("Required columns (chain_length, correctness) not found")
        
        for line in f:
            parts = line.strip().split(',')
            if len(parts) > max(hop_idx, correct_idx):
                try:
                    hop = int(parts[hop_idx])
                    correct = 1 if parts[correct_idx].lower() in ['true', '1', 'yes'] else 0
                    data.append({'chain_length': hop, 'correctness': correct})
                except ValueError:
                    continue
    return data

def load_bin_config() -> Dict[str, Any]:
    """
    Load the bin configuration from T020a output.
    """
    path = get_path("data/processed/bin_config.json")
    if not path.exists():
        raise FileNotFoundError(f"Bin config not found at {path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def calculate_effect_size(data: List[Dict], knot: int) -> float:
    """
    Calculate the effect size (accuracy drop) at the knot.
    """
    # Split data into left (<= knot) and right (> knot)
    left = [d['correctness'] for d in data if d['chain_length'] <= knot]
    right = [d['correctness'] for d in data if d['chain_length'] > knot]
    
    if not left or not right:
        return 0.0
    
    acc_left = sum(left) / len(left)
    acc_right = sum(right) / len(right)
    
    return acc_left - acc_right

def permutation_test(data: List[Dict], knot: int, n_permutations: int = 1000) -> float:
    """
    Perform a permutation test to assess significance of the effect size.
    """
    # Calculate observed statistic
    observed_effect = calculate_effect_size(data, knot)
    
    # Prepare data for permutation
    hops = [d['chain_length'] for d in data]
    correctness = [d['correctness'] for d in data]
    
    permuted_effects = []
    
    for _ in range(n_permutations):
        # Shuffle correctness labels
        shuffled_correctness = correctness[:]
        random.shuffle(shuffled_correctness)
        
        # Reconstruct data
        perm_data = [{'chain_length': h, 'correctness': c} for h, c in zip(hops, shuffled_correctness)]
        
        # Calculate permuted effect
        effect = calculate_effect_size(perm_data, knot)
        permuted_effects.append(effect)
    
    # Calculate p-value
    # One-tailed test: how often is permuted effect >= observed effect?
    count = sum(1 for e in permuted_effects if e >= observed_effect)
    p_value = count / n_permutations
    
    return p_value

def bonferroni_correction(p_value: float, n_tests: int) -> float:
    """
    Apply Bonferroni correction.
    """
    return min(p_value * n_tests, 1.0)

def grid_search_change_point(data: List[Dict], n_permutations: int = 1000) -> Tuple[int, float]:
    """
    Grid search for the optimal change point (knot).
    Returns (optimal_knot, corrected_p_value).
    """
    # Define search range (1 to 5)
    knots = range(1, 6)
    best_knot = None
    best_p_value = 1.0
    
    results = []
    
    for knot in knots:
        raw_p = permutation_test(data, knot, n_permutations)
        corrected_p = bonferroni_correction(raw_p, len(knots))
        results.append({'knot': knot, 'raw_p': raw_p, 'corrected_p': corrected_p})
        
        if corrected_p < best_p_value:
            best_p_value = corrected_p
            best_knot = knot
    
    logger.info(f"Grid search results: {results}")
    return best_knot, best_p_value

def detect_threshold(data: List[Dict], n_permutations: int = 1000) -> Dict[str, Any]:
    """
    Main threshold detection logic.
    """
    optimal_knot, corrected_p = grid_search_change_point(data, n_permutations)
    
    effect_size = calculate_effect_size(data, optimal_knot)
    
    alpha = 0.05
    is_significant = corrected_p < alpha
    conclusion = "PASS" if is_significant else "FAIL"
    
    return {
        'optimal_knot': optimal_knot,
        'p_value': corrected_p,
        'alpha': alpha,
        'is_significant': is_significant,
        'conclusion': conclusion,
        'effect_size': effect_size
    }

def save_results(results: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """
    Save results to JSON.
    """
    if output_path is None:
        output_path = get_path("data/processed/threshold_results.json")
    
    ensure_dir(output_path)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        logger.info("Loading raw annotated data...")
        data = load_raw_annotated_data()
        logger.info(f"Loaded {len(data)} records.")
        
        logger.info("Loading bin config...")
        bin_config = load_bin_config()
        if bin_config.get('deferred', False):
            logger.warning("Analysis deferred due to insufficient power. Writing deferred results.")
            results = {
                'status': 'deferred',
                'reason': bin_config.get('reason', 'insufficient_power'),
                'conclusion': 'FAIL',
                'p_value': None,
                'optimal_knot': None
            }
            save_results(results)
            return

        logger.info("Running threshold detection...")
        results = detect_threshold(data)
        
        logger.info(f"Results: {results}")
        
        logger.info("Saving results...")
        save_results(results)
        
        logger.info("Threshold detection complete.")
        
    except Exception as e:
        logger.error(f"Error in detect_threshold main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
