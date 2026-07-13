"""
Length filtering module for code snippet preprocessing.

Implements function-length filtering to achieve median length difference <= 20%
between human-written and LLM-generated code groups using a binary search algorithm.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from existing project modules
from logging_config import setup_logger, get_logger

# Configure logger
logger = setup_logger("length_filtering", "data/logs/length_filtering.log")

# Constants
MAX_ITERATIONS = 5
ERROR_103 = 103
TARGET_MEDIAN_DIFF_PCT = 20.0

def load_snippets_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load snippets from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing snippets.
        
    Returns:
        List of snippet dictionaries.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Snippets file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_median_length(snippets: List[Dict[str, Any]]) -> float:
    """
    Calculate the median length (number of lines) of a list of snippets.
    
    Args:
        snippets: List of snippet dictionaries, each expected to have a 'length' key.
        
    Returns:
        Median length as a float.
    """
    if not snippets:
        return 0.0
    
    lengths = [s.get('length', 0) for s in snippets]
    lengths.sort()
    n = len(lengths)
    if n % 2 == 1:
        return float(lengths[n // 2])
    else:
        return (lengths[n // 2 - 1] + lengths[n // 2]) / 2.0

def filter_by_length_threshold(snippets: List[Dict[str, Any]], 
                               min_lines: int, 
                               max_lines: int) -> List[Dict[str, Any]]:
    """
    Filter snippets by length range.
    
    Args:
        snippets: List of snippet dictionaries.
        min_lines: Minimum number of lines (inclusive).
        max_lines: Maximum number of lines (inclusive).
        
    Returns:
        Filtered list of snippets.
    """
    return [
        s for s in snippets 
        if min_lines <= s.get('length', 0) <= max_lines
    ]

def calculate_median_difference(group1: List[Dict[str, Any]], 
                                group2: List[Dict[str, Any]]) -> float:
    """
    Calculate the percentage difference between medians of two groups.
    
    Formula: |median1 - median2| / max(median1, median2) * 100
    
    Args:
        group1: First group of snippets.
        group2: Second group of snippets.
        
    Returns:
        Percentage difference.
    """
    med1 = calculate_median_length(group1)
    med2 = calculate_median_length(group2)
    
    if med1 == 0 and med2 == 0:
        return 0.0
    
    max_med = max(med1, med2)
    if max_med == 0:
        return 100.0  # Avoid division by zero
    
    diff = abs(med1 - med2)
    return (diff / max_med) * 100.0

def binary_search_length_filter(human_snippets: List[Dict[str, Any]], 
                                llm_snippets: List[Dict[str, Any]], 
                                max_iterations: int = MAX_ITERATIONS) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], bool]:
    """
    Perform binary search to find a length threshold that balances median lengths.
    
    The algorithm searches for a minimum line threshold that reduces the median
    length difference to <= 20% between groups.
    
    Args:
        human_snippets: List of human-written code snippets.
        llm_snippets: List of LLM-generated code snippets.
        max_iterations: Maximum number of binary search iterations.
        
    Returns:
        Tuple of (filtered_human, filtered_llm, success_flag).
    """
    logger.info(f"Starting binary search length filter with max {max_iterations} iterations")
    
    # Determine initial range based on available data
    all_lengths = [s.get('length', 0) for s in human_snippets + llm_snippets]
    if not all_lengths:
        logger.error("No valid lengths found in snippets")
        return [], [], False
    
    min_possible = min(all_lengths)
    max_possible = max(all_lengths)
    
    logger.info(f"Initial length range: [{min_possible}, {max_possible}]")
    logger.info(f"Initial medians - Human: {calculate_median_length(human_snippets):.2f}, LLM: {calculate_median_length(llm_snippets):.2f}")
    logger.info(f"Initial median difference: {calculate_median_difference(human_snippets, llm_snippets):.2f}%")
    
    low = min_possible
    high = max_possible
    best_human = human_snippets
    best_llm = llm_snippets
    best_diff = calculate_median_difference(human_snippets, llm_snippets)
    success = best_diff <= TARGET_MEDIAN_DIFF_PCT
    
    if success:
        logger.info(f"Initial groups already meet target difference ({best_diff:.2f}% <= {TARGET_MEDIAN_DIFF_PCT}%)")
        return best_human, best_llm, True
    
    iteration = 0
    while iteration < max_iterations and low <= high:
        iteration += 1
        mid = (low + high) // 2
        
        # Filter both groups with the current threshold
        # We try increasing the minimum length to reduce the median of the longer group
        filtered_human = filter_by_length_threshold(human_snippets, mid, max_possible)
        filtered_llm = filter_by_length_threshold(llm_snippets, mid, max_possible)
        
        # Check if we have enough samples
        if not filtered_human or not filtered_llm:
            # If one group is empty, we can't proceed with this threshold
            # Move the threshold to see if we can get a valid range
            if len(filtered_human) < len(filtered_llm):
                low = mid + 1
            else:
                high = mid - 1
            continue
        
        current_diff = calculate_median_difference(filtered_human, filtered_llm)
        logger.info(f"Iteration {iteration}: Threshold={mid}, Diff={current_diff:.2f}%, "
                    f"H:{len(filtered_human)}, L:{len(filtered_llm)}")
        
        if current_diff <= TARGET_MEDIAN_DIFF_PCT:
            # Found a valid threshold
            best_diff = current_diff
            best_human = filtered_human
            best_llm = filtered_llm
            success = True
            logger.info(f"Found valid threshold at iteration {iteration}: diff={current_diff:.2f}%")
            # Try to find a better one by searching lower thresholds (less filtering)
            high = mid - 1
        else:
            # Difference is too large, try to adjust threshold
            # If human median is much larger, we might need to increase min threshold
            med_h = calculate_median_length(filtered_human)
            med_l = calculate_median_length(filtered_llm)
            
            if med_h > med_l:
                # Human group is longer, increase min threshold to cut more human code
                low = mid + 1
            else:
                # LLM group is longer, increase min threshold to cut more LLM code
                low = mid + 1
    
    logger.info(f"Binary search completed after {iteration} iterations. Success: {success}, Best diff: {best_diff:.2f}%")
    
    if not success:
        logger.error(f"Failed to achieve median difference <= {TARGET_MEDIAN_DIFF_PCT}% after {max_iterations} iterations. "
                     f"Final difference: {best_diff:.2f}%")
        return [], [], False
    
    return best_human, best_llm, True

def run_length_filtering_workflow(input_path: str, 
                                  output_path: str, 
                                  max_iterations: int = MAX_ITERATIONS) -> bool:
    """
    Run the complete length filtering workflow.
    
    1. Load human and LLM snippets from input file.
    2. Perform binary search to find optimal length threshold.
    3. Filter snippets to achieve median difference <= 20%.
    4. Save filtered snippets to output file.
    5. Abort with error 103 if max iterations reached without success.
    
    Args:
        input_path: Path to input JSON file containing both groups.
        output_path: Path to output JSON file for filtered snippets.
        max_iterations: Maximum binary search iterations.
        
    Returns:
        True if successful, False otherwise (and exits with error 103).
    """
    logger.info(f"Starting length filtering workflow")
    logger.info(f"Input: {input_path}, Output: {output_path}")
    
    # Load data
    try:
        data = load_snippets_from_file(input_path)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(ERROR_103)
    
    # Expect data to have 'human' and 'codegen' keys
    if 'human' not in data or 'codegen' not in data:
        logger.error("Input data must contain 'human' and 'codegen' keys")
        sys.exit(ERROR_103)
    
    human_snippets = data['human']
    llm_snippets = data['codegen']
    
    logger.info(f"Loaded {len(human_snippets)} human snippets and {len(llm_snippets)} LLM snippets")
    
    # Perform binary search filtering
    filtered_human, filtered_llm, success = binary_search_length_filter(
        human_snippets, 
        llm_snippets, 
        max_iterations
    )
    
    if not success:
        logger.error(f"Length filtering failed to meet target. Aborting with error {ERROR_103}")
        sys.exit(ERROR_103)
    
    # Prepare output
    output_data = {
        'human': filtered_human,
        'codegen': filtered_llm,
        'metadata': {
            'human_count': len(filtered_human),
            'codegen_count': len(filtered_llm),
            'human_median_length': calculate_median_length(filtered_human),
            'codegen_median_length': calculate_median_length(filtered_llm),
            'median_difference_pct': calculate_median_difference(filtered_human, filtered_llm),
            'max_iterations': max_iterations
        }
    }
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Successfully wrote filtered snippets to {output_path}")
    logger.info(f"Final counts - Human: {len(filtered_human)}, LLM: {len(filtered_llm)}")
    logger.info(f"Final median difference: {output_data['metadata']['median_difference_pct']:.2f}%")
    
    return True

def main():
    """Main entry point for the length filtering module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Filter code snippets by length to balance median lengths")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSON file with 'human' and 'codegen' keys")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file for filtered snippets")
    parser.add_argument("--max-iterations", type=int, default=MAX_ITERATIONS, help="Maximum binary search iterations")
    
    args = parser.parse_args()
    
    success = run_length_filtering_workflow(
        args.input, 
        args.output, 
        args.max_iterations
    )
    
    if success:
        print("Length filtering completed successfully.")
        sys.exit(0)
    else:
        print(f"Length filtering failed. Aborting with error {ERROR_103}")
        sys.exit(ERROR_103)

if __name__ == "__main__":
    main()