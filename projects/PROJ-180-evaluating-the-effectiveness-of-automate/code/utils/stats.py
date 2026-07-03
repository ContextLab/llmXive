"""
Statistical utility functions for the llmXive automated science pipeline.

Provides wrappers for:
- Wilcoxon signed-rank tests (scipy.stats)
- Variance Inflation Factor (VIF) calculation (statsmodels)
- Mixed-Effects Linear Models (statsmodels)

All functions are designed to handle real data inputs and return
standard statistical objects or dictionaries suitable for serialization.
"""
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.mixed_linear_model import MixedLM

def wilcoxon_signed_rank(
    group_a: Union[List[float], np.ndarray],
    group_b: Union[List[float], np.ndarray],
    alternative: str = 'two-sided'
) -> Dict[str, float]:
    """
    Perform a Wilcoxon signed-rank test on paired samples.
    
    Args:
        group_a: First set of measurements (paired).
        group_b: Second set of measurements (paired).
        alternative: Defines the alternative hypothesis. 
                     'two-sided', 'less', or 'greater'.
                     
    Returns:
        A dictionary containing:
        - 'statistic': The Wilcoxon W statistic.
        - 'pvalue': The p-value for the test.
        - 'method': 'Wilcoxon Signed-Rank Test'
    """
    if len(group_a) != len(group_b):
        raise ValueError("Groups must be of equal length for paired test.")
    
    if len(group_a) < 2:
        raise ValueError("At least 2 observations are required per group.")
        
    stat, p_val = stats.wilcoxon(
        group_a, 
        group_b, 
        alternative=alternative
    )
    
    return {
        "statistic": float(stat),
        "pvalue": float(p_val),
        "method": "Wilcoxon Signed-Rank Test"
    }

def calculate_vif(
    df: pd.DataFrame,
    feature_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factors (VIF) for a set of features.
    
    Args:
        df: DataFrame containing the features.
        feature_columns: List of column names to calculate VIF for.
                         If None, uses all numeric columns.
                         
    Returns:
        A DataFrame with columns 'feature' and 'VIF'.
    """
    if feature_columns is None:
        feature_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
    if not feature_columns:
        raise ValueError("No numeric features found to calculate VIF.")
        
    X = df[feature_columns]
    
    # Handle potential constant columns or NaNs
    if X.isnull().any().any():
        raise ValueError("Data contains NaN values. Impute or drop before VIF calculation.")
        
    vif_data = []
    for col in feature_columns:
        # VIF calculation requires an intercept column added by statsmodels usually,
        # but for VIF specifically, we regress X_i on all other X_j.
        # The standard formula: VIF = 1 / (1 - R^2)
        # We use the VIF function from statsmodels which handles the regression internally.
        # Note: statsmodels variance_inflation_factor expects an array with an intercept column
        # if we were doing the full model, but for pairwise VIF, we pass the design matrix.
        # Actually, the standard usage for VIF in statsmodels is:
        # vif = variance_inflation_factor(X_with_intercept, i)
        # But to get VIF for each feature, we iterate.
        
        # To calculate VIF for column 'col', we regress 'col' on all other columns.
        # The variance_inflation_factor function in statsmodels takes the full matrix 
        # and the index of the column. It automatically includes an intercept if the 
        # matrix has one column that is all 1s, but typically we pass the matrix without
        # an explicit intercept column and the function calculates it relative to the others.
        # However, the standard implementation in statsmodels docs suggests adding an intercept
        # column to the matrix if we want the VIF relative to the full model including intercept.
        # For collinearity diagnostics among predictors, we usually add a constant.
        
        # Let's construct the design matrix with a constant for the regression context,
        # but the VIF function calculates the VIF for the specific column index.
        # If we want VIF for 'col', we need the index of 'col' in the matrix passed.
        
        # Simpler approach: Use the function directly on the subset of features.
        # We must include a constant column for the regression to be valid, 
        # but the VIF for the constant is not of interest.
        
        # We will calculate VIF for each column in feature_columns.
        # We construct X with a constant.
        X_with_const = sm.add_constant(X)
        
        # Find the index of the current column in X_with_const
        # The constant is at index 0. Features start at 1.
        try:
            col_idx = feature_columns.index(col) + 1
            vif = variance_inflation_factor(X_with_const.values, col_idx)
            vif_data.append({"feature": col, "VIF": vif})
        except Exception as e:
            # If a column is constant or singular, VIF might be infinite or error
            vif_data.append({"feature": col, "VIF": float('inf')})
    
    return pd.DataFrame(vif_data)

def fit_mixed_effects_model(
    df: pd.DataFrame,
    endog: str,
    exog: List[str],
    groups: str,
    use_ridge: bool = False,
    ridge_alpha: float = 1.0
) -> Dict[str, Any]:
    """
    Fit a Linear Mixed-Effects Model (LMM).
    
    Args:
        df: DataFrame containing the data.
        endog: Name of the dependent variable column.
        exog: List of names of independent variable columns.
        groups: Name of the column containing group identifiers (random effects).
        use_ridge: If True, attempts to use Ridge regression if VIF is high.
                   Note: statsmodels MixedLM does not natively support Ridge.
                   This flag currently triggers a check and fallback to a warning
                   or a standard fit, as Ridge for LMM is not standard in statsmodels.
                   For this implementation, we perform the standard LMM fit.
        ridge_alpha: Alpha parameter for Ridge (unused in standard statsmodels MixedLM).
                     
    Returns:
        A dictionary containing:
        - 'summary': String representation of the model summary.
        - 'coefficients': Dictionary of fixed effects coefficients.
        - 'std_errors': Dictionary of standard errors for fixed effects.
        - 'pvalues': Dictionary of p-values for fixed effects.
        - 'log_likelihood': Model log-likelihood.
    """
    # Prepare data
    if endog not in df.columns or groups not in df.columns:
        raise ValueError("Endog or groups column not found in DataFrame.")
        
    for col in exog:
        if col not in df.columns:
            raise ValueError(f"Exog column '{col}' not found in DataFrame.")
            
    # Check for NaNs in relevant columns
    cols_to_check = [endog] + exog + [groups]
    if df[cols_to_check].isnull().any().any():
        # Drop rows with NaNs in these columns
        df_clean = df[cols_to_check].dropna()
    else:
        df_clean = df
        
    if len(df_clean) < 2:
        raise ValueError("Insufficient data after cleaning to fit mixed effects model.")
        
    if df_clean[groups].nunique() < 2:
        raise ValueError("Need at least 2 groups to fit random effects.")
        
    endog_data = df_clean[endog]
    exog_data = df_clean[exog]
    groups_data = df_clean[groups]
    
    # Fit the model
    # MixedLM requires the formula style or explicit design matrices.
    # Using explicit design matrices:
    # We do not add a constant here; MixedLM adds it by default if not specified otherwise?
    # Actually, MixedLM does not automatically add a constant. We should add one if we want an intercept.
    exog_with_const = sm.add_constant(exog_data)
    
    try:
        model = MixedLM(endog_data, exog_with_const, groups=groups_data)
        result = model.fit()
    except Exception as e:
        raise RuntimeError(f"Failed to fit MixedLM: {e}")
        
    # Extract results
    fixed_effects = result.fe_params
    std_errors = result.bse
    p_values = result.pvalues
    
    # Format p-values (handle inf/NaN)
    p_values_clean = {}
    for k, v in p_values.items():
        if np.isinf(v) or np.isnan(v):
            p_values_clean[k] = None
        else:
            p_values_clean[k] = float(v)
    
    return {
        "summary": str(result.summary()),
        "coefficients": {str(k): float(v) for k, v in fixed_effects.items()},
        "std_errors": {str(k): float(v) for k, v in std_errors.items()},
        "pvalues": p_values_clean,
        "log_likelihood": float(result.llf),
        "model": result # Return the result object for further inspection if needed
    }

def main():
    """
    Entry point for testing the stats module.
    This function runs a simple self-test to ensure imports and basic logic work.
    """
    print("Running stats module self-test...")
    
    # Test Wilcoxon
    data_a = [1, 2, 3, 4, 5]
    data_b = [1, 2, 4, 5, 6]
    w_result = wilcoxon_signed_rank(data_a, data_b)
    print(f"Wilcoxon Test: {w_result}")
    
    # Test VIF
    df_vif = pd.DataFrame({
        'x1': [1, 2, 3, 4, 5],
        'x2': [2, 4, 6, 8, 10], # Perfectly correlated
        'x3': [1, 3, 5, 7, 9]
    })
    try:
        vif_result = calculate_vif(df_vif)
        print(f"VIF Calculation:\n{vif_result}")
    except Exception as e:
        print(f"VIF Test (expected potential singular matrix issues): {e}")
        
    # Test Mixed Effects
    df_mixed = pd.DataFrame({
        'y': [1, 2, 3, 4, 5, 6, 7, 8],
        'x1': [1, 1, 2, 2, 3, 3, 4, 4],
        'x2': [1, 2, 1, 2, 1, 2, 1, 2],
        'group': ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B']
    })
    try:
        mixed_result = fit_mixed_effects_model(df_mixed, 'y', ['x1', 'x2'], 'group')
        print(f"Mixed Effects Model Log-Likelihood: {mixed_result['log_likelihood']}")
    except Exception as e:
        print(f"Mixed Effects Test: {e}")
        
    print("Self-test completed.")

if __name__ == "__main__":
    main()