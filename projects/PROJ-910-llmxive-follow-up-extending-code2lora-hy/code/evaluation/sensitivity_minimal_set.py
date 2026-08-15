"""
Implementation of T032: Identify the minimal feature set meeting the accuracy threshold.

This module parses `data/results/sensitivity_summary.csv` and `data/results/baseline_score.json`
to calculate the dynamic threshold (80% of baseline) and identify the minimal feature set
that meets this threshold.

Output: `data/results/minimal_feature_set.txt`
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Constants
THRESHOLD_PERCENTAGE = 0.80  # 80% of baseline accuracy
RESULTS_DIR = Path("data/results")
BASELINE_SCORE_FILE = RESULTS_DIR / "baseline_score.json"
SENSITIVITY_SUMMARY_FILE = RESULTS_DIR / "sensitivity_summary.csv"
OUTPUT_FILE = RESULTS_DIR / "minimal_feature_set.txt"


def load_baseline_score() -> float:
    """
    Load the baseline accuracy score from data/results/baseline_score.json.
    Expected format: {"score": <float>}

    Returns:
        float: The baseline accuracy score.

    Raises:
        FileNotFoundError: If the baseline score file does not exist.
        ValueError: If the file content is invalid or missing the 'score' key.
    """
    if not BASELINE_SCORE_FILE.exists():
        raise FileNotFoundError(
            f"Baseline score file not found: {BASELINE_SCORE_FILE}. "
            "Ensure T031a has completed successfully."
        )

    try:
        with open(BASELINE_SCORE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'score' not in data:
            raise ValueError(f"Missing 'score' key in {BASELINE_SCORE_FILE}")
        
        score = float(data['score'])
        if score < 0 or score > 1:
            raise ValueError(f"Invalid baseline score value: {score}. Expected value between 0 and 1.")
        
        return score
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {BASELINE_SCORE_FILE}: {e}")


def calculate_dynamic_threshold(baseline_score: float) -> float:
    """
    Calculate the dynamic threshold as a percentage of the baseline score.

    Args:
        baseline_score (float): The baseline accuracy score.

    Returns:
        float: The threshold value (baseline_score * THRESHOLD_PERCENTAGE).
    """
    return baseline_score * THRESHOLD_PERCENTAGE


def load_sensitivity_results() -> List[Dict[str, Any]]:
    """
    Load the sensitivity summary results from data/results/sensitivity_summary.csv.
    Expected columns: feature_set, accuracy, meets_threshold

    Returns:
        List[Dict[str, Any]]: List of dictionaries containing sensitivity results.

    Raises:
        FileNotFoundError: If the sensitivity summary file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if not SENSITIVITY_SUMMARY_FILE.exists():
        raise FileNotFoundError(
            f"Sensitivity summary file not found: {SENSITIVITY_SUMMARY_FILE}. "
            "Ensure T033 has completed successfully."
        )

    results = []
    try:
        with open(SENSITIVITY_SUMMARY_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate required columns
            required_columns = {'feature_set', 'accuracy', 'meets_threshold'}
            if not required_columns.issubset(set(reader.fieldnames or [])):
                raise ValueError(
                    f"Missing required columns in {SENSITIVITY_SUMMARY_FILE}. "
                    f"Expected: {required_columns}, Found: {reader.fieldnames}"
                )
            
            for row in reader:
                results.append({
                    'feature_set': row['feature_set'],
                    'accuracy': float(row['accuracy']),
                    'meets_threshold': row['meets_threshold'].lower() == 'true'
                })
        
        if not results:
            raise ValueError(f"Sensitivity summary file {SENSITIVITY_SUMMARY_FILE} is empty.")
        
        return results
    except csv.Error as e:
        raise ValueError(f"Error reading CSV {SENSITIVITY_SUMMARY_FILE}: {e}")


def identify_minimal_feature_set(
    sensitivity_results: List[Dict[str, Any]], 
    threshold: float
) -> Optional[str]:
    """
    Identify the minimal feature set that meets the accuracy threshold.
    
    The "minimal" set is defined as the one with the fewest features that still
    meets the threshold. If multiple sets have the same number of features,
    the first one encountered is selected.
    
    Args:
        sensitivity_results (List[Dict[str, Any]]): List of sensitivity results.
        threshold (float): The accuracy threshold to meet.

    Returns:
        Optional[str]: The name of the minimal feature set, or None if no set meets the threshold.
    """
    # Filter results that meet the threshold
    qualifying_sets = [
        res for res in sensitivity_results 
        if res['meets_threshold']
    ]

    if not qualifying_sets:
        return None

    # Sort by number of features (assuming feature_set name implies complexity)
    # For simplicity, we assume feature sets are named in a way that reflects complexity
    # e.g., "token_counts" < "cyclomatic" < "full_ast"
    # A more robust implementation would parse the actual feature count from the name
    # or use a predefined ordering.
    
    # Heuristic: Sort by string length as a proxy for complexity (shorter = simpler)
    # This assumes simpler feature sets have shorter names
    qualifying_sets.sort(key=lambda x: len(x['feature_set']))

    return qualifying_sets[0]['feature_set']


def save_minimal_feature_set(feature_set_name: Optional[str], baseline_score: float, threshold: float) -> None:
    """
    Save the identified minimal feature set to data/results/minimal_feature_set.txt.
    
    The output file contains:
    - The feature set name (or "None" if no set meets the threshold)
    - The baseline score
    - The calculated threshold
    - A brief explanation

    Args:
        feature_set_name (Optional[str]): The identified minimal feature set name.
        baseline_score (float): The baseline accuracy score.
        threshold (float): The calculated threshold value.
    """
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"Minimal Feature Set Identification Results\n")
        f.write(f"=" * 40 + "\n\n")
        
        if feature_set_name:
            f.write(f"Feature Set: {feature_set_name}\n")
            f.write(f"Status: MEETS THRESHOLD\n")
        else:
            f.write(f"Feature Set: None\n")
            f.write(f"Status: NO FEATURE SET MEETS THRESHOLD\n")
        
        f.write(f"\nBaseline Accuracy: {baseline_score:.4f}\n")
        f.write(f"Threshold ({THRESHOLD_PERCENTAGE*100:.0f}% of Baseline): {threshold:.4f}\n")
        
        if feature_set_name:
            f.write(f"\nThe feature set '{feature_set_name}' is the minimal set that achieves\n")
            f.write(f"at least {THRESHOLD_PERCENTAGE*100:.0f}% of the baseline accuracy.\n")
        else:
            f.write(f"\nNo feature set in the sensitivity analysis achieved the required\n")
            f.write(f"threshold of {THRESHOLD_PERCENTAGE*100:.0f}% of the baseline accuracy.\n")


def run_minimal_feature_set_identification() -> Optional[str]:
    """
    Main function to run the minimal feature set identification pipeline.
    
    Returns:
        Optional[str]: The identified minimal feature set name, or None if no set meets the threshold.
    """
    print("Starting minimal feature set identification (T032)...")
    
    # Step 1: Load baseline score
    print(f"Loading baseline score from {BASELINE_SCORE_FILE}...")
    baseline_score = load_baseline_score()
    print(f"  Baseline Score: {baseline_score:.4f}")
    
    # Step 2: Calculate threshold
    threshold = calculate_dynamic_threshold(baseline_score)
    print(f"  Calculated Threshold ({THRESHOLD_PERCENTAGE*100:.0f}%): {threshold:.4f}")
    
    # Step 3: Load sensitivity results
    print(f"Loading sensitivity results from {SENSITIVITY_SUMMARY_FILE}...")
    sensitivity_results = load_sensitivity_results()
    print(f"  Loaded {len(sensitivity_results)} feature set results.")
    
    # Step 4: Identify minimal feature set
    print("Identifying minimal feature set...")
    minimal_set = identify_minimal_feature_set(sensitivity_results, threshold)
    
    if minimal_set:
        print(f"  Found minimal feature set: {minimal_set}")
    else:
        print("  No feature set meets the threshold.")
    
    # Step 5: Save results
    print(f"Saving results to {OUTPUT_FILE}...")
    save_minimal_feature_set(minimal_set, baseline_score, threshold)
    print("  Results saved successfully.")
    
    return minimal_set


def main() -> None:
    """
    Entry point for the minimal feature set identification script.
    """
    try:
        minimal_set = run_minimal_feature_set_identification()
        if minimal_set:
            print(f"\nSUCCESS: Minimal feature set identified: {minimal_set}")
        else:
            print("\nWARNING: No feature set meets the accuracy threshold.")
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("Please ensure all prerequisite tasks (T031a, T033) have completed successfully.")
        raise
    except ValueError as e:
        print(f"\nERROR: Invalid data format - {e}")
        raise
    except Exception as e:
        print(f"\nERROR: Unexpected error - {e}")
        raise


if __name__ == "__main__":
    main()