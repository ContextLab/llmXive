import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import json
from pathlib import Path
import logging
from scipy import stats

from config import get_path

logger = logging.getLogger(__name__)

# --- Existing Functions (Preserved) ---

def calculate_vif(df: pd.DataFrame, variable: str) -> float:
    """
    Calculate Variance Inflation Factor for a specific variable in a DataFrame.
    """
    if variable not in df.columns:
        raise ValueError(f"Variable {variable} not found in DataFrame")
    
    # Prepare design matrix excluding the target variable
    X = df.drop(columns=[variable])
    # Handle non-numeric columns by dropping them or encoding if necessary
    # For simplicity in this context, we assume numeric predictors or that preprocessing handled it
    X = X.select_dtypes(include=[np.number])
    
    if X.empty:
        return 1.0
    
    # Fit linear model of target variable against others
    y = df[variable]
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    try:
        model = sm.OLS(y, X_with_const).fit()
        r_squared = model.rsquared
        vif = 1.0 / (1.0 - r_squared)
        return vif
    except Exception as e:
        logger.warning(f"Could not calculate VIF for {variable}: {e}")
        return float('inf')

def check_collinearity(df: pd.DataFrame, variables: List[str], threshold: float = 5.0) -> Dict[str, float]:
    """
    Check VIF for a list of variables and flag those exceeding threshold.
    """
    results = {}
    for var in variables:
        vif = calculate_vif(df, var)
        results[var] = vif
        if vif > threshold:
            logger.warning(f"High collinearity detected for {var}: VIF={vif:.2f}")
    return results

def run_vif_analysis(df: pd.DataFrame, variables: List[str], threshold: float = 5.0) -> Dict[str, Any]:
    """
    Run full VIF analysis and return summary.
    """
    vif_values = check_collinearity(df, variables, threshold)
    flagged = {k: v for k, v in vif_values.items() if v > threshold}
    return {
        "vif_values": vif_values,
        "flagged_variables": list(flagged.keys()),
        "threshold": threshold,
        "is_clean": len(flagged) == 0
    }

def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Perform Benjamini-Hochberg FDR correction.
    Returns list of booleans (True if significant) and adjusted p-values.
    """
    n = len(p_values)
    if n == 0:
        return [], []
    
    # Sort p-values with original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    # Calculate adjusted p-values
    # Formula: p_adj[i] = p[i] * n / i
    # We also need to ensure monotonicity (cumulative min from right)
    adjusted = np.zeros(n)
    for i in range(n):
        adjusted[i] = sorted_p[i] * n / (i + 1)
    
    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i+1])
        
    # Map back to original order
    final_adjusted = np.zeros(n)
    final_adjusted[sorted_indices] = adjusted
    
    # Determine significance
    significant = final_adjusted <= alpha
    
    return significant.tolist(), final_adjusted.tolist()

def calculate_model_convergence_metrics(convergence_results: List[bool], threshold: float = 0.80) -> Dict[str, Any]:
    """
    Calculate convergence success rate.
    """
    total = len(convergence_results)
    if total == 0:
        rate = 0.0
    else:
        rate = sum(convergence_results) / total
    
    return {
        "convergence_rate": rate,
        "total_attempts": total,
        "successful_attempts": sum(convergence_results),
        "threshold": threshold,
        "meets_target": rate >= threshold
    }

def save_convergence_metrics(metrics: Dict[str, Any], output_path: Optional[Path] = None):
    """
    Save convergence metrics to JSON.
    """
    if output_path is None:
        output_path = get_path("state/model_convergence_metrics.json")
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved convergence metrics to {output_path}")

def run_fdr_correction_on_model_results(results_df: pd.DataFrame, p_column: str, alpha: float = 0.05) -> pd.DataFrame:
    """
    Apply FDR correction to a dataframe of model results.
    """
    p_values = results_df[p_column].tolist()
    significant, adjusted_p = benjamini_hochberg(p_values, alpha)
    
    results_df = results_df.copy()
    results_df['p_adj'] = adjusted_p
    results_df['is_significant_fdr'] = significant
    return results_df

def calculate_cohens_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    """
    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(), group2.std()
    n1, n2 = len(group1), len(group2)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
        
    return (mean1 - mean2) / pooled_std

def calculate_partial_eta_squared(ss_effect: float, ss_error: float) -> float:
    """
    Calculate partial eta-squared.
    """
    if ss_error == 0:
        return 0.0
    return ss_effect / (ss_effect + ss_error)

def bootstrap_effect_size(data: pd.Series, n_bootstrap: int = 1000, ci: float = 0.95) -> Tuple[float, float, float]:
    """
    Bootstrap effect size (mean) with confidence interval.
    Returns: (mean, lower_ci, upper_ci)
    """
    bootstrap_means = []
    for _ in range(n_bootstrap):
        sample = data.sample(n=len(data), replace=True)
        bootstrap_means.append(sample.mean())
    
    mean = np.mean(bootstrap_means)
    lower = np.percentile(bootstrap_means, (1 - ci) / 2 * 100)
    upper = np.percentile(bootstrap_means, (1 + ci) / 2 * 100)
    
    return mean, lower, upper

def calculate_effect_sizes_with_bootstrap(data: pd.DataFrame, group_col: str, value_col: str, n_bootstrap: int = 1000) -> Dict[str, Any]:
    """
    Calculate effect sizes (Cohen's d) with bootstrapped CIs.
    """
    groups = data[group_col].unique()
    if len(groups) != 2:
        logger.warning("Effect size calculation requires exactly two groups.")
        return {}
    
    g1, g2 = data[data[group_col] == groups[0]][value_col], data[data[group_col] == groups[1]][value_col]
    
    d = calculate_cohens_d(g1, g2)
    
    # Bootstrap the difference in means
    diff_means = []
    for _ in range(n_bootstrap):
        s1 = g1.sample(n=len(g1), replace=True)
        s2 = g2.sample(n=len(g2), replace=True)
        diff_means.append(s1.mean() - s2.mean())
    
    lower = np.percentile(diff_means, 2.5)
    upper = np.percentile(diff_means, 97.5)
    
    return {
        "cohens_d": d,
        "mean_diff_bootstrap_ci": (lower, upper),
        "n_bootstrap": n_bootstrap
    }

def save_effect_sizes(effect_data: Dict[str, Any], output_path: Optional[Path] = None):
    """
    Save effect sizes to JSON.
    """
    if output_path is None:
        output_path = get_path("data/processed/effect_sizes.json")
    
    with open(output_path, 'w') as f:
        json.dump(effect_data, f, indent=2)
    logger.info(f"Saved effect sizes to {output_path}")

# --- New Implementation for T035: Alpha Sensitivity Analysis ---

def calculate_sensitivity_analysis(results_df: pd.DataFrame, p_column: str = 'p_value', alphas: Optional[List[float]] = None) -> pd.DataFrame:
    """
    Perform alpha sensitivity analysis.
    
    Sweeps through significance thresholds (alphas) and calculates the 
    percentage of results that are significant at each threshold.
    
    Args:
        results_df: DataFrame containing model results (e.g., from LMM).
        p_column: Name of the column containing p-values.
        alphas: List of alpha thresholds to test. Defaults to [0.001, 0.01, 0.05, 0.10].
        
    Returns:
        DataFrame with columns: alpha, significance_rate
    """
    if alphas is None:
        alphas = [0.001, 0.01, 0.05, 0.10]
    
    if p_column not in results_df.columns:
        raise ValueError(f"Column '{p_column}' not found in results DataFrame. Available: {results_df.columns.tolist()}")
    
    p_values = results_df[p_column].dropna()
    total_tests = len(p_values)
    
    if total_tests == 0:
        logger.warning("No p-values found to analyze for sensitivity.")
        return pd.DataFrame(columns=['alpha', 'significance_rate'])
    
    results = []
    for alpha in sorted(alphas):
        # Count significant tests at this alpha
        significant_count = (p_values <= alpha).sum()
        rate = significant_count / total_tests
        results.append({
            'alpha': alpha,
            'significance_rate': rate,
            'significant_count': int(significant_count),
            'total_tests': total_tests
        })
    
    return pd.DataFrame(results)

def run_sensitivity_analysis(input_path: Optional[Path] = None, output_path: Optional[Path] = None, alphas: Optional[List[float]] = None):
    """
    Main entry point to run sensitivity analysis on model results.
    
    1. Loads the LMM results (expected at data/processed/lmm_results.csv).
    2. Calculates significance rates for specified alpha levels.
    3. Saves the output to data/processed/sensitivity_analysis.csv.
    """
    if input_path is None:
        input_path = get_path("data/processed/lmm_results.csv")
    
    if output_path is None:
        output_path = get_path("data/processed/sensitivity_analysis.csv")
    
    logger.info(f"Loading model results from {input_path}")
    
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Please ensure LMM analysis has been run first.")
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read input CSV: {e}")
    
    logger.info(f"Loaded {len(df)} results. Columns: {df.columns.tolist()}")
    
    # Determine p-value column if not standard
    p_col = 'p_value'
    if p_col not in df.columns and 'p' in df.columns:
        p_col = 'p'
    
    if p_col not in df.columns:
        # Try to find any column that looks like p-values (0-1 range)
        possible_cols = [c for c in df.columns if df[c].dtype in [float, int] and df[c].min() >= 0 and df[c].max() <= 1]
        if possible_cols:
            p_col = possible_cols[0]
            logger.warning(f"Standard p-value column not found. Using '{p_col}' as proxy.")
        else:
            raise ValueError("Could not identify a p-value column in the input data.")
    
    logger.info(f"Performing sensitivity analysis on column '{p_col}' with alphas: {alphas}")
    
    sensitivity_df = calculate_sensitivity_analysis(df, p_column=p_col, alphas=alphas)
    
    logger.info(f"Sensitivity Analysis Results:\n{sensitivity_df.to_string(index=False)}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    sensitivity_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity analysis saved to {output_path}")
    
    return sensitivity_df

def main():
    """
    CLI entry point for sensitivity analysis.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run alpha sensitivity analysis on LMM results.")
    parser.add_argument("--input", type=str, help="Path to input LMM results CSV")
    parser.add_argument("--output", type=str, help="Path to output sensitivity analysis CSV")
    parser.add_argument("--alphas", type=str, help="Comma-separated list of alpha thresholds (e.g., '0.001,0.01,0.05,0.10')")
    
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else None
    output_path = Path(args.output) if args.output else None
    
    alphas = None
    if args.alphas:
        alphas = [float(x.strip()) for x in args.alphas.split(',')]
    
    try:
        run_sensitivity_analysis(input_path, output_path, alphas)
        print("Sensitivity analysis completed successfully.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
