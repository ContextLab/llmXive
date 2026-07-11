"""
T032: Identify the minimal feature set meeting the dynamic threshold.

This module reads the baseline accuracy from data/results/baseline_score.json
(produced by T031a), calculates the dynamic threshold (80% of baseline),
and identifies the minimal feature set from the sensitivity analysis results
(data/results/sensitivity_summary.csv) that meets or exceeds this threshold.
"""
import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Constants
BASELINE_SCORE_PATH = Path("data/results/baseline_score.json")
SENSITIVITY_SUMMARY_PATH = Path("data/results/sensitivity_summary.csv")
OUTPUT_PATH = Path("data/results/minimal_feature_set.json")
THRESHOLD_FACTOR = 0.80


def load_baseline_score() -> float:
    """
    Load the baseline accuracy score from the JSON file produced by T031a.
    
    Returns:
        float: The baseline accuracy score.
        
    Raises:
        FileNotFoundError: If the baseline score file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if not BASELINE_SCORE_PATH.exists():
        raise FileNotFoundError(
            f"Baseline score file not found: {BASELINE_SCORE_PATH}. "
            "Ensure T031a has been completed successfully."
        )
    
    with open(BASELINE_SCORE_PATH, 'r') as f:
        data = json.load(f)
    
    if 'baseline_accuracy' not in data:
        raise ValueError(f"Invalid format in {BASELINE_SCORE_PATH}: missing 'baseline_accuracy'")
    
    score = float(data['baseline_accuracy'])
    if score < 0 or score > 1:
        raise ValueError(f"Invalid baseline score value: {score}. Expected value between 0 and 1.")
    
    return score


def calculate_dynamic_threshold(baseline_score: float) -> float:
    """
    Calculate the dynamic threshold as a percentage of the baseline score.
    
    Args:
        baseline_score: The baseline accuracy score.
        
    Returns:
        float: The dynamic threshold (80% of baseline).
    """
    return baseline_score * THRESHOLD_FACTOR


def load_sensitivity_results() -> List[Dict[str, Any]]:
    """
    Load the sensitivity analysis results from the CSV file.
    
    Returns:
        List of dictionaries containing feature set data.
        
    Raises:
        FileNotFoundError: If the sensitivity summary file does not exist.
    """
    if not SENSITIVITY_SUMMARY_PATH.exists():
        raise FileNotFoundError(
            f"Sensitivity summary file not found: {SENSITIVITY_SUMMARY_PATH}. "
            "Ensure T033 has been completed successfully."
        )
    
    results = []
    with open(SENSITIVITY_SUMMARY_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    
    if not results:
        raise ValueError(f"Sensitivity summary file {SENSITIVITY_SUMMARY_PATH} is empty.")
    
    return results


def identify_minimal_feature_set(
    sensitivity_results: List[Dict[str, Any]], 
    threshold: float
) -> Optional[Dict[str, Any]]:
    """
    Identify the minimal feature set that meets the threshold.
    
    The "minimal" set is defined as the one with the fewest features 
    among those that meet the accuracy threshold.
    
    Args:
        sensitivity_results: List of sensitivity analysis results.
        threshold: The dynamic accuracy threshold.
        
    Returns:
        Optional dictionary containing the minimal feature set info, or None if none found.
    """
    candidates = []
    
    for row in sensitivity_results:
        accuracy = float(row['accuracy'])
        meets_threshold = row.get('meets_threshold', 'False').lower() == 'true'
        
        # Count features in the set (assuming 'feature_set' is a comma-separated string)
        feature_set_str = row.get('feature_set', '')
        if feature_set_str:
            feature_count = len([f.strip() for f in feature_set_str.split(',') if f.strip()])
        else:
            feature_count = 0
        
        if meets_threshold and accuracy >= threshold:
            candidates.append({
                'feature_set': row['feature_set'],
                'accuracy': accuracy,
                'feature_count': feature_count,
                'meets_threshold': True
            })
    
    if not candidates:
        return None
    
    # Sort by feature count (ascending) to find the minimal set
    candidates.sort(key=lambda x: x['feature_count'])
    
    return candidates[0]


def save_minimal_feature_set(result: Dict[str, Any], baseline_score: float, threshold: float) -> None:
    """
    Save the minimal feature set result to a JSON file.
    
    Args:
        result: The minimal feature set dictionary.
        baseline_score: The baseline accuracy score.
        threshold: The calculated dynamic threshold.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        'baseline_score': baseline_score,
        'dynamic_threshold': threshold,
        'threshold_factor': THRESHOLD_FACTOR,
        'minimal_feature_set': result
    }
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Minimal feature set saved to {OUTPUT_PATH}")


def run_minimal_feature_set_identification() -> Dict[str, Any]:
    """
    Main function to run the minimal feature set identification.
    
    Returns:
        Dictionary containing the results.
    """
    print("Loading baseline score...")
    baseline_score = load_baseline_score()
    print(f"Baseline score: {baseline_score:.4f}")
    
    threshold = calculate_dynamic_threshold(baseline_score)
    print(f"Dynamic threshold (80% of baseline): {threshold:.4f}")
    
    print("Loading sensitivity results...")
    sensitivity_results = load_sensitivity_results()
    print(f"Loaded {len(sensitivity_results)} sensitivity results.")
    
    print("Identifying minimal feature set...")
    minimal_set = identify_minimal_feature_set(sensitivity_results, threshold)
    
    if minimal_set:
        print(f"Found minimal feature set: {minimal_set['feature_set']}")
        print(f"Accuracy: {minimal_set['accuracy']:.4f} (>= {threshold:.4f})")
        print(f"Feature count: {minimal_set['feature_count']}")
        save_minimal_feature_set(minimal_set, baseline_score, threshold)
    else:
        print("No feature set meets the dynamic threshold.")
        # Still save the result indicating no set was found
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        output_data = {
            'baseline_score': baseline_score,
            'dynamic_threshold': threshold,
            'threshold_factor': THRESHOLD_FACTOR,
            'minimal_feature_set': None,
            'message': 'No feature set meets the dynamic threshold.'
        }
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"Result saved to {OUTPUT_PATH}")
    
    return {
        'baseline_score': baseline_score,
        'threshold': threshold,
        'minimal_feature_set': minimal_set
    }


def main():
    """Entry point for the script."""
    try:
        result = run_minimal_feature_set_identification()
        print("\nTask T032 completed successfully.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure prerequisite tasks (T031a, T033) have been completed.")
        return 1
    except ValueError as e:
        print(f"Data error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())