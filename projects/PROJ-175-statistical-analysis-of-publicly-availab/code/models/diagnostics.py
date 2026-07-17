import json
import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from scipy.stats import chi2

# Ensure project root is in path for relative imports if run as script
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def load_processed_data(data_path: str = "data/processed/merged_dataset.csv") -> pd.DataFrame:
    """
    Load the processed dataset containing features and labels.
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found at {data_path}. "
                                "Ensure T018 (preprocessing) has been completed.")
    return pd.read_csv(path)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factors (VIF) for a list of features.
    
    Args:
        df: DataFrame containing the features.
        features: List of column names to calculate VIF for.
        
    Returns:
        DataFrame with feature names and their VIF scores.
    """
    # Filter to only requested features and drop rows with NaN
    subset = df[features].dropna()
    if subset.empty:
        return pd.DataFrame(columns=["feature", "vif"])

    # Add constant for intercept
    X = add_constant(subset)
    
    vif_data = []
    for i, col in enumerate(features):
        # VIF calculation: 1 / (1 - R^2) where R^2 is from regressing col on others
        # statsmodels vif function handles the constant automatically if present
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data.append({"feature": col, "vif": vif})
        except Exception:
            vif_data.append({"feature": col, "vif": np.nan})
    
    return pd.DataFrame(vif_data)

def drop_high_vif_predictors(df: pd.DataFrame, threshold: float = 5.0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Iteratively drop predictors with VIF > threshold until all remaining are below threshold.
    
    Args:
        df: DataFrame with features.
        threshold: Maximum allowed VIF.
        
    Returns:
        Tuple of (DataFrame with safe features, list of dropped feature names)
    """
    # Identify candidate features (exclude target and ID columns if present)
    # Assuming 'compatibility_label' is the target and we want to check all others
    # We need to know which columns are predictors. 
    # Based on T018, predictors include: log_freq, flavor_similarity, functional_role (categorical/numeric), etc.
    # We will assume the input df has a 'target' column or we pass specific feature names.
    # For this function, we assume the caller passes the full df and we filter out known non-features.
    
    potential_features = [c for c in df.columns if c not in ['compatibility_label', 'recipe_id', 'ingredient_id']]
    
    current_features = potential_features.copy()
    dropped = []
    
    # Safety break to prevent infinite loops
    max_iterations = len(current_features) + 1
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        if len(current_features) <= 1:
            break
            
        vif_df = calculate_vif(df, current_features)
        max_vif_row = vif_df.loc[vif_df['vif'].idxmax()]
        
        if pd.isna(max_vif_row['vif']) or max_vif_row['vif'] <= threshold:
            break
        
        # Drop the feature with highest VIF
        worst_feature = max_vif_row['feature']
        dropped.append(worst_feature)
        current_features.remove(worst_feature)
        
    return df[current_features], dropped

def perform_likelihood_ratio_test(y: np.ndarray, log_likelihood_null: float, 
                                  log_likelihood_full: float, df_diff: int) -> Dict:
    """
    Perform Likelihood-Ratio Test comparing Null vs Full model.
    
    Args:
        y: Target array (unused in calculation but kept for signature consistency).
        log_likelihood_null: Log-likelihood of the Null model.
        log_likelihood_full: Log-likelihood of the Full model.
        df_diff: Difference in degrees of freedom (number of added parameters).
        
    Returns:
        Dictionary with test statistic and p-value.
    """
    stat = 2 * (log_likelihood_full - log_likelihood_null)
    p_value = 1 - chi2.cdf(stat, df_diff)
    
    return {
        "statistic": float(stat),
        "p_value": float(p_value),
        "df_diff": df_diff,
        "log_likelihood_null": float(log_likelihood_null),
        "log_likelihood_full": float(log_likelihood_full)
    }

def post_hoc_power_validation(sample_size: int, effect_size: float = 0.1, alpha: float = 0.05) -> Dict:
    """
    Validate achieved power given sample size and effect size.
    """
    from statsmodels.stats.power import GofChisquarePower
    power_analysis = GofChisquarePower()
    # Approximate power for logistic regression using chi-square approximation
    try:
        power = power_analysis.solve_power(effect_size=effect_size, 
                                           nobs=sample_size, 
                                           alpha=alpha, 
                                           power=None)
        return {"power": power, "sample_size": sample_size, "effect_size": effect_size}
    except Exception:
        return {"power": None, "sample_size": sample_size, "effect_size": effect_size, "error": "Calculation failed"}

def resolve_multicollinearity_and_retest(data_path: str = "data/processed/merged_dataset.csv",
                                         target_col: str = "compatibility_label",
                                         vif_threshold: float = 5.0,
                                         output_lrt_path: str = "data/lrt_result_vif_corrected.json",
                                         output_model_comparison_path: str = "data/model_comparison.json") -> Dict:
    """
    T043 Implementation: Multicollinearity Resolution.
    
    1. Loads processed data.
    2. Checks VIF for 'Functional Role' (and other predictors).
    3. If VIF > 5 for 'Functional Role', drops it and re-runs LRT.
    4. Saves results to specified JSON files.
    
    This function assumes that the necessary models (Null and Full) have been fit 
    on the original data and that we need to re-evaluate the LRT after feature removal.
    Since we cannot re-fit models here without the full pipeline context, we assume
    the 'Full Model' here refers to the model trained on the reduced feature set.
    
    To make this robust, we will:
    - Load the data.
    - Identify 'Functional Role' (likely 'functional_role' or similar).
    - Calculate VIF.
    - If 'Functional Role' is dropped, we simulate the LRT result update by:
      a. Noting the drop.
      b. Saving the VIF corrected results.
    
    Note: In a real pipeline, we would re-fit the logistic model on the reduced features.
    For this task, we assume the existence of a mechanism to get the new log-likelihood
    or we re-fit a simple OLS/Logistic proxy if needed. 
    However, the task specifically asks to "re-run the Likelihood-Ratio Test".
    We will implement a helper to re-fit a logistic model on the reduced set using statsmodels
    to get the accurate log-likelihood for the LRT.
    """
    import statsmodels.api as sm
    from sklearn.linear_model import LogisticRegression
    
    # 1. Load Data
    df = load_processed_data(data_path)
    
    # Identify predictors. We assume standard columns from T018/T019
    # Columns: log_freq, flavor_similarity, functional_role (might be numeric or encoded)
    # We need to handle categorical 'functional_role' if it exists.
    # For VIF, we need numeric columns.
    
    # Let's assume the processed data has numeric columns for these.
    # If 'functional_role' is categorical, we might need dummy encoding, but VIF is usually on numeric.
    # We will look for a numeric column named 'functional_role' or similar.
    
    potential_predictors = [c for c in df.columns if c not in [target_col, 'recipe_id', 'ingredient_id', 'id']]
    
    # Ensure we have numeric data
    numeric_df = df[potential_predictors].select_dtypes(include=[np.number])
    
    if 'functional_role' not in numeric_df.columns:
        # Try to find a column that might represent it
        role_cols = [c for c in numeric_df.columns if 'role' in c.lower()]
        if role_cols:
            role_col = role_cols[0]
        else:
            role_col = None
    else:
        role_col = 'functional_role'
    
    # 2. Calculate VIF
    vif_df = calculate_vif(numeric_df, numeric_df.columns.tolist())
    
    dropped_predictors = []
    final_features = numeric_df.columns.tolist()
    
    # Check if 'Functional Role' (or equivalent) has VIF > 5
    if role_col:
        role_vif = vif_df[vif_df['feature'] == role_col]['vif'].values
        if len(role_vif) > 0 and role_vif[0] > vif_threshold:
            # Drop it
            final_features.remove(role_col)
            dropped_predictors.append(role_col)
            # Re-calculate VIF for remaining if we want to be thorough, but task focuses on this one
            # We proceed with reduced set
    
    # 3. Re-run Likelihood Ratio Test on Reduced Set
    # We need to fit Null and Full models on the REDUCED feature set to get log-likelihoods.
    
    y = df[target_col].values
    
    # Prepare features for reduced set
    X_reduced = numeric_df[final_features].dropna()
    y_reduced = y[:len(X_reduced)]
    
    if len(X_reduced) < 10:
        raise ValueError("Not enough data points after dropping predictors to fit models.")
        
    X_const = sm.add_constant(X_reduced)
    
    # Fit Null Model (Intercept only)
    # Null model usually uses only frequency (log_freq) as per T022 description "Null Model (frequency only)"
    # But if we dropped frequency? Unlikely. Assuming log_freq is in final_features.
    # If we dropped log_freq, Null might be intercept only?
    # Let's assume Null is intercept only for simplicity of LRT, or we re-define Null as frequency only.
    # T022 says: "Null Model (frequency only)".
    # If 'log_freq' is in final_features:
    
    null_features = ['log_freq'] if 'log_freq' in final_features else ['const']
    if 'const' in null_features and len(X_const.columns) > 1:
       # Remove const from null_features if we use intercept in model
       pass
    
    # Fit Null (Frequency only)
    if 'log_freq' in final_features:
        X_null = sm.add_constant(numeric_df[['log_freq']].dropna())
        y_null = y[:len(X_null)]
        null_model = sm.Logit(y_null, X_null).fit(disp=0)
        ll_null = null_model.llf
    else:
        # Fallback: Intercept only
        X_null = sm.add_constant(pd.Series([1]*len(y_reduced)))
        null_model = sm.Logit(y_reduced, X_null).fit(disp=0)
        ll_null = null_model.llf
        
    # Fit Full Model (Reduced set)
    full_model = sm.Logit(y_reduced, X_const).fit(disp=0)
    ll_full = full_model.llf
    
    # Calculate LRT
    df_diff = len(final_features) - len(null_features)
    if df_diff < 0: df_diff = 1 # Fallback
    
    lrt_result = perform_likelihood_ratio_test(y_reduced, ll_null, ll_full, df_diff)
    lrt_result['dropped_predictors'] = dropped_predictors
    lrt_result['final_features_used'] = final_features
    
    # 4. Save Results
    Path(output_lrt_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_lrt_path, 'w') as f:
        json.dump(lrt_result, f, indent=2)
    
    # Update model_comparison.json
    # Load existing if exists, else create
    comparison_data = {}
    if Path(output_model_comparison_path).exists():
        with open(output_model_comparison_path, 'r') as f:
            comparison_data = json.load(f)
    
    # Update with new VIF-corrected results
    comparison_data['vif_corrected_lrt'] = lrt_result
    comparison_data['dropped_predictors'] = dropped_predictors
    
    with open(output_model_comparison_path, 'w') as f:
        json.dump(comparison_data, f, indent=2)
        
    return {
        "status": "success",
        "dropped": dropped_predictors,
        "lrt_p_value": lrt_result['p_value'],
        "output_lrt_path": output_lrt_path,
        "output_comparison_path": output_model_comparison_path
    }

def main():
    """
    Main entry point for T043: Multicollinearity Resolution.
    """
    print("Starting T043: Multicollinearity Resolution...")
    try:
        result = resolve_multicollinearity_and_retest()
        print(f"Completed successfully. Dropped predictors: {result['dropped']}")
        print(f"Results saved to {result['output_lrt_path']}")
    except Exception as e:
        print(f"Failed: {e}")
        raise

if __name__ == "__main__":
    main()
