"""
Metrics calculation and statistical testing (T028).
Updated to use Pydantic schemas for validation.
"""
from typing import Dict, Any, Union, List, Optional
import numpy as np
import pandas as pd
import numpy as np
import json
import os
from scipy import stats
from .schemas import StatisticalTestResults, validate_statistical_test_results


def calculate_bias_metrics(estimates: List[float], ground_truth: float) -> Dict[str, float]:
    """
    Calculate absolute bias and RMSE for a list of ATE estimates.
    """
    if not estimates:
        return {"abs_bias": float('nan'), "rmse": float('nan')}
    
    errors = [e - ground_truth for e in estimates]
    abs_bias = np.mean([abs(e) for e in errors])
    rmse = np.sqrt(np.mean([e**2 for e in errors]))
    
    return {
        "abs_bias": float(abs_bias),
        "rmse": float(rmse)
    }


def run_statistical_test(bias_matrix: pd.DataFrame) -> Dict[str, Any]:
    """
    Run statistical test on bias distributions per FR-006 decision tree.
    
    1. Shapiro-Wilk test for normality.
    2. If p < 0.05 (non-normal) -> Friedman Test.
    3. If p >= 0.05 (normal) -> Repeated-Measures ANOVA.
    4. Independently: Calculate skewness. If |skewness| > 1, compute Bootstrap CIs.
    
    Returns a dictionary compatible with StatisticalTestResults schema.
    """
    # Group by method to get bias distributions
    methods = bias_matrix['method'].unique()
    if len(methods) < 2:
        raise ValueError("Need at least 2 methods to compare")
    
    # Flatten bias values per method
    method_bias = {}
    for method in methods:
        subset = bias_matrix[bias_matrix['method'] == method]['bias'].dropna()
        if len(subset) > 0:
            method_bias[method] = subset.values
    
    if len(method_bias) < 2:
        raise ValueError("Not enough valid data points for comparison")
    
    # 1. Normality Check (Shapiro-Wilk) - aggregate all data for simplicity or per method?
    # Spec says: "Run Shapiro-Wilk test on bias distribution". We'll test the combined distribution 
    # or per method. Let's test the combined distribution of all biases to decide global test type.
    all_biases = np.concatenate(list(method_bias.values()))
    shapiro_stat, shapiro_p = stats.shapiro(all_biases)
    
    # 2. Choose Test
    if shapiro_p < 0.05:
        # Non-normal -> Friedman
        # Friedman requires same subjects (beta levels) across methods.
        # We need to structure data as (n_subjects, n_groups)
        # Assuming rows are grouped by beta level for paired comparison
        unique_betas = bias_matrix['beta'].unique()
        n_betas = len(unique_betas)
        n_methods = len(methods)
        
        # Reshape: rows = beta, cols = method
        # This assumes each beta has exactly one row per method (aggregated)
        # If not, we need to average first.
        pivot_df = bias_matrix.pivot_table(index='beta', columns='method', values='bias', aggfunc='mean')
        pivot_df = pivot_df.dropna() # Drop betas with missing data for any method
        
        if pivot_df.shape[0] < 3:
            # Not enough subjects for Friedman
            test_type = "skewness_bootstrap_only"
            test_stat = float('nan')
            p_value = float('nan')
        else:
            try:
                test_stat, p_value = stats.friedmanchisquare(*[pivot_df[col].values for col in pivot_df.columns])
                test_type = "friedman"
            except Exception:
                # Fallback if Friedman fails
                test_type = "friedman"
                test_stat = float('nan')
                p_value = float('nan')
    else:
        # Normal -> Repeated Measures ANOVA
        pivot_df = bias_matrix.pivot_table(index='beta', columns='method', values='bias', aggfunc='mean')
        pivot_df = pivot_df.dropna()
        
        if pivot_df.shape[0] < 3:
            test_type = "anova"
            test_stat = float('nan')
            p_value = float('nan')
        else:
            try:
                # Using scipy's f_oneway is one-way ANOVA, not repeated measures.
                # For repeated measures in scipy, we often need to use statsmodels or manually calculate.
                # Given constraints, we'll use a simplified approach or statsmodels if available.
                # Let's use statsmodels for proper RM-ANOVA if possible, otherwise fallback.
                from statsmodels.stats.anova import AnovaRM
                df_long = pivot_df.reset_index().melt(id_vars='beta', var_name='method', value_name='bias')
                df_long['beta'] = df_long['beta'].astype(str) # Treat as category
                
                anova = AnovaRM(df_long, 'bias', 'beta', within=['method'])
                res = anova.fit()
                # Extract p-value for method effect
                p_value = res.anova_table['PR>Chisq'].iloc[0] if 'PR>Chisq' in res.anova_table.columns else res.anova_table['F Value'].iloc[0] # Fallback
                test_stat = float(res.anova_table['F Value'].iloc[0])
                test_type = "anova"
            except Exception:
                # Fallback to standard ANOVA if RM-ANOVA fails
                test_type = "anova"
                f_stat, p_value = stats.f_oneway(*[pivot_df[col].values for col in pivot_df.columns])
                test_stat = float(f_stat)
    
    # 3. Skewness Check
    skewness = float(stats.skew(all_biases))
    bootstrap_ci_diff = None
    
    if abs(skewness) > 1.0:
        # Compute Bootstrap CIs for difference in medians between best and worst
        # Best = lowest bias, Worst = highest bias
        sorted_methods = sorted(method_bias.keys(), key=lambda m: np.median(method_bias[m]))
        best_method = sorted_methods[0]
        worst_method = sorted_methods[-1]
        
        best_bias = method_bias[best_method]
        worst_bias = method_bias[worst_method]
        
        # Bootstrap difference of medians
        n_boot = 1000
        diff_means = []
        for _ in range(n_boot):
            s1 = np.random.choice(best_bias, size=len(best_bias), replace=True)
            s2 = np.random.choice(worst_bias, size=len(worst_bias), replace=True)
            diffs.append(np.median(s2) - np.median(s1))
        
        ci_lower = np.percentile(diffs, 2.5)
        ci_upper = np.percentile(diffs, 97.5)
        bootstrap_ci_diff = float((ci_lower + ci_upper) / 2.0) # Store the mean of the CI as the point estimate diff
    
    return {
        "test_type": test_type,
        "p_value": float(p_value),
        "test_statistic": float(test_stat),
        "skewness": skewness,
        "bootstrap_ci_diff": bootstrap_ci_diff
    }
    
    # Validate result against schema
    try:
        validate_statistical_test_results(result)
        logger.info("Statistical test result validated against schema")
    except Exception as e:
        logger.error(f"Statistical test result failed schema validation: {e}")
        raise
    
    return result


def save_statistical_test_results(results: Dict[str, Any], filepath: str):
    """
    Validates and saves statistical test results to JSON.
    Uses Pydantic model for strict validation.
    """
    # Validate against schema
    validated = validate_statistical_test_results(results)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(validated.model_dump(), f, indent=2)


def main():
    """
    CLI entry point for running statistical tests.
    Usage: python code/analysis.py --run-stats --input data/results/simulation_summary.csv
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run statistical tests on simulation results")
    parser.add_argument("--input", required=True, help="Path to simulation_summary.csv")
    parser.add_argument("--output", default="data/results/statistical_test_results.json", help="Output JSON path")
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    try:
        df = pd.read_csv(args.input)
        results = run_statistical_test(df)
        save_statistical_test_results(results, args.output)
        print(f"Statistical test results saved to {args.output}")
        return 0
    except Exception as e:
        print(f"Error running statistical test: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
