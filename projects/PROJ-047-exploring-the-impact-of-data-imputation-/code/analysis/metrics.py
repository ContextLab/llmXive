"""
Metrics module for calculating bias and error metrics in causal inference studies.
"""
from typing import Dict, Any, Union, List, Optional
import numpy as np
import pandas as pd
import json
import os
from scipy import stats
from scipy.stats import shapiro, skew, friedmanchisquare
from statsmodels.stats.anova import AnovaRM
from statsmodels.stats.multicomp import pairwise_tukeyhsd

from .entities import CausalEstimate

def calculate_bias_metrics(
    estimates: Union[list[CausalEstimate], pd.DataFrame],
    ground_truth: float
) -> Dict[str, float]:
    """
    Calculate absolute bias and Root Mean Squared Error (RMSE) for a set of ATE estimates.

    This function implements FR-005 requirements for bias quantification.

    Args:
        estimates: A list of CausalEstimate objects or a DataFrame containing 'ate' column.
                   Each estimate represents an ATE calculation from a specific method/estimator.
        ground_truth: The known true ATE value (tau_true) from the data generation process.

    Returns:
        A dictionary containing:
            - 'absolute_bias': The mean absolute difference between estimates and ground truth.
            - 'rmse': The Root Mean Squared Error of the estimates.
            - 'mean_estimate': The mean of the provided estimates.
            - 'count': The number of estimates processed.

    Raises:
        ValueError: If estimates list is empty or if ground_truth is not a valid number.
        TypeError: If estimates input is not a list of CausalEstimate or a DataFrame.
    """
    if ground_truth is None or not isinstance(ground_truth, (int, float)):
        raise ValueError("ground_truth must be a valid numeric value.")

    # Extract ATE values from input
    ate_values = []

    if isinstance(estimates, pd.DataFrame):
        if 'ate' not in estimates.columns:
            raise ValueError("DataFrame must contain an 'ate' column.")
        ate_values = estimates['ate'].dropna().values
    elif isinstance(estimates, list):
        if not estimates:
            raise ValueError("Estimates list cannot be empty.")
        
        for est in estimates:
            if not isinstance(est, CausalEstimate):
                raise TypeError(f"Expected list of CausalEstimate, got {type(est)}")
            if est.ate is not None and not np.isnan(est.ate):
                ate_values.append(est.ate)
        ate_values = np.array(ate_values)
    else:
        raise TypeError("estimates must be a list of CausalEstimate or a pandas DataFrame.")

    if len(ate_values) == 0:
        raise ValueError("No valid ATE values found in estimates.")

    # Convert to numpy array for calculation
    ate_array = np.array(ate_values)

    # Calculate Absolute Bias (Mean Absolute Error)
    # Bias = E[estimate] - truth
    # Absolute Bias usually refers to Mean Absolute Error (MAE) in this context,
    # or the absolute value of the bias. We return MAE as the primary metric.
    absolute_bias = np.mean(np.abs(ate_array - ground_truth))

    # Calculate RMSE
    # RMSE = sqrt( mean( (estimate - truth)^2 ) )
    squared_errors = (ate_array - ground_truth) ** 2
    rmse = np.sqrt(np.mean(squared_errors))

    return {
        'absolute_bias': float(absolute_bias),
        'rmse': float(rmse),
        'mean_estimate': float(np.mean(ate_array)),
        'count': int(len(ate_array))
    }

def run_statistical_test(bias_matrix: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform statistical testing on the bias matrix to determine if there are significant
    differences between imputation methods.

    Implements the FR-006 decision tree:
    1. Run Shapiro-Wilk test on bias distribution.
    2. If p < 0.05 (non-normal) → Use Friedman Test.
    3. If p >= 0.05 (normal) → Use Repeated-Measures ANOVA.
    4. Conditionally: If skewness > 1 OR < -1 → Compute Bootstrap CIs for the difference
       in medians between the best and worst performing methods.

    Args:
        bias_matrix: A DataFrame with columns ['method', 'bias'].
                     Each row represents a bias measurement for a specific method.
                     Expected to have multiple rows per method (repeated measures).

    Returns:
        A dictionary containing:
            - 'p_value': The p-value from the statistical test.
            - 'test_type': The type of test used ('Friedman' or 'ANOVA').
            - 'conclusion': A string describing the conclusion (significant or not).
            - 'bootstrap_ci_diff': (Optional) The bootstrap CI for median difference if skewness condition met.
    """
    if bias_matrix.empty or 'method' not in bias_matrix.columns or 'bias' not in bias_matrix.columns:
        raise ValueError("bias_matrix must contain 'method' and 'bias' columns.")

    # Aggregate bias by method to get a distribution per method
    # We assume the matrix is in long format: rows are observations, columns include method and bias
    methods = bias_matrix['method'].unique()
    if len(methods) < 2:
        raise ValueError("Need at least 2 methods to compare.")

    # Check normality of the combined bias distribution (or per method? FR-006 says "bias distribution")
    # Interpretation: Check normality of the pooled residuals or the distribution of bias values.
    # A robust interpretation for repeated measures ANOVA assumption is checking residuals,
    # but for a simple decision tree, we check the overall distribution of the 'bias' column.
    all_betas = bias_matrix['bias'].dropna().values
    
    if len(all_betas) < 3:
        # Not enough data for Shapiro
        shapiro_p = 0.0 
    else:
        _, shapiro_p = shapiro(all_betas)

    # Determine test type
    test_type = ""
    p_value = 0.0
    conclusion = ""

    # Prepare data for ANOVA/Friedman
    # We need wide format for these tests: rows = subjects (e.g., beta levels or run IDs), cols = methods
    # Assuming the bias_matrix has a way to identify the "subject" (e.g., a 'run_id' or 'beta' column).
    # If not present, we assume each row is an independent observation and we might not be able to do RM-ANOVA.
    # However, the task implies a "bias_matrix" which usually implies a structured comparison.
    # Let's assume the input has a 'group' or 'run_id' column if it's repeated measures.
    # If not, we treat it as independent groups? No, FR-006 says "Repeated-Measures".
    # We will attempt to pivot. If no unique ID exists, we might need to create one or fail.
    # Let's assume the index or a column 'run_id' exists. If not, we create a synthetic one if unique rows exist.
    
    # Check for a grouping column
    group_col = None
    for col in ['run_id', 'beta', 'seed', 'group']:
        if col in bias_matrix.columns:
            group_col = col
            break
    
    if group_col is None:
        # If no group column, we cannot do Repeated Measures. We fallback to Kruskal-Wallis or ANOVA on independent groups?
        # But the spec says "Repeated-Measures". We will assume the data provided is already grouped or we use the index.
        # Let's try to use the index as the subject if it repeats.
        # For safety, if we can't group, we raise an error or assume independent.
        # Given the strict spec, let's assume the caller ensures a 'run_id' or similar exists.
        # If missing, we raise a clear error.
        raise ValueError("bias_matrix must contain a grouping column (e.g., 'run_id', 'beta') for Repeated-Measures test.")

    # Pivot to wide format: index=group, columns=method, values=bias
    try:
        wide_data = bias_matrix.pivot_table(index=group_col, columns='method', values='bias', aggfunc='mean')
    except Exception as e:
        raise ValueError(f"Could not pivot data for statistical test. Ensure each group has one value per method. Error: {e}")

    # Drop rows with NaN (incomplete subjects)
    wide_data = wide_data.dropna()

    if len(wide_data) < 2:
        raise ValueError("Not enough complete subjects for statistical test.")

    # 1. Normality Check (Shapiro-Wilk on residuals or pooled)
    # Re-using the pooled Shapiro result from above as a proxy for normality of the distribution
    is_normal = shapiro_p >= 0.05

    if not is_normal:
        # Friedman Test
        # Requires arrays for each method
        method_names = wide_data.columns.tolist()
        data_arrays = [wide_data[col].values for col in method_names]
        
        # Friedman test requires at least 3 groups for scipy's friedmanchisquare
        if len(method_names) < 3:
            # If only 2 methods and non-normal, use Wilcoxon signed-rank?
            # Friedman is for >2. For 2, Wilcoxon is appropriate.
            # But spec says "Friedman". We'll try to handle 2 by repeating or just using Wilcoxon.
            # Let's stick to the spec: if <3, we might need to warn or use Wilcoxon.
            # For robustness, if <3, we use Wilcoxon.
            from scipy.stats import wilcoxon
            # Wilcoxon is pairwise. We'll do pairwise and report min p-value?
            # Or just report that Friedman requires >2.
            # Let's assume the spec implies >2 methods. If not, we fallback to Wilcoxon for the pair.
            stat, p_value = wilcoxon(data_arrays[0], data_arrays[1])
            test_type = "Wilcoxon (Fallback for 2 methods)"
        else:
            stat, p_value = friedmanchisquare(*data_arrays)
            test_type = "Friedman"
        
        if p_value < 0.05:
            conclusion = "Significant difference found between methods (p < 0.05)."
        else:
            conclusion = "No significant difference found between methods (p >= 0.05)."

    else:
        # Repeated-Measures ANOVA
        # Using statsmodels
        wide_data_reset = wide_data.reset_index()
        wide_data_long = wide_data_reset.melt(id_vars=[group_col], var_name='method', value_name='bias')
        
        try:
            anova = AnovaRM(wide_data_long, depvar='bias', subject=group_col, within=['method'])
            res = anova.fit()
            # Extract p-value for the 'method' effect
            # The table structure varies by version, usually res.mixed_lm or res.anova_lm
            # In AnovaRM, the result is a DataFrame
            p_value = res.loc['method', 'Pr > F']
            test_type = "Repeated-Measures ANOVA"
            
            if p_value < 0.05:
                conclusion = "Significant difference found between methods (p < 0.05)."
            else:
                conclusion = "No significant difference found between methods (p >= 0.05)."
        except Exception as e:
            # Fallback to standard ANOVA if RM fails (e.g., sphericity issues)
            # Or just raise
            raise RuntimeError(f"Repeated-Measures ANOVA failed: {e}")

    # 4. Conditional Bootstrap CIs if skewness > 1 or < -1
    bootstrap_ci_diff = None
    current_skew = skew(all_betas)
    
    if current_skew > 1 or current_skew < -1:
        # Find best and worst methods based on median bias
        method_medians = wide_data.median()
        best_method = method_medians.idxmin() # Lower bias is better
        worst_method = method_medians.idxmax()
        
        # Extract data for these two methods
        data_best = wide_data[best_method].values
        data_worst = wide_data[worst_method].values
        
        # Calculate difference in medians
        diff_medians = np.median(data_worst) - np.median(data_best) # Positive if worst > best
        
        # Bootstrap CI for the difference
        n_boot = 1000
        boot_diffs = []
        rng = np.random.default_rng(42)
        
        for _ in range(n_boot):
            idx_best = rng.integers(0, len(data_best), len(data_best))
            idx_worst = rng.integers(0, len(data_worst), len(data_worst))
            sample_best = data_best[idx_best]
            sample_worst = data_worst[idx_worst]
            boot_diffs.append(np.median(sample_worst) - np.median(sample_best))
        
        ci_low, ci_high = np.percentile(boot_diffs, [2.5, 97.5])
        bootstrap_ci_diff = {
            "median_difference": float(diff_medians),
            "ci_low": float(ci_low),
            "ci_high": float(ci_high),
            "best_method": best_method,
            "worst_method": worst_method,
            "skewness": float(current_skew)
        }

    result = {
        "p_value": float(p_value),
        "test_type": test_type,
        "conclusion": conclusion,
        "shapiro_p_value": float(shapiro_p),
        "skewness": float(current_skew)
    }
    
    if bootstrap_ci_diff:
        result["bootstrap_ci_diff"] = bootstrap_ci_diff

    return result

def save_statistical_test_results(result: Dict[str, Any], output_path: str) -> None:
    """
    Save the statistical test results to a JSON file.

    Args:
        result: The dictionary returned by run_statistical_test.
        output_path: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)