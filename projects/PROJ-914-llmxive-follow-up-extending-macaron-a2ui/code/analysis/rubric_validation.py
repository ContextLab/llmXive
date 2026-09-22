"""
Rubric validation module.
Validates the rubric correlation against human-annotated hold-out set.
Includes power analysis to ensure sufficient sample size.
"""
import os
import sys
import json
import argparse
import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Import project configuration
try:
    from config import get_holdout_data_path, ensure_dirs, RANDOM_SEED
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import get_holdout_data_path, ensure_dirs, RANDOM_SEED

try:
    from analysis.stats import calculate_power, validate_sample_size
except ImportError:
    from stats import calculate_power, validate_sample_size

np.random.seed(RANDOM_SEED)
logger = logging.getLogger(__name__)

def load_holdout_set(input_path: Optional[str] = None) -> 'pd.DataFrame':
    """Load the human-annotated hold-out set."""
    import pandas as pd
    if input_path is None:
        input_path = get_holdout_data_path()
        
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Hold-out set not found: {input_path}")
        
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from hold-out set")
    return df

def simulate_rubric_scoring(df: 'pd.DataFrame') -> 'pd.DataFrame':
    """
    Apply the rubric scoring to the hold-out set.
    Returns dataframe with rubric scores added.
    """
    import pandas as pd
    from simulation.rubric import calculate_alignment_score, calculate_latency_penalty
    
    scores = []
    for _, row in df.iterrows():
        # Simulate rubric calculation based on available data
        # In real usage, this would use actual latency and UI completeness
        intent_match = 1.0 if row.get('ground_truth_intent') == row.get('predicted_intent') else 0.0
        
        # Get latency from row or simulate
        latency = row.get('latency_ms', 0) / 1000.0  # Convert to seconds
        latency_penalty = calculate_latency_penalty(latency)
        
        # UI completeness (simulated or from data)
        ui_completeness = row.get('ui_completeness', 0.8)
        
        # Calculate alignment score
        score = 0.4 * intent_match + 0.3 * (1 - latency_penalty) + 0.3 * ui_completeness
        scores.append(score)
        
    df['rubric_score'] = scores
    return df

def calculate_correlation(df: 'pd.DataFrame') -> Tuple[float, float]:
    """
    Calculate correlation between rubric scores and human scores.
    Returns (correlation_coefficient, p_value).
    """
    from scipy import stats
    
    rubric_scores = df['rubric_score'].dropna().values
    human_scores = df['human_score'].dropna().values
    
    # Align indices
    common_idx = np.intersect1d(np.where(~np.isnan(rubric_scores))[0], 
                                np.where(~np.isnan(human_scores))[0])
    
    if len(common_idx) < 2:
        logger.warning("Insufficient data for correlation calculation")
        return 0.0, 1.0
        
    rubric_aligned = rubric_scores[common_idx]
    human_aligned = human_scores[common_idx]
    
    corr, p_val = stats.pearsonr(rubric_aligned, human_aligned)
    logger.info(f"Correlation calculated: r={corr:.3f}, p={p_val:.3f}")
    
    return float(corr), float(p_val)

def validate_correlation(correlation: float, threshold: float = 0.7) -> bool:
    """Validate if correlation meets the threshold."""
    return correlation >= threshold

def save_validation_report(report: Dict, output_path: str) -> None:
    """Save validation report to JSON."""
    ensure_dirs(Path(output_path))
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved validation report to {output_path}")

def print_validation_summary(report: Dict) -> None:
    """Print a summary of the validation results."""
    print("\n=== Rubric Validation Summary ===")
    print(f"Sample Size: {report['sample_size']}")
    print(f"Correlation (r): {report['correlation']:.3f}")
    print(f"P-value: {report['p_value']:.3f}")
    print(f"Threshold Met: {report['threshold_met']}")
    print(f"Power Analysis:")
    print(f"  - Required Power: {report['power_analysis']['min_power']}")
    print(f"  - Actual Power: {report['power_analysis']['actual_power']:.3f}")
    print(f"  - Sufficient: {report['power_analysis']['is_sufficient']}")
    print("================================\n")

def validate_sample_size_for_validation(n: int, min_power: float = 0.8, 
                                        effect_size: float = 0.5, 
                                        alpha: float = 0.05) -> Tuple[bool, float]:
    """
    Validate sample size for correlation analysis.
    This wraps the power calculation from stats module.
    
    Args:
        n: Sample size
        min_power: Minimum required power
        effect_size: Expected effect size (Cohen's d)
        alpha: Significance level
        
    Returns:
        Tuple of (is_sufficient, actual_power)
        
    Raises:
        ValueError: If sample size is insufficient
    """
    return validate_sample_size(n, min_power, effect_size, alpha)

def main():
    """Main entry point for rubric validation."""
    parser = argparse.ArgumentParser(description='Validate rubric against human scores')
    parser.add_argument('--input', type=str, required=True, help='Input hold-out CSV')
    parser.add_argument('--output', type=str, required=True, help='Output JSON report')
    parser.add_argument('--min-power', type=float, default=0.8, help='Minimum required power')
    parser.add_argument('--effect-size', type=float, default=0.5, help='Expected effect size')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load hold-out set
        df = load_holdout_set(args.input)
        
        # Validate sample size FIRST (T048 requirement)
        n = len(df)
        logger.info(f"Validating sample size: n={n}")
        
        is_sufficient, actual_power = validate_sample_size_for_validation(
            n, args.min_power, args.effect_size, args.alpha
        )
        
        if not is_sufficient:
            # This is the abort condition from T048
            raise ValueError(
                f"Sample size {n} is insufficient for validation. "
                f"Actual power: {actual_power:.3f} < {args.min_power}. "
                f"Please increase sample size or adjust parameters."
            )
        
        logger.info(f"Sample size validation passed. Power: {actual_power:.3f}")
        
        # Simulate rubric scoring
        df = simulate_rubric_scoring(df)
        
        # Calculate correlation
        correlation, p_value = calculate_correlation(df)
        
        # Validate against threshold
        threshold_met = validate_correlation(correlation)
        
        # Prepare report
        report = {
            'sample_size': n,
            'correlation': correlation,
            'p_value': p_value,
            'threshold_met': threshold_met,
            'threshold_value': 0.7,
            'power_analysis': {
                'min_power': args.min_power,
                'effect_size': args.effect_size,
                'alpha': args.alpha,
                'actual_power': actual_power,
                'is_sufficient': is_sufficient
            },
            'rubric_stats': {
                'mean': float(df['rubric_score'].mean()),
                'std': float(df['rubric_score'].std())
            }
        }
        
        save_validation_report(report, args.output)
        print_validation_summary(report)
        
        print(f"Validation complete. Report saved to {args.output}")
        
    except ValueError as e:
        if "insufficient" in str(e).lower():
            logger.error(f"ABORT: {e}")
            raise  # Re-raise to signal failure
        raise
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

if __name__ == '__main__':
    main()