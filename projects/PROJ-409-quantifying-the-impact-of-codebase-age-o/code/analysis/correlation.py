"""
Spearman rank correlation analysis between codebase age and LLM metrics.

This module performs statistical correlation analysis on the aggregated file metrics
to determine if there is a significant relationship between median_commit_age and
model performance metrics (perplexity and functional_correctness_rate), while
controlling for complexity and token_length covariates.
"""
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
from scipy import stats

# Import project utilities
from utils.logging import get_logger
from utils.config import ensure_directories

logger = get_logger(__name__)


def load_file_metrics(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the aggregated file metrics CSV.

    Args:
        input_path: Path to the file_metrics.csv file

    Returns:
        List of dictionaries containing row data
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields, handling potential NaN strings
            for key in ['mean_perplexity', 'mean_correctness', 'mean_complexity', 
                        'mean_length', 'median_age']:
                if key in row:
                    val = row[key]
                    if val is None or val == '' or val.lower() == 'nan':
                        row[key] = np.nan
                    else:
                        try:
                            row[key] = float(val)
                        except ValueError:
                            row[key] = np.nan
            data.append(row)

    logger.info(f"Loaded {len(data)} rows from {input_path}")
    return data


def filter_valid_rows(data: List[Dict[str, Any]], 
                      required_columns: List[str]) -> List[Dict[str, Any]]:
    """
    Filter out rows containing NaN values in required columns.

    Args:
        data: List of row dictionaries
        required_columns: Columns that must have valid (non-NaN) values

    Returns:
        Filtered list of rows with valid data
    """
    valid_data = []
    for row in data:
        is_valid = True
        for col in required_columns:
            if col not in row or np.isnan(row.get(col, np.nan)):
                is_valid = False
                break
        if is_valid:
            valid_data.append(row)

    logger.info(f"Filtered data: {len(data)} -> {len(valid_data)} valid rows")
    return valid_data


def calculate_partial_correlation(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray
) -> Tuple[float, float]:
    """
    Calculate partial correlation between x and y, controlling for z.
    
    Uses the formula: r_xy.z = (r_xy - r_xz * r_yz) / sqrt((1 - r_xz^2) * (1 - r_yz^2))

    Args:
        x: First variable array
        y: Second variable array
        z: Control variable array

    Returns:
        Tuple of (correlation coefficient, p-value)
    """
    # Calculate pairwise correlations
    r_xy, p_xy = stats.spearmanr(x, y)
    r_xz, p_xz = stats.spearmanr(x, z)
    r_yz, p_yz = stats.spearmanr(y, z)

    # Handle potential NaN or infinity in correlations
    if np.isnan(r_xz) or np.isnan(r_yz) or np.isnan(r_xy):
        return np.nan, np.nan

    # Calculate partial correlation
    numerator = r_xy - (r_xz * r_yz)
    denominator = np.sqrt((1 - r_xz**2) * (1 - r_yz**2))

    if denominator == 0:
        return np.nan, np.nan

    r_partial = numerator / denominator

    # Convert to t-statistic for p-value calculation
    n = len(x)
    if n <= 3:
        return r_partial, np.nan

    t_stat = r_partial * np.sqrt((n - 3) / (1 - r_partial**2))
    p_value = 2 * (1 - stats.t.cdf(np.abs(t_stat), n - 3))

    return r_partial, p_value


def run_correlation_analysis(
    data: List[Dict[str, Any]],
    age_col: str = 'median_age',
    perplexity_col: str = 'mean_perplexity',
    correctness_col: str = 'mean_correctness',
    complexity_col: str = 'mean_complexity',
    length_col: str = 'mean_length'
) -> Dict[str, Any]:
    """
    Perform Spearman rank correlation analysis with covariate control.

    Args:
        data: Filtered list of valid row dictionaries
        age_col: Column name for median commit age
        perplexity_col: Column name for perplexity metric
        correctness_col: Column name for correctness metric
        complexity_col: Column name for complexity covariate
        length_col: Column name for token length covariate

    Returns:
        Dictionary containing correlation results
    """
    if len(data) < 3:
        logger.warning("Insufficient data for correlation analysis")
        return {
            'status': 'insufficient_data',
            'n_samples': len(data),
            'spearman_correlation_age_perplexity': None,
            'p_value_age_perplexity': None,
            'spearman_correlation_age_correctness': None,
            'p_value_age_correctness': None,
            'partial_correlation_age_perplexity_complexity': None,
            'partial_correlation_age_correctness_complexity': None,
            'partial_correlation_age_perplexity_length': None,
            'partial_correlation_age_correctness_length': None
        }

    # Extract arrays
    ages = np.array([row[age_col] for row in data])
    perplexities = np.array([row[perplexity_col] for row in data])
    corrects = np.array([row[correctness_col] for row in data])
    complexities = np.array([row[complexity_col] for row in data])
    lengths = np.array([row[length_col] for row in data])

    results = {
        'n_samples': len(data),
        'status': 'success'
    }

    # Simple Spearman correlations
    logger.info("Calculating simple Spearman correlations...")
    
    r_age_perp, p_age_perp = stats.spearmanr(ages, perplexities)
    results['spearman_correlation_age_perplexity'] = float(r_age_perp)
    results['p_value_age_perplexity'] = float(p_age_perp)
    logger.info(f"Age-Perplexity: r={r_age_perp:.4f}, p={p_age_perp:.4f}")

    r_age_corr, p_age_corr = stats.spearmanr(ages, corrects)
    results['spearman_correlation_age_correctness'] = float(r_age_corr)
    results['p_value_age_correctness'] = float(p_age_corr)
    logger.info(f"Age-Correctness: r={r_age_corr:.4f}, p={p_age_corr:.4f}")

    # Partial correlations controlling for complexity
    logger.info("Calculating partial correlations (controlling for complexity)...")
    
    r_part_perp_comp, p_part_perp_comp = calculate_partial_correlation(
        ages, perplexities, complexities
    )
    results['partial_correlation_age_perplexity_complexity'] = float(r_part_perp_comp) if not np.isnan(r_part_perp_comp) else None
    results['partial_p_value_age_perplexity_complexity'] = float(p_part_perp_comp) if not np.isnan(p_part_perp_comp) else None
    logger.info(f"Age-Perplexity (|Complexity): r={r_part_perp_comp:.4f}, p={p_part_perp_comp:.4f}")

    r_part_corr_comp, p_part_corr_comp = calculate_partial_correlation(
        ages, corrects, complexities
    )
    results['partial_correlation_age_correctness_complexity'] = float(r_part_corr_comp) if not np.isnan(r_part_corr_comp) else None
    results['partial_p_value_age_correctness_complexity'] = float(p_part_corr_comp) if not np.isnan(p_part_corr_comp) else None
    logger.info(f"Age-Correctness (|Complexity): r={r_part_corr_comp:.4f}, p={p_part_corr_comp:.4f}")

    # Partial correlations controlling for token length
    logger.info("Calculating partial correlations (controlling for token length)...")
    
    r_part_perp_len, p_part_perp_len = calculate_partial_correlation(
        ages, perplexities, lengths
    )
    results['partial_correlation_age_perplexity_length'] = float(r_part_perp_len) if not np.isnan(r_part_perp_len) else None
    results['partial_p_value_age_perplexity_length'] = float(p_part_perp_len) if not np.isnan(p_part_perp_len) else None
    logger.info(f"Age-Perplexity (|Length): r={r_part_perp_len:.4f}, p={p_part_perp_len:.4f}")

    r_part_corr_len, p_part_corr_len = calculate_partial_correlation(
        ages, corrects, lengths
    )
    results['partial_correlation_age_correctness_length'] = float(r_part_corr_len) if not np.isnan(r_part_corr_len) else None
    results['partial_p_value_age_correctness_length'] = float(p_part_corr_len) if not np.isnan(p_part_corr_len) else None
    logger.info(f"Age-Correctness (|Length): r={r_part_corr_len:.4f}, p={p_part_corr_len:.4f}")

    return results


def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save correlation results to a JSON file.

    Args:
        results: Dictionary of correlation results
        output_path: Path to save the results JSON
    """
    import json
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")


def main() -> int:
    """
    Main entry point for correlation analysis.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / 'data' / 'aggregated' / 'file_metrics.csv'
    output_path = project_root / 'data' / 'results' / 'correlation_results.json'

    ensure_directories([output_path.parent])

    logger.info(f"Starting correlation analysis for {input_path}")

    try:
        # Load data
        data = load_file_metrics(input_path)

        if len(data) == 0:
            logger.error("No data loaded from input file")
            return 1

        # Define required columns
        required_columns = [
            'median_age', 'mean_perplexity', 'mean_correctness',
            'mean_complexity', 'mean_length'
        ]

        # Filter valid rows
        valid_data = filter_valid_rows(data, required_columns)

        if len(valid_data) < 3:
            logger.error(f"Insufficient valid data points: {len(valid_data)}")
            # Save empty result structure
            results = {
                'status': 'insufficient_data',
                'n_samples': len(valid_data),
                'message': 'Not enough valid data points for correlation analysis'
            }
            save_results(results, output_path)
            return 1

        # Run analysis
        results = run_correlation_analysis(valid_data)

        # Save results
        save_results(results, output_path)

        logger.info("Correlation analysis completed successfully")
        return 0

    except Exception as e:
        logger.exception(f"Error during correlation analysis: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
