"""
Statistical analysis models and hypothesis testing for PR review time impact.

This module implements the Mann-Whitney U test as the primary hypothesis test
(per Plan Override for SC-001) and prepares data for subsequent LMER analysis.
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from scipy import stats

from data.logging_config import get_logger
from config import MAX_REVIEW_DAYS

logger = get_logger(__name__)


def load_filtered_pr_data(filepath: str) -> Tuple[List[float], List[float]]:
    """
    Load the filtered PR dataset and separate review times by origin label.

    Args:
        filepath: Path to the CSV file containing filtered PR data.

    Returns:
        A tuple of (disclosing_times, non_disclosing_times) as lists of floats.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    input_path = Path(filepath)
    if not input_path.exists():
        logger.error(f"Input file not found: {filepath}")
        raise FileNotFoundError(f"Input file not found: {filepath}")

    disclosing_times = []
    non_disclosing_times = []

    required_columns = {'origin_label', 'first_review_time', 'total_review_time'}

    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Validate headers
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no headers.")
        
        missing_cols = required_columns - set(reader.fieldnames)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        for row in reader:
            label = row['origin_label']
            
            # Prefer total_review_time, fallback to first_review_time if needed
            # (Assuming process.py ensures at least one is present and valid)
            try:
                time_val = float(row.get('total_review_time') or row.get('first_review_time'))
            except (TypeError, ValueError):
                logger.warning(f"Skipping row with invalid time: {row}")
                continue

            if label == 'Disclosing':
                disclosing_times.append(time_val)
            elif label == 'Non-Disclosing':
                non_disclosing_times.append(time_val)
            else:
                logger.warning(f"Unknown origin_label '{label}' in row: {row}")

    if not disclosing_times:
        logger.warning("No 'Disclosing' PRs found in the filtered dataset.")
    if not non_disclosing_times:
        logger.warning("No 'Non-Disclosing' PRs found in the filtered dataset.")

    return disclosing_times, non_disclosing_times


def perform_mann_whitney_u_test(
    group1: List[float], 
    group2: List[float],
    alternative: str = 'two-sided'
) -> Dict[str, float]:
    """
    Perform the Mann-Whitney U test to compare two independent samples.

    This test is non-parametric and does not assume normality, making it suitable
    for review time data which often has skewed distributions.

    Args:
        group1: List of values for the first group (e.g., Disclosing).
        group2: List of values for the second group (e.g., Non-Disclosing).
        alternative: Specifies the alternative hypothesis. 
                     Options: 'two-sided', 'less', 'greater'.

    Returns:
        Dictionary containing 'statistic' (U statistic) and 'p_value'.
    """
    if len(group1) < 2 or len(group2) < 2:
        logger.warning("One of the groups has fewer than 2 samples. Cannot perform test.")
        return {'statistic': np.nan, 'p_value': np.nan}

    statistic, p_value = stats.mannwhitneyu(
        group1, 
        group2, 
        alternative=alternative,
        use_continuity=True
    )

    return {
        'statistic': float(statistic),
        'p_value': float(p_value)
    }


def run_mann_whitney_analysis(
    input_file: str,
    output_file: str
) -> Dict[str, Any]:
    """
    Main execution function for the Mann-Whitney U test analysis.

    1. Loads data from input_file.
    2. Performs the Mann-Whitney U test.
    3. Updates or creates the analysis_results.json file.

    Args:
        input_file: Path to the filtered PR data CSV.
        output_file: Path to the JSON results file.

    Returns:
        The result dictionary containing the test statistics.
    """
    logger.info(f"Starting Mann-Whitney U test analysis.")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")

    # Load data
    disclosing_times, non_disclosing_times = load_filtered_pr_data(input_file)
    
    logger.info(f"Loaded {len(disclosing_times)} Disclosing and {len(non_disclosing_times)} Non-Disclosing samples.")

    # Perform test
    result = perform_mann_whitney_u_test(disclosing_times, non_disclosing_times)

    # Prepare output structure
    analysis_result = {
        'mann_whitney': {
            'statistic': result['statistic'],
            'p_value': result['p_value'],
            'primary_p_value': result['p_value'], # Per task spec, primary_p_value maps to p_value
            'sample_sizes': {
                'disclosing': len(disclosing_times),
                'non_disclosing': len(non_disclosing_times)
            }
        }
    }

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing results if file exists, otherwise start fresh
    final_results = {}
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                final_results = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing results file {output_file}: {e}. Starting fresh.")

    # Merge results
    final_results['mann_whitney'] = analysis_result['mann_whitney']

    # Write back to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2)

    logger.info(f"Mann-Whitney U test completed. Results written to {output_file}")
    logger.info(f"Statistic: {result['statistic']:.4f}, P-value: {result['p_value']:.6f}")

    return final_results


def main():
    """Entry point for the Mann-Whitney U test script."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "processed" / "pr_data_filtered.csv"
    output_path = project_root / "data" / "analysis_results.json"

    try:
        run_mann_whitney_analysis(str(input_path), str(output_path))
    except FileNotFoundError as e:
        logger.error(f"Data file missing. Ensure T022 (outlier exclusion) has run first: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during Mann-Whitney analysis: {e}")
        raise


if __name__ == "__main__":
    main()