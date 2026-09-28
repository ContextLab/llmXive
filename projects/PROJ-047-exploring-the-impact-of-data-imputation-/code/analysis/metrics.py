from typing import Dict, Any, Union, List, Optional
import numpy as np
import pandas as pd
import json
import os
from scipy import stats
from statsmodels.stats.power import tt_ind_solve_power
from statsmodels.stats.anova import AnovaRM
import warnings

def calculate_bias_metrics(estimates: List[float], ground_truth: float) -> Dict[str, float]:
    """Calculate absolute bias and RMSE."""
    if not estimates:
        return {"absolute_bias": 0.0, "rmse": 0.0}
    
    errors = np.array(estimates) - ground_truth
    abs_bias = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors**2))
    
    return {
        "absolute_bias": float(abs_bias),
        "rmse": float(rmse)
    }

def run_statistical_test(bias_matrix: pd.DataFrame) -> Dict[str, Any]:
    """
    Implement the decision tree for statistical testing:
    1. Shapiro-Wilk on bias distribution.
    2. If p < 0.05 (non-normal) -> Friedman Test.
    3. If p >= 0.05 (normal) -> Repeated-Measures ANOVA.
    4. Independently: Calculate skewness. If |skewness| > 1 -> Bootstrap CIs.
    """
    # Ensure we have valid data
    if bias_matrix.empty or 'bias' not in bias_matrix.columns:
        return {
            "test_type": "none",
            "p_value": 0.0,
            "test_statistic": 0.0,
            "skewness": 0.0,
            "bootstrap_ci_diff": 0.0,
            "conclusion": "Insufficient data"
        }

    # Aggregate by method to get bias distributions per method
    # Assuming bias_matrix has columns: 'method', 'bias' (and potentially others)
    methods = bias_matrix['method'].unique()
    if len(methods) < 2:
        return {
            "test_type": "none",
            "p_value": 0.0,
            "test_statistic": 0.0,
            "skewness": 0.0,
            "bootstrap_ci_diff": 0.0,
            "conclusion": "Need at least 2 methods"
        }

    # Prepare data for normality test (pool all biases or test per method? Spec says "bias distribution")
    # We will test the distribution of biases across all methods for normality to decide the test type.
    all_biases = bias_matrix['bias'].values
    shapiro_stat, shapiro_p = stats.shapiro(all_biases)
    
    is_normal = shapiro_p >= 0.05
    
    # Calculate skewness
    skewness = float(stats.skew(all_biases))
    
    test_type = ""
    p_value = 0.0
    test_statistic = 0.0
    conclusion = ""
    bootstrap_ci_diff = 0.0

    # Prepare data for ANOVA/Friedman (wide format needed for ANOVA, long for Friedman)
    # Pivot to get methods as columns, rows as observations (if paired)
    # Since runs are independent per method but we want to compare methods, we treat them as independent samples for ANOVA/Kruskal if not paired.
    # However, the spec implies "Repeated-Measures" which implies paired data (same seed/beta across methods).
    # We will try to pivot by 'seed' or 'run_id' if available.
    
    pivot_data = bias_matrix.pivot_table(values='bias', index='seed', columns='method', aggfunc='mean')
    pivot_data = pivot_data.dropna() # Ensure complete cases for repeated measures
    
    if pivot_data.shape[0] > 1:
        # We have paired data structure (same seeds across methods)
        if is_normal:
            # Repeated Measures ANOVA
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    anova = AnovaRM(pivot_data.reset_index(), 'bias', 'seed', within=['method'])
                    res = anova.fit()
                    test_statistic = float(res.fvalues.iloc[0])
                    p_value = float(res.pvalues.iloc[0])
                test_type = "anova"
                conclusion = "Normal distribution detected. Repeated-Measures ANOVA used."
            except Exception as e:
                # Fallback to Kruskal if ANOVA fails
                test_type = "friedman"
                _, p_value = stats.friedmanchisquare(*[pivot_data[col].values for col in pivot_data.columns])
                test_statistic = float(_)
                conclusion = f"ANOVA failed, fallback to Friedman. Error: {e}"
        else:
            # Friedman Test
            _, p_value = stats.friedmanchisquare(*[pivot_data[col].values for col in pivot_data.columns])
            test_statistic = float(_)
            test_type = "friedman"
            conclusion = "Non-normal distribution detected. Friedman Test used."
    else:
        # Not enough paired data, fall back to independent tests
        if is_normal:
            # One-way ANOVA
            groups = [bias_matrix[bias_matrix['method'] == m]['bias'].values for m in methods]
            test_statistic, p_value = stats.f_oneway(*groups)
            test_type = "anova"
            conclusion = "Normal distribution detected. One-way ANOVA used (unpaired)."
        else:
            # Kruskal-Wallis
            groups = [bias_matrix[bias_matrix['method'] == m]['bias'].values for m in methods]
            test_statistic, p_value = stats.kruskal(*groups)
            test_type = "friedman" # Using name 'friedman' to indicate non-parametric
            conclusion = "Non-normal distribution detected. Kruskal-Wallis used (unpaired)."

    # Mandatory Bootstrap CI if |skewness| > 1
    if abs(skewness) > 1:
        # Find best and worst methods by median bias
        medians = bias_matrix.groupby('method')['bias'].median()
        best_method = medians.idxmin()
        worst_method = medians.idxmax()
        
        best_vals = bias_matrix[bias_matrix['method'] == best_method]['bias'].values
        worst_vals = bias_matrix[bias_matrix['method'] == worst_method]['bias'].values
        
        # Bootstrap difference in medians
        n_boot = 1000
        diffs = []
        for _ in range(n_boot):
            b1 = np.random.choice(best_vals, size=len(best_vals), replace=True)
            b2 = np.random.choice(worst_vals, size=len(worst_vals), replace=True)
            diffs.append(np.median(b2) - np.median(b1))
        
        ci_low, ci_high = np.percentile(diffs, [2.5, 97.5])
        bootstrap_ci_diff = float(ci_high - ci_low) # Width of CI or the diff? Spec says "bootstrap_ci_diff". Let's store the width or the range.
        # Actually, usually "diff" implies the point estimate of the difference, but "bootstrap_ci_diff" implies the CI range.
        # Let's store the tuple or the width. The schema says float. Let's store the width of the interval.
        bootstrap_ci_diff = float(ci_high - ci_low)
        
        conclusion += f" Skewness={skewness:.2f} > 1. Bootstrap CI computed for median difference."

    return {
        "test_type": test_type,
        "p_value": float(p_value),
        "test_statistic": float(test_statistic),
        "skewness": skewness,
        "bootstrap_ci_diff": bootstrap_ci_diff,
        "conclusion": conclusion
    }

def save_statistical_test_results(results: Dict[str, Any], output_path: str = 'data/results/statistical_test_results.json'):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description='Run statistical tests on bias data')
    parser.add_argument('--input', type=str, required=True, help='Path to simulation_summary.csv')
    parser.add_argument('--output', type=str, default='data/results/statistical_test_results.json')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
        
    df = pd.read_csv(args.input)
    results = run_statistical_test(df)
    save_statistical_test_results(results, args.output)
    print(f"Results saved to {args.output}")

if __name__ == '__main__':
    import sys
    main()
