"""
Rubric validation module for the llmXive A2UI latency study.

Validates the rubric correlation against human-annotated hold-out set
and performs statistical power analysis.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional, Any

# Import from local modules
from simulation.rubric import calculate_alignment_score, score_interaction
from config import RANDOM_SEED

# Configure logging
logger = logging.getLogger(__name__)

def load_holdout_set(file_path: str) -> pd.DataFrame:
    """
    Load the human-annotated hold-out set.
    
    Args:
        file_path: Path to the hold-out set JSON file
        
    Returns:
        DataFrame containing hold-out set data
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Hold-out set not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame([data])
    
    logger.info(f"Loaded {len(df)} rows from hold-out set")
    return df

def simulate_rubric_scoring(
    df: pd.DataFrame,
    rubric_weights: Optional[Dict[str, float]] = None
) -> pd.DataFrame:
    """
    Apply the rubric scoring to the hold-out set.
    
    Args:
        df: DataFrame containing interaction data
        rubric_weights: Optional custom weights for rubric components
        
    Returns:
        DataFrame with added rubric scores
    """
    if rubric_weights is None:
        rubric_weights = {
            'intent_match': 0.4,
            'latency_penalty': 0.3,
            'ui_completeness': 0.3
        }
    
    scores = []
    for idx, row in df.iterrows():
        # Extract relevant fields
        query = row.get('query', '')
        ground_truth = row.get('ground_truth_intent', '')
        latency = row.get('latency_ms', 0)
        ui_elements = row.get('ui_element_count', 0)
        
        # Calculate rubric components
        intent_match = 1.0 if query == ground_truth else 0.0
        latency_penalty = 1 - min(1, latency / 2000.0) if latency > 0 else 1.0
        ui_completeness = min(1.0, ui_elements / 10.0) if ui_elements > 0 else 0.0
        
        # Calculate total alignment score
        alignment_score = (
            rubric_weights['intent_match'] * intent_match +
            rubric_weights['latency_penalty'] * latency_penalty +
            rubric_weights['ui_completeness'] * ui_completeness
        )
        
        scores.append({
            'query': query,
            'ground_truth': ground_truth,
            'rubric_score': alignment_score,
            'intent_match': intent_match,
            'latency_penalty': latency_penalty,
            'ui_completeness': ui_completeness
        })
    
    result_df = pd.DataFrame(scores)
    return pd.concat([df.reset_index(drop=True), result_df], axis=1)

def calculate_correlation(
    df: pd.DataFrame,
    rubric_score_col: str = 'rubric_score',
    human_score_col: str = 'score'
) -> Dict[str, float]:
    """
    Calculate correlation between rubric scores and human scores.
    
    Args:
        df: DataFrame containing both rubric and human scores
        rubric_score_col: Column name for rubric scores
        human_score_col: Column name for human scores
        
    Returns:
        Dictionary containing correlation metrics
    """
    # Remove rows with missing values
    valid_data = df[[rubric_score_col, human_score_col]].dropna()
    
    if len(valid_data) < 2:
        logger.warning("Insufficient data for correlation calculation")
        return {
            'pearson_r': None,
            'pearson_p': None,
            'spearman_r': None,
            'spearman_p': None,
            'n': len(valid_data)
        }
    
    # Pearson correlation
    pearson_r, pearson_p = stats.pearsonr(
        valid_data[rubric_score_col], 
        valid_data[human_score_col]
    )
    
    # Spearman correlation
    spearman_r, spearman_p = stats.spearmanr(
        valid_data[rubric_score_col], 
        valid_data[human_score_col]
    )
    
    return {
        'pearson_r': float(pearson_r),
        'pearson_p': float(pearson_p),
        'spearman_r': float(spearman_r),
        'spearman_p': float(spearman_p),
        'n': len(valid_data)
    }

def validate_correlation(
    correlation_results: Dict[str, float],
    min_correlation: float = 0.7,
    min_power: float = 0.8,
    expected_effect_size: float = 0.5
) -> Dict[str, Any]:
    """
    Validate if the correlation meets the required threshold.
    
    Args:
        correlation_results: Dictionary containing correlation metrics
        min_correlation: Minimum required correlation coefficient
        min_power: Minimum required statistical power
        expected_effect_size: Expected effect size for power calculation
        
    Returns:
        Dictionary containing validation results
    """
    n = correlation_results.get('n', 0)
    pearson_r = correlation_results.get('pearson_r')
    
    # Power analysis
    power_result = validate_sample_size(
        n,
        expected_effect_size=expected_effect_size,
        min_power=min_power
    )
    
    # Correlation validation
    correlation_valid = pearson_r is not None and pearson_r >= min_correlation
    
    validation = {
        'correlation_valid': correlation_valid,
        'power_valid': power_result['is_sufficient'],
        'overall_valid': correlation_valid and power_result['is_sufficient'],
        'correlation_threshold': min_correlation,
        'power_threshold': min_power,
        'correlation_details': correlation_results,
        'power_details': power_result
    }
    
    if not validation['overall_valid']:
        reasons = []
        if not correlation_valid:
            reasons.append(f"Correlation {pearson_r:.3f} < {min_correlation}")
        if not power_result['is_sufficient']:
            reasons.append(f"Power {power_result['calculated_power']:.3f} < {min_power}")
        
        logger.warning("Validation failed: " + "; ".join(reasons))
    
    return validation

def save_validation_report(
    report: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save validation report to a JSON file.
    
    Args:
        report: Dictionary containing validation results
        output_path: Path for output JSON file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Saved validation report to {output_path}")

def print_validation_summary(validation: Dict[str, Any]) -> None:
    """
    Print a summary of the validation results.
    
    Args:
        validation: Dictionary containing validation results
    """
    print("\n" + "="*60)
    print("RUBRIC VALIDATION SUMMARY")
    print("="*60)
    
    corr = validation.get('correlation_details', {})
    power = validation.get('power_details', {})
    
    print(f"Sample Size (n): {corr.get('n', 0)}")
    print(f"Pearson Correlation (r): {corr.get('pearson_r', 'N/A'):.3f}" if corr.get('pearson_r') else "Pearson Correlation (r): N/A")
    print(f"Pearson p-value: {corr.get('pearson_p', 'N/A'):.4f}" if corr.get('pearson_p') else "Pearson p-value: N/A")
    print(f"Spearman Correlation (r): {corr.get('spearman_r', 'N/A'):.3f}" if corr.get('spearman_r') else "Spearman Correlation (r): N/A")
    print(f"Spearman p-value: {corr.get('spearman_p', 'N/A'):.4f}" if corr.get('spearman_p') else "Spearman p-value: N/A")
    print("-"*60)
    print(f"Statistical Power: {power.get('calculated_power', 'N/A'):.3f}")
    print(f"Required Power: {validation.get('power_threshold', 0.8)}")
    print(f"Power Sufficient: {'Yes' if power.get('is_sufficient') else 'No'}")
    print("-"*60)
    print(f"Correlation Threshold: {validation.get('correlation_threshold', 0.7)}")
    print(f"Correlation Sufficient: {'Yes' if validation.get('correlation_valid') else 'No'}")
    print("="*60)
    print(f"OVERALL VALIDATION: {'PASSED' if validation.get('overall_valid') else 'FAILED'}")
    print("="*60 + "\n")

def validate_sample_size(
    n: int,
    expected_effect_size: float = 0.5,
    min_power: float = 0.8,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Validate if sample size is sufficient for the expected effect size.
    
    Args:
        n: Sample size
        expected_effect_size: Expected Cohen's d
        min_power: Minimum required power (default 0.8)
        alpha: Significance level
        
    Returns:
        Dictionary with validation results
    """
    from analysis.stats import calculate_power
    
    power = calculate_power(n, expected_effect_size, alpha)
    
    result = {
        'sample_size': n,
        'expected_effect_size': expected_effect_size,
        'calculated_power': power,
        'min_required_power': min_power,
        'is_sufficient': power >= min_power,
        'alpha': alpha
    }
    
    if not result['is_sufficient']:
        logger.warning(
            f"Sample size {n} is insufficient for effect size {expected_effect_size}. "
            f"Power: {power:.3f} < {min_power}"
        )
        # Calculate required sample size
        required_n = 0
        for test_n in range(n, 10000):
            test_power = calculate_power(test_n, expected_effect_size, alpha)
            if test_power >= min_power:
                required_n = test_n
                break
        
        result['required_sample_size'] = required_n if required_n > 0 else None
        result['power_deficit'] = min_power - power
    
    return result

def main():
    """Main entry point for rubric validation."""
    parser = argparse.ArgumentParser(description='Validate rubric against human annotations')
    parser.add_argument('--holdout', type=str, required=True, help='Path to hold-out set JSON file')
    parser.add_argument('--baseline', type=str, required=True, help='Path to baseline simulation results CSV')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file for validation report')
    parser.add_argument('--min-correlation', type=float, default=0.7, help='Minimum required correlation')
    parser.add_argument('--min-power', type=float, default=0.8, help='Minimum required statistical power')
    parser.add_argument('--effect-size', type=float, default=0.5, help='Expected effect size for power calculation')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load hold-out set
        holdout_df = load_holdout_set(args.holdout)
        
        # Load baseline results
        baseline_df = pd.read_csv(args.baseline)
        
        # Merge datasets (assuming they can be matched by query or index)
        # For simplicity, we'll assume the holdout set is a subset of the baseline
        if 'query' in holdout_df.columns and 'query' in baseline_df.columns:
            merged_df = pd.merge(holdout_df, baseline_df, on='query', how='inner')
        else:
            # Fallback: use index if available
            merged_df = pd.concat([holdout_df, baseline_df], axis=1)
        
        # Simulate rubric scoring
        scored_df = simulate_rubric_scoring(merged_df)
        
        # Calculate correlation
        correlation_results = calculate_correlation(scored_df)
        
        # Validate correlation and power
        validation = validate_correlation(
            correlation_results,
            min_correlation=args.min_correlation,
            min_power=args.min_power,
            expected_effect_size=args.effect_size
        )
        
        # Compile report
        report = {
            'holdout_set_path': args.holdout,
            'baseline_path': args.baseline,
            'sample_size': correlation_results.get('n', 0),
            'correlation_results': correlation_results,
            'validation': validation,
            'parameters': {
                'min_correlation': args.min_correlation,
                'min_power': args.min_power,
                'expected_effect_size': args.effect_size
            }
        }
        
        # Save report
        save_validation_report(report, args.output)
        
        # Print summary
        print_validation_summary(validation)
        
        if not validation['overall_valid']:
            logger.error("Validation failed. Check the report for details.")
            sys.exit(1)
        else:
            print("Validation passed!")
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

if __name__ == '__main__':
    main()