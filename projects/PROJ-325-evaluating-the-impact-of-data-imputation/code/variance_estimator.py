import logging
import sys
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
from statsmodels.stats.sandwich_covariance import cov_hc0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def estimate_taylor_variance(
    data: pd.DataFrame,
    variable: str,
    weight_col: str = 'weight',
    psu_col: str = 'psu',
    strata_col: str = 'strata'
) -> Dict[str, Any]:
    """
    Estimate variance using Taylor series linearization for a single variable.
    
    This function implements design-based variance estimation. It strictly checks
    for the presence of design columns (weight, psu, strata). If 'psu' or 'strata'
    are missing, it ABORTS and returns an error status as per T009 requirements.
    
    It also implements robust error handling for small cluster sizes (PSU=1) as per T017/T009b:
    - Detects clusters where PSU size = 1.
    - Issues a warning.
    - Flags the variance as "potentially unstable".
    - Proceeds with calculation but includes a flag in the result.
    
    Args:
        data: DataFrame containing the variable and design columns.
        variable: Name of the variable to estimate variance for.
        weight_col: Name of the weight column.
        psu_col: Name of the PSU (cluster) column.
        strata_col: Name of the strata column.
        
    Returns:
        Dictionary with keys: 'mean', 'variance', 'status', 'design_type', 
        'psu_singleton_warning', 'error_message' (if any).
    """
    result = {
        'variable': variable,
        'mean': None,
        'variance': None,
        'status': 'pending',
        'design_type': 'taylor_linearization',
        'psu_singleton_warning': False,
        'error_message': None
    }

    # 1. Verify required columns exist (T009 requirement)
    required_cols = [variable, weight_col, psu_col, strata_col]
    missing_cols = [col for col in required_cols if col not in data.columns]
    
    if missing_cols:
        error_msg = f"Missing required design columns: {missing_cols}. Aborting analysis for {variable}."
        logger.error(error_msg)
        result['status'] = 'aborted'
        result['error_message'] = error_msg
        return result

    # 2. Handle missing values in the variable of interest (Complete Case for this variable)
    valid_data = data[[variable, weight_col, psu_col, strata_col]].dropna(subset=[variable])
    
    if len(valid_data) == 0:
        error_msg = f"No valid data points for variable {variable} after dropping NaNs."
        logger.error(error_msg)
        result['status'] = 'aborted'
        result['error_message'] = error_msg
        return result

    # 3. Check for small cluster sizes (PSU=1) - T017 / T009b Logic
    # Group by strata and PSU to count cluster sizes
    # We need to ensure we have enough PSUs within strata to estimate variance
    valid_data['psu_size'] = valid_data.groupby([strata_col, psu_col])[variable].transform('count')
    
    singleton_psus = valid_data[valid_data['psu_size'] == 1]
    
    if len(singleton_psus) > 0:
        num_singletons = singleton_psus[psu_col].nunique()
        warning_msg = (
            f"Detected {num_singletons} PSU(s) with cluster size = 1 in variable '{variable}'. "
            "Variance estimates for these clusters are potentially unstable. "
            "Proceeding with calculation but flagging result."
        )
        logger.warning(warning_msg)
        result['psu_singleton_warning'] = True
        # Note: We do not abort here per T009b (T009b says "issue a warning and flag... but do not abort")
        # However, if ALL PSUs are singletons, variance calculation might fail mathematically.
        # We proceed and let the math handle it, but the flag is set.

    # 4. Calculate Mean (Weighted)
    weights = valid_data[weight_col]
    values = valid_data[variable]
    
    w_sum = weights.sum()
    mean_est = (weights * values).sum() / w_sum
    result['mean'] = float(mean_est)

    # 5. Calculate Variance using Taylor Linearization (Sandwich Estimator approach)
    # For complex survey data, we often use the sandwich estimator (HC0) on the residuals
    # adjusted for weights, or a specific Taylor linearization formula.
    # Given the use of statsmodels cov_hc0, we adapt the data to fit the model interface.
    # We treat the variable as the dependent variable and include a constant.
    # The robust covariance matrix provides the variance of the intercept (which is the mean).
    
    try:
        # Prepare design matrix X (just a constant for mean estimation)
        X = np.ones((len(valid_data), 1))
        y = values.values
        
        # statsmodels cov_hc0 expects residuals and design matrix.
        # Residuals = y - y_hat (where y_hat is the weighted mean? No, OLS assumes unweighted mean for intercept)
        # To get weighted mean via OLS, we need weighted least squares or replicate weights.
        # However, a common approximation for Taylor linearization in this context 
        # is using the sandwich estimator on the weighted residuals or using the 'svy' logic.
        # Since we are using cov_hc0 directly:
        # We will compute the residuals from the weighted mean manually to be precise,
        # then use the sandwich formula structure: (X'WX)^-1 X'W e e' W X (X'WX)^-1
        # But cov_hc0 computes (X'X)^-1 X' diag(e^2) X (X'X)^-1.
        
        # Let's implement the specific Taylor Linearization for a mean with weights/strata/PSU manually
        # to ensure correctness, as generic HC0 might not respect the strata/PSU structure without grouping.
        
        # Correct Taylor Linearization for Mean with Strata/PSU:
        # Variance = sum_over_strata ( sum_over_psu_in_strata ( (sum_w_in_psu * (y_bar_psu - y_bar_strata))^2 ) )
        # This is the standard formula for stratified cluster sampling.
        
        # Step 5a: Calculate strata totals and means
        strata_groups = valid_data.groupby(strata_col)
        total_weight_strata = strata_groups[weight_col].sum()
        weighted_sum_strata = strata_groups.apply(lambda g: (g[weight_col] * g[variable]).sum())
        mean_strata = weighted_sum_strata / total_weight_strata
        
        total_var = 0.0
        num_strata = 0
        
        for stratum, group in strata_groups:
            num_strata += 1
            w_s = group[weight_col].sum()
            y_bar_s = mean_strata[stratum]
            
            psu_groups = group.groupby(psu_col)
            psu_contribution = 0.0
            
            for psu, p_group in psu_groups:
                w_p = p_group[weight_col].sum()
                y_bar_p = (p_group[weight_col] * p_group[variable]).sum() / w_p
                # Contribution of this PSU to the stratum total
                # The term is (w_p * (y_bar_p - y_bar_s))
                # Actually, the linearized variable for the mean is (y_i - mu)
                # The estimator for the variance of the mean is (1/N^2) * sum_{h} (1 - f_h) * sum_{j} (sum_{k in j} e_k)^2
                # Assuming f_h is negligible or handled by weights.
                # Simplified Taylor: Var(mu) = (1 / W_total^2) * sum_h sum_j ( w_j * (y_bar_j - y_bar_h) )^2
                # where w_j is total weight in PSU j.
                
                # Wait, the standard formula for the variance of the estimated total is:
                # Var(T) = sum_h (1 - f_h) * (N_h^2 / n_h) * s_h^2 ...
                # For mean: Var(y_bar) = (1 / W^2) * sum_h sum_j ( w_j * (y_bar_j - y_bar_h) )^2
                # This is the most robust "design-based" approach given the columns.
                
                diff = y_bar_p - y_bar_s
                psu_contribution += (w_p * diff) ** 2
            
            total_var += psu_contribution
        
        # Normalize by total weight squared
        final_variance = total_var / (w_sum ** 2)
        
        result['variance'] = float(final_variance)
        result['status'] = 'success'
        
        if result['psu_singleton_warning']:
            result['status'] = 'success_with_warning'

    except Exception as e:
        error_msg = f"Error calculating Taylor variance for {variable}: {str(e)}"
        logger.error(error_msg)
        result['status'] = 'error'
        result['error_message'] = error_msg

    return result

def estimate_variance_for_multiple_variables(
    data: pd.DataFrame,
    variables: List[str],
    weight_col: str = 'weight',
    psu_col: str = 'psu',
    strata_col: str = 'strata'
) -> List[Dict[str, Any]]:
    """
    Estimate variance for multiple variables using Taylor series linearization.
    
    Args:
        data: DataFrame with data.
        variables: List of variable names to estimate variance for.
        weight_col: Weight column name.
        psu_col: PSU column name.
        strata_col: Strata column name.
        
    Returns:
        List of result dictionaries, one per variable.
    """
    results = []
    for var in variables:
        res = estimate_taylor_variance(
            data, var, weight_col, psu_col, strata_col
        )
        results.append(res)
    return results

def main():
    """
    Main entry point for variance estimation script.
    Expects data to be loaded from data/raw/gss_2018_subset.csv (or similar).
    Outputs results to data/processed/variance_results.json.
    """
    import json
    from pathlib import Path

    # Configuration
    input_path = Path("data/raw/gss_2018_subset.csv")
    output_path = Path("data/processed/variance_results.json")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Please run data_ingestion first.")
        sys.exit(1)

    # Load Data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Select variables for analysis (example: 'hrs1', 'age')
    # In a real scenario, this might be configurable or scan all numeric columns
    # excluding design columns
    design_cols = ['weight', 'psu', 'strata']
    target_vars = [col for col in df.columns if col not in design_cols and df[col].dtype in ['int64', 'float64']]
    
    if not target_vars:
        logger.warning("No numeric target variables found.")
        sys.exit(0)

    # Limit to first 5 for demonstration if too many, or process all
    # For this task, we process all found numeric variables
    logger.info(f"Estimating variance for variables: {target_vars}")
    
    results = estimate_variance_for_multiple_variables(
        df, 
        target_vars,
        weight_col='weight',
        psu_col='psu',
        strata_col='strata'
    )
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Variance estimation complete. Results saved to {output_path}")
    
    # Print summary
    for res in results:
        status = res['status']
        var_name = res['variable']
        mean = res['mean']
        var = res['variance']
        warning = " [WARNING: PSU=1 detected]" if res['psu_singleton_warning'] else ""
        print(f"{var_name}: Mean={mean:.4f}, Variance={var:.4f} (Status: {status}){warning}")

if __name__ == "__main__":
    main()