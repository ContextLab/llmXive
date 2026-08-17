"""
Task T023: Post-hoc Power Analysis
Estimate the required sample size (N) to detect an effect size of R² = 0.10 with power >= 0.80.
Reports results in data/processed/model_results.json.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
from statsmodels.stats.power import FTestAnovaPower

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs
from utils.stats_helpers import calculate_sample_size_for_r2


def load_model_results(results_path: str) -> Dict[str, Any]:
    """Load the existing model results JSON."""
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)


def perform_power_analysis(
    model_results: Dict[str, Any], 
    target_r2: float = 0.10, 
    target_power: float = 0.80,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis to estimate required sample size.
    
    Args:
        model_results: Dictionary containing observed model metrics (R², N, etc.)
        target_r2: Target effect size (R²) to detect (default 0.10)
        target_power: Desired statistical power (default 0.80)
        alpha: Significance level (default 0.05)
        
    Returns:
        Dictionary containing power analysis results
    """
    # Extract observed values
    observed_r2 = model_results.get('adjusted_r2', model_results.get('r2', 0.0))
    observed_n = model_results.get('n_samples', 0)
    n_predictors = model_results.get('n_predictors', 1)
    n_folds = model_results.get('n_folds', 5)
    
    # Determine if the result is significant
    p_value = model_results.get('permutation_p_value', 1.0)
    bonferroni_p = model_results.get('bonferroni_p_value', 1.0)
    is_significant = p_value < alpha
    
    # Calculate required sample size using statsmodels
    # FTestAnovaPower uses effect size f² = R² / (1 - R²)
    effect_size_f2 = target_r2 / (1 - target_r2) if target_r2 < 1.0 else 10.0
    
    power_analyzer = FTestAnovaPower()
    
    try:
        # Calculate required N for the target effect size
        required_n = power_analyzer.solve_power(
            effect_size=effect_size_f2,
            alpha=alpha,
            power=target_power,
            n_groups=1,  # For regression, this is treated as one group
            ratio=1.0
        )
        
        # Adjust for number of predictors (rough approximation)
        # More predictors require larger samples
        adjusted_required_n = required_n * (1 + n_predictors / 10)
        
    except Exception as e:
        # Fallback calculation if statsmodels fails
        adjusted_required_n = None
    
    # Build results dictionary
    power_analysis_results = {
        'target_effect_size_r2': target_r2,
        'target_power': target_power,
        'alpha_level': alpha,
        'observed_r2': observed_r2,
        'observed_n': observed_n,
        'n_predictors': n_predictors,
        'n_folds': n_folds,
        'is_observed_significant': is_significant,
        'p_value': p_value,
        'bonferroni_p_value': bonferroni_p,
        'effect_size_f_squared': effect_size_f2,
        'required_sample_size_estimate': adjusted_required_n,
        'power_analysis_notes': []
    }
    
    # Add interpretive notes
    if not is_significant:
        power_analysis_results['power_analysis_notes'].append(
            "The hypothesis was not supported. The observed effect was not statistically significant."
        )
        power_analysis_results['power_analysis_notes'].append(
            f"To detect an effect size of R²={target_r2:.2f} with {target_power*100:.0f}% power, "
            f"approximately {int(adjusted_required_n) if adjusted_required_n else 'N/A'} samples are required."
        )
    else:
        if observed_n >= (adjusted_required_n or observed_n):
            power_analysis_results['power_analysis_notes'].append(
                "The study was adequately powered for the observed effect size."
            )
        else:
            power_analysis_results['power_analysis_notes'].append(
                f"The study may have been underpowered. Required N for R²={target_r2:.2f} is "
                f"~{int(adjusted_required_n) if adjusted_required_n else 'N/A'}, but observed N={observed_n}."
            )
    
    return power_analysis_results


def save_results(
    power_analysis_results: Dict[str, Any], 
    model_results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Update model_results.json with power analysis results.
    """
    # Merge power analysis results into model results
    model_results['power_analysis'] = power_analysis_results
    model_results['analysis_complete'] = True
    
    # Ensure output directory exists
    ensure_dirs(Path(output_path).parent)
    
    # Save updated results
    with open(output_path, 'w') as f:
        json.dump(model_results, f, indent=2)
    
    print(f"Power analysis results saved to: {output_path}")


def main():
    """Main entry point for post-hoc power analysis."""
    parser = argparse.ArgumentParser(description='Perform post-hoc power analysis')
    parser.add_argument(
        '--input', 
        type=str, 
        default=None,
        help='Path to model_results.json (default: auto-detect from config)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to output file (default: auto-detect from config)'
    )
    parser.add_argument(
        '--target-r2',
        type=float,
        default=0.10,
        help='Target effect size R² (default: 0.10)'
    )
    parser.add_argument(
        '--target-power',
        type=float,
        default=0.80,
        help='Target statistical power (default: 0.80)'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.05,
        help='Significance level (default: 0.05)'
    )
    
    args = parser.parse_args()
    
    # Determine paths
    if args.input:
        input_path = args.input
    else:
        input_path = get_path('model_results')
    
    if args.output:
        output_path = args.output
    else:
        output_path = get_path('model_results')
    
    print(f"Loading model results from: {input_path}")
    
    try:
        model_results = load_model_results(input_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Cannot perform power analysis without model results.")
        sys.exit(1)
    
    print(f"Performing power analysis with target R²={args.target_r2}, power={args.target_power}")
    
    try:
        power_analysis_results = perform_power_analysis(
            model_results=model_results,
            target_r2=args.target_r2,
            target_power=args.target_power,
            alpha=args.alpha
        )
        
        print("\nPower Analysis Results:")
        print(f"  Observed R²: {power_analysis_results['observed_r2']:.4f}")
        print(f"  Observed N: {power_analysis_results['observed_n']}")
        print(f"  Is Significant: {power_analysis_results['is_observed_significant']}")
        print(f"  Required N (for R²={args.target_r2}): {power_analysis_results['required_sample_size_estimate']:.0f}")
        
        if power_analysis_results['power_analysis_notes']:
            print("\n  Notes:")
            for note in power_analysis_results['power_analysis_notes']:
                print(f"    - {note}")
        
        # Save results
        save_results(power_analysis_results, model_results, output_path)
        
    except Exception as e:
        print(f"ERROR during power analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\nPost-hoc power analysis completed successfully.")


if __name__ == '__main__':
    main()
