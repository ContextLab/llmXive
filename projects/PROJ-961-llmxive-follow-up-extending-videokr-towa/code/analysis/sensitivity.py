"""
Sensitivity analysis for threshold definitions.
"""
import csv
import json
import logging
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from analysis.detect_threshold import calculate_effect_size, permutation_test, bonferroni_correction


def load_annotated_data(
    file_path: Union[str, Path]
) -> List[Dict[str, Any]]:
    """
    Load annotated data from CSV.
    
    Args:
        file_path (Union[str, Path]): Path to the CSV file.
        
    Returns:
        List[Dict[str, Any]]: List of row dictionaries.
    """
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path
    data = []
    
    with open(path_obj, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    return data


def perform_threshold_sweep(
    data: List[Dict[str, Any]],
    thresholds: List[int],
    n_permutations: int = 1000,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Perform threshold sweep analysis.
    
    Args:
        data (List[Dict[str, Any]]): Annotated data.
        thresholds (List[int]): List of thresholds to test.
        n_permutations (int): Number of permutations.
        seed (Optional[int]): Random seed.
        
    Returns:
        List[Dict[str, Any]]: Results for each threshold.
    """
    results = []
    num_tests = len(thresholds)
    
    for threshold in thresholds:
        effect, p_value = permutation_test(data, threshold, n_permutations, seed)
        corrected_p = bonferroni_correction(p_value, num_tests)
        
        results.append({
            'threshold_hop': threshold,
            'p_value': corrected_p,
            'effect_size': effect,
            'is_significant': corrected_p < 0.05
        })
    
    return results


def save_results(
    results: List[Dict[str, Any]],
    output_path: Union[str, Path]
) -> None:
    """
    Save sensitivity results to a JSON file.
    
    Args:
        results (List[Dict[str, Any]]): Sensitivity results.
        output_path (Union[str, Path]): Path for the output file.
    """
    output_obj = Path(output_path) if isinstance(output_path, str) else output_path
    output_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_obj, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)


def run_sensitivity_analysis(
    data: List[Dict[str, Any]],
    min_threshold: int = 2,
    max_threshold: int = 4,
    n_permutations: int = 1000,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Run full sensitivity analysis.
    
    Args:
        data (List[Dict[str, Any]]): Annotated data.
        min_threshold (int): Minimum threshold to test.
        max_threshold (int): Maximum threshold to test.
        n_permutations (int): Number of permutations.
        seed (Optional[int]): Random seed.
        
    Returns:
        List[Dict[str, Any]]: Sensitivity results.
    """
    thresholds = list(range(min_threshold, max_threshold + 1))
    return perform_threshold_sweep(data, thresholds, n_permutations, seed)


def main() -> None:
    """Main entry point for sensitivity analysis module."""
    pass


if __name__ == "__main__":
    main()
