"""
Threshold detection using permutation tests.
"""
import json
import logging
import os
import sys
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union


def load_raw_annotated_data(
    file_path: Union[str, Path]
) -> List[Dict[str, Any]]:
    """
    Load raw annotated data from CSV.
    
    Args:
        file_path (Union[str, Path]): Path to the CSV file.
        
    Returns:
        List[Dict[str, Any]]: List of row dictionaries.
    """
    import csv
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path
    data = []
    
    with open(path_obj, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    return data


def load_bin_config(
    file_path: Union[str, Path]
) -> Dict[str, Any]:
    """
    Load bin configuration from JSON.
    
    Args:
        file_path (Union[str, Path]): Path to the JSON file.
        
    Returns:
        Dict[str, Any]: Bin configuration.
    """
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path
    
    with open(path_obj, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_effect_size(
    data: List[Dict[str, Any]],
    threshold: int
) -> float:
    """
    Calculate effect size for a given threshold.
    
    Args:
        data (List[Dict[str, Any]]): Annotated data.
        threshold (int): Threshold hop count.
        
    Returns:
        float: Effect size.
    """
    group1_correct = 0
    group1_total = 0
    group2_correct = 0
    group2_total = 0
    
    for row in data:
        try:
            hop = int(row['chain_length'])
            correct = row.get('correctness', '0').lower() in ['1', 'true', 'yes']
            
            if hop < threshold:
                group1_total += 1
                if correct:
                    group1_correct += 1
            else:
                group2_total += 1
                if correct:
                    group2_correct += 1
        except (ValueError, KeyError):
            continue
    
    if group1_total == 0 or group2_total == 0:
        return 0.0
    
    mean1 = group1_correct / group1_total
    mean2 = group2_correct / group2_total
    
    return abs(mean1 - mean2)


def permutation_test(
    data: List[Dict[str, Any]],
    threshold: int,
    n_permutations: int = 1000,
    seed: Optional[int] = None
) -> Tuple[float, float]:
    """
    Perform permutation test for threshold detection.
    
    Args:
        data (List[Dict[str, Any]]): Annotated data.
        threshold (int): Threshold hop count.
        n_permutations (int): Number of permutations.
        seed (Optional[int]): Random seed.
        
    Returns:
        Tuple[float, float]: Observed statistic and p-value.
    """
    if seed is not None:
        random.seed(seed)
    
    # Extract correctness values
    correctness_values = []
    hop_values = []
    
    for row in data:
        try:
            hop = int(row['chain_length'])
            correct = 1 if row.get('correctness', '0').lower() in ['1', 'true', 'yes'] else 0
            correctness_values.append(correct)
            hop_values.append(hop)
        except (ValueError, KeyError):
            continue
    
    if len(correctness_values) == 0:
        return 0.0, 1.0
    
    # Calculate observed statistic
    observed_effect = calculate_effect_size(data, threshold)
    
    # Permutation test
    permuted_effects = []
    for _ in range(n_permutations):
        shuffled_correctness = correctness_values.copy()
        random.shuffle(shuffled_correctness)
        
        # Create permuted data
        permuted_data = []
        for i, hop in enumerate(hop_values):
            permuted_data.append({
                'chain_length': hop,
                'correctness': str(shuffled_correctness[i])
            })
        
        permuted_effect = calculate_effect_size(permuted_data, threshold)
        permuted_effects.append(permuted_effect)
    
    # Calculate p-value
    p_value = sum(1 for e in permuted_effects if e >= observed_effect) / n_permutations
    
    return observed_effect, p_value


def bonferroni_correction(
    p_value: float,
    num_tests: int
) -> float:
    """
    Apply Bonferroni correction.
    
    Args:
        p_value (float): Raw p-value.
        num_tests (int): Number of tests performed.
        
    Returns:
        float: Corrected p-value.
    """
    corrected = p_value * num_tests
    return min(corrected, 1.0)


def grid_search_change_point(
    data: List[Dict[str, Any]],
    min_hop: int = 1,
    max_hop: int = 5,
    n_permutations: int = 1000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Grid search for optimal change point.
    
    Args:
        data (List[Dict[str, Any]]): Annotated data.
        min_hop (int): Minimum hop to test.
        max_hop (int): Maximum hop to test.
        n_permutations (int): Number of permutations.
        seed (Optional[int]): Random seed.
        
    Returns:
        Dict[str, Any]: Best threshold and statistics.
    """
    best_threshold = min_hop
    best_p_value = 1.0
    best_effect = 0.0
    
    results = []
    
    for threshold in range(min_hop, max_hop + 1):
        effect, p_value = permutation_test(data, threshold, n_permutations, seed)
        corrected_p = bonferroni_correction(p_value, max_hop - min_hop + 1)
        
        results.append({
            'threshold': threshold,
            'effect_size': effect,
            'p_value': p_value,
            'p_value_corrected': corrected_p
        })
        
        if corrected_p < best_p_value:
            best_p_value = corrected_p
            best_threshold = threshold
            best_effect = effect
    
    return {
        'optimal_knot': best_threshold,
        'p_value': best_p_value,
        'effect_size': best_effect,
        'all_results': results
    }


def detect_threshold(
    data: List[Dict[str, Any]],
    bin_config: Dict[str, Any],
    n_permutations: int = 1000,
    alpha: float = 0.05,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Detect threshold using permutation test.
    
    Args:
        data (List[Dict[str, Any]]): Annotated data.
        bin_config (Dict[str, Any]): Bin configuration.
        n_permutations (int): Number of permutations.
        alpha (float): Significance level.
        seed (Optional[int]): Random seed.
        
    Returns:
        Dict[str, Any]: Threshold detection results.
    """
    if bin_config.get('strategy') == 'deferred':
        return {
            'status': 'deferred',
            'reason': 'insufficient_power'
        }
    
    search_result = grid_search_change_point(
        data,
        min_hop=1,
        max_hop=5,
        n_permutations=n_permutations,
        seed=seed
    )
    
    is_significant = search_result['p_value'] < alpha
    conclusion = "Significant reasoning cliff detected" if is_significant else "No significant reasoning cliff detected"
    
    return {
        'optimal_knot': search_result['optimal_knot'],
        'p_value': search_result['p_value'],
        'alpha': alpha,
        'is_significant': is_significant,
        'conclusion': conclusion,
        'effect_size': search_result['effect_size']
    }


def save_results(
    results: Dict[str, Any],
    output_path: Union[str, Path]
) -> None:
    """
    Save threshold detection results to a JSON file.
    
    Args:
        results (Dict[str, Any]): Detection results.
        output_path (Union[str, Path]): Path for the output file.
    """
    output_obj = Path(output_path) if isinstance(output_path, str) else output_path
    output_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_obj, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)


def main() -> None:
    """Main entry point for threshold detection module."""
    pass


if __name__ == "__main__":
    main()
