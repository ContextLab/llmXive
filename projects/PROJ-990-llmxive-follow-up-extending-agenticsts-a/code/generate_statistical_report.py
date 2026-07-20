"""
generate_statistical_report.py

Generates the final statistical report by aggregating results from T025 (statistical testing)
and T021 (baseline comparison). It calculates effect sizes, extracts SC-001/SC-003 metrics,
and produces the final JSON report required by T028.

Input:
  - data/processed/statistical_results.json (from T025)
  - data/processed/baseline_comparison.csv (from T021)

Output:
  - data/processed/statistical_results.json (Final report with schema: {p_value, effect_size, test_type, bonferroni_adjusted, divergence_status})
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_statistical_results(filepath: Path) -> Dict[str, Any]:
    """Load the statistical results from the T025 output file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Statistical results file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    logger.info(f"Loaded statistical results from {filepath}")
    return data

def load_baseline_comparison(filepath: Path) -> pd.DataFrame:
    """Load the baseline comparison CSV from T021."""
    if not filepath.exists():
        raise FileNotFoundError(f"Baseline comparison file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded baseline comparison from {filepath}")
    return df

def calculate_effect_size(mean_diff: float, std_diff: float) -> float:
    """
    Calculate Cohen's d effect size.
    Effect Size = (Mean1 - Mean2) / StdDev_Pooled
    For simplicity in this context, we use the standard deviation of the difference.
    """
    if std_diff == 0 or np.isnan(std_diff):
        return 0.0
    return mean_diff / std_diff

def extract_sc_metrics(baseline_df: pd.DataFrame) -> Dict[str, float]:
    """
    Extract SC-001 and SC-003 metrics from the baseline comparison.
    SC-001: Win Rate Improvement (Dynamic vs Static)
    SC-003: Token Reduction (Dynamic vs Static)
    """
    # Ensure we have the necessary columns
    required_cols = ['condition', 'win_rate', 'avg_tokens']
    if not all(col in baseline_df.columns for col in required_cols):
        raise ValueError(f"Baseline comparison missing required columns: {required_cols}")

    dynamic_row = baseline_df[baseline_df['condition'] == 'dynamic'].iloc[0]
    static_row = baseline_df[baseline_df['condition'] == 'static'].iloc[0]

    # SC-001: Win Rate Improvement
    win_rate_diff = dynamic_row['win_rate'] - static_row['win_rate']
    
    # SC-003: Token Reduction (percentage)
    if static_row['avg_tokens'] > 0:
        token_reduction = (static_row['avg_tokens'] - dynamic_row['avg_tokens']) / static_row['avg_tokens'] * 100
    else:
        token_reduction = 0.0

    return {
        'sc_001_win_rate_improvement': float(win_rate_diff),
        'sc_003_token_reduction_percent': float(token_reduction)
    }

def generate_final_report(
    stat_results: Dict[str, Any], 
    baseline_df: pd.DataFrame, 
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate the final statistical report combining test results and metrics.
    """
    # Extract key values from statistical results
    # The structure of stat_results depends on T025 output, assuming a flat or nested structure
    # We expect keys like 'p_value', 'test_type', 'bonferroni_adjusted', 'divergence_status'
    
    p_value = stat_results.get('p_value', 0.0)
    test_type = stat_results.get('test_type', 'unknown')
    bonferroni_adjusted = stat_results.get('bonferroni_adjusted', False)
    divergence_status = stat_results.get('divergence_status', False)
    
    # Calculate effect size if we have token usage stats
    # Assuming stat_results contains token stats if available
    token_stats = stat_results.get('token_stats', {})
    mean_token_diff = token_stats.get('mean_diff', 0.0)
    std_token_diff = token_stats.get('std_diff', 1.0)
    
    effect_size = calculate_effect_size(mean_token_diff, std_token_diff)

    # Extract SC metrics
    sc_metrics = extract_sc_metrics(baseline_df)

    # Construct final report
    final_report = {
        'p_value': float(p_value),
        'effect_size': float(effect_size),
        'test_type': str(test_type),
        'bonferroni_adjusted': bool(bonferroni_adjusted),
        'divergence_status': bool(divergence_status),
        'sc_001_win_rate_improvement': sc_metrics['sc_001_win_rate_improvement'],
        'sc_003_token_reduction_percent': sc_metrics['sc_003_token_reduction_percent'],
        'metadata': {
            'generated_by': 'generate_statistical_report.py',
            'task_id': 'T027'
        }
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write final report
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)

    logger.info(f"Final statistical report written to {output_path}")
    return final_report

def main():
    """Main entry point for the script."""
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    stat_results_path = project_root / 'data' / 'processed' / 'statistical_results.json'
    baseline_path = project_root / 'data' / 'processed' / 'baseline_comparison.csv'
    output_path = project_root / 'data' / 'processed' / 'statistical_results.json'

    try:
        # Load inputs
        stat_results = load_statistical_results(stat_results_path)
        baseline_df = load_baseline_comparison(baseline_path)

        # Generate report
        report = generate_final_report(stat_results, baseline_df, output_path)

        print("Final Statistical Report Generated Successfully:")
        print(json.dumps(report, indent=2))

    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise

if __name__ == '__main__':
    main()