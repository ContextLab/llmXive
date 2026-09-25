import os
import sys
import json
import argparse
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

from logging_config import get_logger, log_state_event
from config import DATA_PROCESSED_DIR, OUTPUTS_DIR

logger = get_logger(__name__)

def compute_spearman_correlation_with_ci(consistency_scores: np.ndarray, trust_scores: np.ndarray) -> Dict[str, Any]:
    """
    Compute Spearman correlation coefficient and 95% confidence interval.
    
    Args:
        consistency_scores: Array of consistency metric values
        trust_scores: Array of trust scores
        
    Returns:
        Dictionary with correlation coefficient, p-value, and confidence interval
    """
    if len(consistency_scores) != len(trust_scores) or len(consistency_scores) < 2:
        raise ValueError("Input arrays must have the same length and at least 2 elements")
    
    # Compute Spearman correlation
    corr, p_value = stats.spearmanr(consistency_scores, trust_scores)
    
    # Compute 95% CI using Fisher transformation
    # Fisher z-transformation
    z = 0.5 * np.log((1 + corr) / (1 - corr))
    se_z = 1.0 / np.sqrt(len(consistency_scores) - 3)
    
    # Confidence interval for z
    z_lower = z - 1.96 * se_z
    z_upper = z + 1.96 * se_z
    
    # Back-transform to correlation scale
    ci_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    ci_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
    
    return {
        "correlation": float(corr),
        "p_value": float(p_value),
        "ci_95_lower": float(ci_lower),
        "ci_95_upper": float(ci_upper),
        "n_samples": len(consistency_scores),
        "method": "Spearman's rho"
    }

def run_ordinal_regression(
    data: pd.DataFrame,
    dependent_var: str = "trust_score",
    independent_vars: List[str] = None,
    control_vars: List[str] = None
) -> Dict[str, Any]:
    """
    Run ordinal regression (proportional odds model) with control variables.
    
    Args:
        data: DataFrame containing the analysis data
        dependent_var: Name of the dependent variable column
        independent_vars: List of primary independent variable names
        control_vars: List of control variable names (avatar_type, duration, difficulty)
        
    Returns:
        Dictionary containing model coefficients, p-values, and fit statistics
    """
    if independent_vars is None:
        independent_vars = ["consistency_score"]
    if control_vars is None:
        control_vars = ["avatar_type", "duration", "difficulty"]
    
    # Construct formula
    all_predictors = independent_vars + control_vars
    formula = f"{dependent_var} ~ " + " + ".join(all_predictors)
    
    logger.info(f"Fitting ordinal regression model: {formula}")
    
    try:
        # Fit ordinal regression model using statsmodels
        # Note: statsmodels doesn't have native ordinal regression, so we use OrderedModel
        # or fallback to a proportional odds implementation
        from statsmodels.miscmodels.ordinal_model import OrderedModel
        
        # Prepare data
        y = data[dependent_var].astype('category').cat.codes.values
        X = data[all_predictors]
        
        # Handle categorical variables
        for var in control_vars:
            if var in X.columns and X[var].dtype == 'object':
                X = pd.get_dummies(X, columns=[var], drop_first=True)
        
        # Fit model
        model = OrderedModel(y, X, distr='logit')
        result = model.fit(method='bfgs', disp=False)
        
        # Extract results
        coefficients = result.params.values
        p_values = result.pvalues.values
        pseudo_r2 = result.prsquared
        
        # Create result dictionary
        results = {
            "formula": formula,
            "pseudo_r_squared": float(pseudo_r2),
            "n_samples": len(data),
            "convergence": result.converged,
            "coefficients": {},
            "p_values": {},
            "model_fit": {
                "log_likelihood": float(result.llf),
                "pseudo_r_squared": float(pseudo_r2)
            }
        }
        
        # Map coefficients and p-values to variable names
        for i, var in enumerate(X.columns):
            results["coefficients"][var] = float(coefficients[i])
            results["p_values"][var] = float(p_values[i])
        
        # Specifically extract consistency and control variable stats
        results["consistency_stats"] = {
            "coefficient": results["coefficients"].get("consistency_score", None),
            "p_value": results["p_values"].get("consistency_score", None),
            "significant": results["p_values"].get("consistency_score", 1.0) < 0.05
        }
        
        results["control_stats"] = {}
        for var in control_vars:
            # Handle potential dummies from get_dummies
            matching_keys = [k for k in results["p_values"].keys() if var in k]
            for key in matching_keys:
                results["control_stats"][key] = {
                    "coefficient": results["coefficients"][key],
                    "p_value": results["p_values"][key],
                    "significant": results["p_values"][key] < 0.05
                }
        
        logger.info(f"Ordinal regression completed. Pseudo R-squared: {pseudo_r2:.4f}")
        return results
        
    except Exception as e:
        logger.error(f"Ordinal regression failed: {str(e)}")
        raise

def generate_analysis_report(
    spearman_results: Dict[str, Any],
    regression_results: Dict[str, Any],
    output_path: str
) -> str:
    """
    Generate a unified analysis report combining Spearman correlation and ordinal regression results.
    
    Args:
        spearman_results: Results from Spearman correlation analysis
        regression_results: Results from ordinal regression analysis
        output_path: Path to save the JSON report
        
    Returns:
        Path to the generated report
    """
    report = {
        "title": "Analysis Report: Emotional Expression in AI Avatars",
        "methodology_note": "ASSOCIATIONAL ONLY - This analysis identifies correlations and statistical relationships. No causal claims are made.",
        "spearman_correlation": spearman_results,
        "ordinal_regression": regression_results,
        "summary": {
            "consistency_trust_relationship": "Positive association detected" if spearman_results["correlation"] > 0 else "Negative or no association",
            "statistical_significance": "Significant" if spearman_results["p_value"] < 0.05 else "Not significant",
            "model_fit": f"Pseudo R-squared: {regression_results['pseudo_r_squared']:.4f}"
        }
    }
    
    # Ensure output directory exists
    os.makedirs(os.dirname(output_path), exist_ok=True)
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Analysis report saved to {output_path}")
    return output_path

def main():
    """
    Main function to run the full analysis pipeline.
    """
    parser = argparse.ArgumentParser(description="Run analysis on extracted features")
    parser.add_argument("--data", type=str, default=DATA_PROCESSED_DIR, help="Path to processed data")
    parser.add_argument("--output", type=str, default=OUTPUTS_DIR, help="Path to save outputs")
    args = parser.parse_args()
    
    # Load data
    data_path = os.path.join(args.data, "features.csv")
    if not os.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    data = pd.read_csv(data_path)
    logger.info(f"Loaded {len(data)} samples from {data_path}")
    
    # Run Spearman correlation
    spearman_results = compute_spearman_correlation_with_ci(
        data["consistency_score"].values,
        data["trust_score"].values
    )
    logger.info(f"Spearman correlation: {spearman_results['correlation']:.4f} (p={spearman_results['p_value']:.4f})")
    
    # Run ordinal regression
    regression_results = run_ordinal_regression(
        data,
        dependent_var="trust_score",
        independent_vars=["consistency_score"],
        control_vars=["avatar_type", "duration", "difficulty"]
    )
    
    # Generate report
    report_path = os.path.join(args.output, "analysis_report.json")
    generate_analysis_report(spearman_results, regression_results, report_path)
    
    # Print summary
    print("\n" + "="*50)
    print("ANALYSIS SUMMARY")
    print("="*50)
    print(f"Spearman Correlation: {spearman_results['correlation']:.4f}")
    print(f"95% CI: [{spearman_results['ci_95_lower']:.4f}, {spearman_results['ci_95_upper']:.4f}]")
    print(f"P-value: {spearman_results['p_value']:.4f}")
    print(f"\nOrdinal Regression Pseudo R-squared: {regression_results['pseudo_r_squared']:.4f}")
    print(f"Consistency Score Coefficient: {regression_results['coefficients'].get('consistency_score', 'N/A')}")
    print(f"Consistency Score p-value: {regression_results['p_values'].get('consistency_score', 'N/A')}")
    print("\nNOTE: These results represent ASSOCIATIONAL relationships only. No causal claims are made.")
    print("="*50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())