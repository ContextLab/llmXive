"""
Analysis module for computing Spearman correlation and ordinal regression.

This module implements:
- T016: Spearman correlation with 95% CI
- T021: Ordinal regression with control variables
"""
from __future__ import annotations

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from scipy import stats

# Import from sibling modules per API surface
from logging_config import get_logger, log_state_event
from config import PROJECT_ROOT, DATA_PROCESSED_DIR, OUTPUTS_DIR

logger = get_logger(__name__)

def compute_spearman_correlation_with_ci(
    consistency_scores: np.ndarray,
    trust_scores: np.ndarray,
    confidence_level: float = 0.95
) -> Tuple[float, float, float]:
    """
    Compute Spearman correlation coefficient and 95% confidence interval.
    
    Uses Fisher z-transformation for CI calculation as per FR-005.
    
    Args:
        consistency_scores: Array of consistency metric values
        trust_scores: Array of trust scores
        confidence_level: Confidence level for interval (default 0.95)
        
    Returns:
        Tuple of (correlation_coefficient, ci_lower, ci_upper)
    """
    n = len(consistency_scores)
    if n < 3:
        raise ValueError("Need at least 3 data points for correlation analysis")
    
    # Compute Spearman correlation
    corr, p_value = stats.spearmanr(consistency_scores, trust_scores)
    
    if np.isnan(corr):
        raise ValueError("Correlation is NaN - check for constant or invalid data")
    
    # Fisher z-transformation for CI
    # z = 0.5 * ln((1+r)/(1-r))
    # SE_z = 1 / sqrt(n-3)
    # CI_z = z +/- z_critical * SE_z
    # Back-transform: r = (exp(2*z) - 1) / (exp(2*z) + 1)
    
    z = 0.5 * np.log((1 + corr) / (1 - corr + 1e-10))
    se_z = 1.0 / np.sqrt(n - 3)
    
    # Critical value for two-tailed test
    z_critical = stats.norm.ppf(1 - (1 - confidence_level) / 2)
    
    ci_z_lower = z - z_critical * se_z
    ci_z_upper = z + z_critical * se_z
    
    # Back-transform
    ci_lower = (np.exp(2 * ci_z_lower) - 1) / (np.exp(2 * ci_z_lower) + 1)
    ci_upper = (np.exp(2 * ci_z_upper) - 1) / (np.exp(2 * ci_z_upper) + 1)
    
    return corr, ci_lower, ci_upper

def run_ordinal_regression(
    df: pd.DataFrame,
    consistency_col: str = 'consistency_score',
    trust_col: str = 'trust_score',
    control_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run ordinal regression (proportional odds model) with control variables.
    
    Args:
        df: DataFrame with consistency scores, trust scores, and controls
        consistency_col: Column name for consistency scores
        trust_col: Column name for trust scores (ordinal dependent variable)
        control_cols: List of control variable column names
        
    Returns:
        Dictionary with coefficients, p-values, and pseudo R-squared
    """
    try:
        import statsmodels.api as sm
        from statsmodels.miscmodels.ordinal_model import OrderedModel
    except ImportError:
        raise ImportError("statsmodels is required for ordinal regression. Install via: pip install statsmodels")
    
    # Prepare data
    y = df[trust_col].values
    X_controls = df[control_cols].values if control_cols else np.zeros((len(df), 0))
    X_consistency = df[consistency_col].values.reshape(-1, 1)
    
    # Combine predictors
    X = np.hstack([X_consistency, X_controls]) if X_controls.size > 0 else X_consistency
    
    # Add column names for results
    col_names = [consistency_col] + (control_cols if control_cols else [])
    
    # Fit Ordered Model (proportional odds)
    model = OrderedModel(y, X, distr='logit')
    result = model.fit(method='bfgs', disp=False)
    
    # Extract results
    coefficients = result.params.values
    p_values = result.pvalues.values
    pseudo_r2 = result.prsquared
    
    # Log results
    logger.log_operation("ordinal_regression_fitted", 
                       n_observations=len(df),
                       pseudo_r2=float(pseudo_r2))
    
    return {
        'coefficients': dict(zip(col_names, coefficients)),
        'p_values': dict(zip(col_names, p_values)),
        'pseudo_r_squared': float(pseudo_r2),
        'n_observations': len(df),
        'log_likelihood': float(result.llf)
    }

def generate_analysis_report(
    correlation_results: Dict[str, Any],
    regression_results: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Generate a summary report of analysis results.
    
    Args:
        correlation_results: Results from Spearman correlation
        regression_results: Optional results from ordinal regression
        output_path: Optional path to write report
        
    Returns:
        Report string
    """
    lines = [
        "# Analysis Report",
        "",
        "## Spearman Correlation Analysis",
        "",
        f"- **Coefficient**: {correlation_results['coefficient']:.4f}",
        f"- **95% CI**: [{correlation_results['ci_lower']:.4f}, {correlation_results['ci_upper']:.4f}]",
        f"- **P-value**: {correlation_results['p_value']:.4f}",
        f"- **N observations**: {correlation_results['n_observations']}",
        "",
        "## Ordinal Regression Analysis",
        ""
    ]
    
    if regression_results:
        lines.append("### Model Fit")
        lines.append(f"- **Pseudo R-squared**: {regression_results['pseudo_r_squared']:.4f}")
        lines.append(f"- **N observations**: {regression_results['n_observations']}")
        lines.append(f"- **Log-likelihood**: {regression_results['log_likelihood']:.4f}")
        lines.append("")
        
        lines.append("### Coefficients")
        lines.append("| Variable | Coefficient | P-value |")
        lines.append("|----------|-------------|---------|")
        for var, coef in regression_results['coefficients'].items():
            p_val = regression_results['p_values'].get(var, 'N/A')
            lines.append(f"| {var} | {coef:.4f} | {p_val:.4f} |")
        lines.append("")
    else:
        lines.append("Ordinal regression was not performed.")
        lines.append("")
    
    lines.append("## Notes")
    lines.append("- **Associational Only**: These results indicate association, not causation.")
    lines.append("- **Confidence Interval**: Calculated using Fisher z-transformation.")
    
    report = "\n".join(lines)
    
    if output_path:
        with open(output_path, 'w') as f:
            f.write(report)
        logger.log_operation("report_written", path=output_path)
    
    return report

def main():
    """
    Main entry point for T016: Spearman correlation analysis.
    
    Reads consistency scores from T015 output (metrics.csv) and computes
    Spearman correlation with trust scores, outputting results to metrics.csv
    with correlation coefficient and 95% CI.
    """
    # Parse arguments
    parser = argparse.ArgumentParser(description='Compute Spearman correlation with CI')
    parser.add_argument('--input', type=str, 
                      default=os.path.join(DATA_PROCESSED_DIR, 'metrics.csv'),
                      help='Input CSV with consistency and trust scores')
    parser.add_argument('--output', type=str,
                      default=os.path.join(DATA_PROCESSED_DIR, 'metrics.csv'),
                      help='Output CSV with correlation results')
    parser.add_argument('--consistency-col', type=str, default='consistency_score',
                      help='Column name for consistency scores')
    parser.add_argument('--trust-col', type=str, default='trust_score',
                      help='Column name for trust scores')
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.input):
        logger.log_operation("analysis_failed", reason="Input file not found", path=args.input)
        print(f"ERROR: Input file not found: {args.input}")
        print("Please ensure T015 has completed successfully.")
        sys.exit(1)
    
    # Load data
    logger.log_operation("loading_data", path=args.input)
    try:
        df = pd.read_csv(args.input)
    except Exception as e:
        logger.log_operation("analysis_failed", reason=str(e))
        print(f"ERROR: Failed to load input file: {e}")
        sys.exit(1)
    
    # Validate required columns
    if args.consistency_col not in df.columns or args.trust_col not in df.columns:
        logger.log_operation("analysis_failed", 
                           reason="Missing required columns",
                           expected=[args.consistency_col, args.trust_col],
                           found=list(df.columns))
        print(f"ERROR: Missing required columns. Expected: {args.consistency_col}, {args.trust_col}")
        print(f"Found columns: {list(df.columns)}")
        sys.exit(1)
    
    # Extract arrays
    consistency = df[args.consistency_col].dropna().values
    trust = df[args.trust_col].dropna().values
    
    # Ensure same length after dropna (should be aligned)
    min_len = min(len(consistency), len(trust))
    consistency = consistency[:min_len]
    trust = trust[:min_len]
    
    if len(consistency) < 3:
        logger.log_operation("analysis_failed", reason="Insufficient data points")
        print(f"ERROR: Need at least 3 data points, found {len(consistency)}")
        sys.exit(1)
    
    # Compute correlation
    logger.log_operation("computing_correlation", n_points=len(consistency))
    try:
        corr, ci_lower, ci_upper = compute_spearman_correlation_with_ci(
            consistency, trust, confidence_level=0.95
        )
    except Exception as e:
        logger.log_operation("analysis_failed", reason=str(e))
        print(f"ERROR: Correlation computation failed: {e}")
        sys.exit(1)
    
    # Get p-value
    _, p_value = stats.spearmanr(consistency, trust)
    
    # Prepare results
    results = {
        'coefficient': corr,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'p_value': p_value,
        'n_observations': len(consistency)
    }
    
    # Log success
    logger.log_operation("correlation_computed", **results)
    
    # Write results to CSV (append to existing or create new)
    logger.log_operation("writing_results", path=args.output)
    
    # If file exists, read and append summary row; otherwise create new
    if os.path.exists(args.output):
        existing = pd.read_csv(args.output)
    else:
        existing = pd.DataFrame()
    
    # Add correlation summary as a new row with interaction_id='SUMMARY'
    summary_row = pd.DataFrame([{
        'interaction_id': 'SUMMARY',
        'consistency_score': results['coefficient'],
        'trust_score': results['ci_lower'],
        'ci_upper': results['ci_upper'],
        'p_value': results['p_value'],
        'n_observations': results['n_observations']
    }])
    
    # Write combined results
    combined = pd.concat([existing, summary_row], ignore_index=True)
    combined.to_csv(args.output, index=False)
    
    # Also write a separate summary file for easy access
    summary_path = os.path.join(OUTPUTS_DIR, 'correlation_results.json')
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analysis complete.")
    print(f"  Correlation coefficient: {corr:.4f}")
    print(f"  95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    print(f"  P-value: {p_value:.4f}")
    print(f"  N observations: {len(consistency)}")
    print(f"Results written to: {args.output}")
    print(f"JSON summary written to: {summary_path}")

if __name__ == '__main__':
    main()