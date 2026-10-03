"""
Generate the final comparison report and analysis flags for T030c.

This script aggregates results from T030a (pairwise diffs) and T030b (significance checks)
to produce:
1. data/analysis_flags.json - Machine-readable flags for SC-004 compliance
2. data/results/comparison_report.md - Human-readable comparison report

It calculates margin, p-value, odds ratio, and CI for each strategy from data/results.csv.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from statsmodels.stats.proportion import proportion_confint

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from analysis.glm_analyzer import load_results_data, calculate_pairwise_diff, check_significance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MARGIN_THRESHOLD = 5.0  # 5% threshold for "significant" improvement
P_VALUE_THRESHOLD = 0.05
MIN_SAMPLE_SIZE_CONFIRMATORY = 800


def determine_study_type(n_samples: int) -> str:
    """Determine study type based on sample size."""
    if n_samples < MIN_SAMPLE_SIZE_CONFIRMATORY:
        return "Exploratory"
    return "Confirmatory"


def calculate_odds_ratio_and_ci(pass_1b: float, pass_7b: float, n_1b: int, n_7b: int) -> Tuple[float, float, float]:
    """
    Calculate Odds Ratio and 95% CI for two proportions.
    
    Args:
        pass_1b: Pass rate for 1B model (0-1)
        pass_7b: Pass rate for 7B model (0-1)
        n_1b: Sample size for 1B model
        n_7b: Sample size for 7B model
        
    Returns:
        Tuple of (odds_ratio, ci_lower, ci_upper)
    """
    if pass_1b <= 0 or pass_1b >= 1 or pass_7b <= 0 or pass_7b >= 1:
        # Use Wilson score interval for boundary cases
        # Avoid division by zero in odds ratio
        eps = 1e-10
        pass_1b = max(eps, min(1 - eps, pass_1b))
        pass_7b = max(eps, min(1 - eps, pass_7b))
    
    # Calculate odds
    odds_1b = pass_1b / (1 - pass_1b)
    odds_7b = pass_7b / (1 - pass_7b)
    
    if odds_7b == 0:
        return np.nan, np.nan, np.nan
    
    # Odds ratio
    odds_ratio = odds_1b / odds_7b
    
    # Log odds ratio and its standard error
    log_or = np.log(odds_ratio)
    se_log_or = np.sqrt(
        (1 - pass_1b) / (pass_1b * n_1b) +
        (1 - pass_7b) / (pass_7b * n_7b)
    )
    
    # 95% CI for log odds ratio
    z = 1.96  # 95% confidence
    log_or_lower = log_or - z * se_log_or
    log_or_upper = log_or + z * se_log_or
    
    # Transform back to odds ratio scale
    ci_lower = np.exp(log_or_lower)
    ci_upper = np.exp(log_or_upper)
    
    return odds_ratio, ci_lower, ci_upper


def analyze_strategy(results_df: pd.DataFrame, strategy: str) -> Optional[Dict[str, Any]]:
    """
    Analyze a single strategy comparing 1B vs 7B models.
    
    Args:
        results_df: DataFrame with all results
        strategy: Strategy name to analyze
        
    Returns:
        Dictionary with analysis results or None if data insufficient
    """
    # Filter for this strategy
    strategy_data = results_df[results_df['strategy'] == strategy]
    
    if strategy_data.empty:
        logger.warning(f"No data found for strategy: {strategy}")
        return None
    
    # Separate by model size
    model_1b = strategy_data[strategy_data['model_size'] == '1B']
    model_7b = strategy_data[strategy_data['model_size'] == '7B']
    
    if model_1b.empty or model_7b.empty:
        logger.warning(f"Insufficient data for strategy {strategy}: 1B={len(model_1b)}, 7B={len(model_7b)}")
        return None
    
    # Calculate pass rates
    pass_1b = model_1b['pass_1'].mean()
    pass_7b = model_7b['pass_1'].mean()
    
    # Calculate sample sizes
    n_1b = len(model_1b)
    n_7b = len(model_7b)
    
    # Calculate margin (percentage difference)
    margin = (pass_1b - pass_7b) * 100
    
    # Calculate odds ratio and CI
    odds_ratio, ci_lower, ci_upper = calculate_odds_ratio_and_ci(pass_1b, pass_7b, n_1b, n_7b)
    
    # Perform significance test (simplified t-test for proportions)
    from scipy import stats
    # Two-proportion z-test
    count_1b = int(model_1b['pass_1'].sum())
    count_7b = int(model_7b['pass_1'].sum())
    
    try:
        z_stat, p_value = stats.proportions_ztest(
            [count_1b, count_7b],
            [n_1b, n_7b],
            alternative='two-sided'
        )
    except Exception as e:
        logger.warning(f"Significance test failed for {strategy}: {e}")
        p_value = np.nan
    
    return {
        'strategy': strategy,
        'margin': round(margin, 4),
        'p_value': round(p_value, 4) if not np.isnan(p_value) else None,
        'odds_ratio': round(odds_ratio, 4) if not np.isnan(odds_ratio) else None,
        'ci_lower': round(ci_lower, 4) if not np.isnan(ci_lower) else None,
        'ci_upper': round(ci_upper, 4) if not np.isnan(ci_upper) else None,
        'n_1b': n_1b,
        'n_7b': n_7b,
        'pass_1b': round(pass_1b * 100, 4),
        'pass_7b': round(pass_7b * 100, 4)
    }


def generate_flags_and_report(
    results_path: Path,
    flags_path: Path,
    report_path: Path
) -> None:
    """
    Generate analysis flags JSON and comparison report markdown.
    
    Args:
        results_path: Path to data/results.csv
        flags_path: Path to output data/analysis_flags.json
        report_path: Path to output data/results/comparison_report.md
    """
    logger.info(f"Loading results from {results_path}")
    
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    # Load data
    df = load_results_data(results_path)
    
    if df.empty:
        raise ValueError("Results DataFrame is empty")
    
    logger.info(f"Loaded {len(df)} results")
    
    # Determine study type
    total_samples = len(df)
    study_type = determine_study_type(total_samples)
    logger.info(f"Study type: {study_type} (N={total_samples})")
    
    # Get unique strategies
    strategies = df['strategy'].unique()
    logger.info(f"Analyzing strategies: {strategies}")
    
    # Analyze each strategy
    all_results = []
    strategy_found = False
    
    for strategy in strategies:
        result = analyze_strategy(df, strategy)
        if result:
            all_results.append(result)
            
            # Check if this strategy meets the criteria (1B outperforms 7B by >= 5% with p < 0.05)
            if (result['margin'] >= MARGIN_THRESHOLD and 
                result['p_value'] is not None and 
                result['p_value'] < P_VALUE_THRESHOLD):
                strategy_found = True
                logger.info(f"Strategy '{strategy}' meets criteria: margin={result['margin']}%, p={result['p_value']}")
    
    if not all_results:
        logger.warning("No strategies could be analyzed")
    
    # Prepare flags data (use the first result or aggregate if needed)
    # For SC-004, we report the best/most significant finding
    if all_results:
        # Sort by margin (descending) to find the strongest effect
        all_results.sort(key=lambda x: x['margin'], reverse=True)
        best_result = all_results[0]
        
        flags_data = {
            'strategy_found': strategy_found,
            'margin': float(best_result['margin']),
            'p_value': float(best_result['p_value']) if best_result['p_value'] is not None else None,
            'odds_ratio': float(best_result['odds_ratio']) if best_result['odds_ratio'] is not None else None,
            'ci_lower': float(best_result['ci_lower']) if best_result['ci_lower'] is not None else None,
            'ci_upper': float(best_result['ci_upper']) if best_result['ci_upper'] is not None else None,
            'study_type': study_type
        }
    else:
        flags_data = {
            'strategy_found': False,
            'margin': 0.0,
            'p_value': None,
            'odds_ratio': None,
            'ci_lower': None,
            'ci_upper': None,
            'study_type': study_type
        }
    
    # Write flags JSON
    flags_path.parent.mkdir(parents=True, exist_ok=True)
    with open(flags_path, 'w') as f:
        json.dump(flags_data, f, indent=2)
    logger.info(f"Written analysis flags to {flags_path}")
    
    # Generate markdown report
    report_lines = [
        "# Context Fidelity vs. Model Scaling: Comparison Report",
        "",
        f"**Study Type:** {study_type}",
        f"**Total Samples:** {total_samples}",
        "",
        "## Summary",
        ""
    ]
    
    if strategy_found:
        report_lines.append(f"✅ **Strategy found** where 1B outperforms 7B by ≥5% with p < 0.05.")
        report_lines.append("")
        for res in all_results:
            if res['margin'] >= MARGIN_THRESHOLD and res['p_value'] and res['p_value'] < P_VALUE_THRESHOLD:
                report_lines.append(f"- **{res['strategy']}**: margin={res['margin']}%, p={res['p_value']}, OR={res['odds_ratio']}")
    else:
        report_lines.append("❌ **No strategy found** where 1B outperforms 7B by ≥5% with p < 0.05.")
        report_lines.append("")
    
    report_lines.append("## Detailed Results by Strategy")
    report_lines.append("")
    report_lines.append("| Strategy | 1B Pass@1 | 7B Pass@1 | Margin (%) | p-value | Odds Ratio | 95% CI |")
    report_lines.append("|----------|-----------|-----------|------------|---------|------------|--------|")
    
    for res in all_results:
        ci_str = f"[{res['ci_lower']:.2f}, {res['ci_upper']:.2f}]" if res['ci_lower'] else "N/A"
        p_str = f"{res['p_value']:.4f}" if res['p_value'] else "N/A"
        or_str = f"{res['odds_ratio']:.2f}" if res['odds_ratio'] else "N/A"
        
        # Highlight significant results
        if res['margin'] >= MARGIN_THRESHOLD and res['p_value'] and res['p_value'] < P_VALUE_THRESHOLD:
            report_lines.append(
                f"| **{res['strategy']}** | {res['pass_1b']:.2f}% | {res['pass_7b']:.2f}% | "
                f"**{res['margin']:.2f}** | **{p_str}** | **{or_str}** | **{ci_str}** |"
            )
        else:
            report_lines.append(
                f"| {res['strategy']} | {res['pass_1b']:.2f}% | {res['pass_7b']:.2f}% | "
                f"{res['margin']:.2f} | {p_str} | {or_str} | {ci_str} |"
            )
    
    report_lines.append("")
    report_lines.append("## Methodology")
    report_lines.append("")
    report_lines.append("- **Margin**: Percentage point difference in Pass@1 (1B - 7B)")
    report_lines.append("- **Significance**: Two-proportion z-test")
    report_lines.append("- **Odds Ratio**: Ratio of odds of success for 1B vs 7B")
    report_lines.append("- **95% CI**: Confidence interval for the odds ratio")
    
    if study_type == "Exploratory":
        report_lines.append("")
        report_lines.append("⚠️ **Note**: This is an **Exploratory** study (N < 800).")
        report_lines.append("Primary emphasis is on Odds Ratio and 95% Confidence Intervals rather than p-values.")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append(f"*Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    # Write report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    logger.info(f"Written comparison report to {report_path}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate comparison report and analysis flags')
    parser.add_argument('--input', type=str, default='data/results.csv',
                      help='Path to results CSV file')
    parser.add_argument('--flags-output', type=str, default='data/analysis_flags.json',
                      help='Path to output flags JSON file')
    parser.add_argument('--report-output', type=str, default='data/results/comparison_report.md',
                      help='Path to output report markdown file')
    
    args = parser.parse_args()
    
    try:
        results_path = Path(args.input)
        flags_path = Path(args.flags_output)
        report_path = Path(args.report_output)
        
        generate_flags_and_report(results_path, flags_path, report_path)
        logger.info("Report generation completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()