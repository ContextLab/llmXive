import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols

from config.environment import get_local_paths

logger = logging.getLogger(__name__)

def load_processed_dataset():
    """Load the processed dataset from the previous stage."""
    paths = get_local_paths()
    input_path = paths['processed_dataset']
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Processed dataset not found at {input_path}. "
                              "Run T018/T020 first to generate the dataset.")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded dataset with {len(df)} samples from {input_path}")
    
    # Ensure required columns exist
    required_cols = ['sample_id', 'age', 'burden', 'depth_stratified_burden', 
                   'sex', 'PC1', 'PC2', 'depth']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")
    
    return df

def calculate_unadjusted_spearman(df):
    """Calculate unadjusted Spearman rank correlation between age and burden."""
    # Use the primary burden metric (total burden) as per T015
    # Filter out any rows with missing values in age or burden
    valid_df = df[['age', 'burden']].dropna()
    
    if len(valid_df) < 2:
        logger.warning("Not enough valid samples for Spearman correlation")
        return pd.DataFrame(columns=['variable', 'correlation', 'p_value', 'n_samples'])
    
    corr, p_value = stats.spearmanr(valid_df['age'], valid_df['burden'])
    
    results = pd.DataFrame([{
        'variable': 'burden_vs_age',
        'correlation': corr,
        'p_value': p_value,
        'n_samples': len(valid_df)
    }])
    
    logger.info(f"Spearman correlation: r={corr:.4f}, p={p_value:.4f}, n={len(valid_df)}")
    return results

def calculate_rank_ols(df):
    """
    Implement Rank-OLS regression as per plan.md Decision Log.
    
    Rank-transform all continuous variables (age, burden, depth, PC1, PC2)
    then fit: rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)
    
    Uses the depth-stratified burden from T016 as the primary burden metric.
    """
    # Create a working copy
    model_df = df.copy()
    
    # Filter out rows with missing values in any required column
    required_cols = ['age', 'burden', 'depth_stratified_burden', 'sex', 'PC1', 'PC2', 'depth']
    model_df = model_df.dropna(subset=required_cols)
    
    if len(model_df) < 10:
        logger.error("Not enough samples for Rank-OLS regression after dropping NA")
        return pd.DataFrame()
    
    # Rank-transform continuous variables
    # Note: We rank age, burden, depth, PC1, PC2 as specified
    # sex is kept as categorical (will be encoded by statsmodels)
    
    rank_cols = ['age', 'depth', 'PC1', 'PC2', 'burden']
    for col in rank_cols:
        # Use method='average' for handling ties
        model_df[f'rank_{col}'] = model_df[col].rank(method='average')
    
    # Prepare the formula
    # rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)
    # Note: We use the original PC1/PC2 (not ranked) as they are already continuous covariates
    # But the task says "Rank-transform all continuous variables (age, burden, depth, PC1, PC2)"
    # So we should rank PC1 and PC2 as well
    
    formula = "rank_age ~ rank_burden + C(sex) + rank_PC1 + rank_PC2 + rank_depth"
    
    # Fit the model
    model = ols(formula, data=model_df).fit()
    
    # Extract results
    results_list = []
    for param_name, param in model.params.items():
        results_list.append({
            'variable': param_name,
            'coefficient': param,
            'std_error': model.bse[param_name],
            't_statistic': model.tvalues[param_name],
            'p_value': model.pvalues[param_name]
        })
    
    results_df = pd.DataFrame(results_list)
    results_df['adjusted_p_value'] = np.nan  # Will be filled by apply_benjamini_hochberg
    
    # Log key findings
    burden_idx = results_df[results_df['variable'] == 'rank_burden'].index
    if len(burden_idx) > 0:
        burden_coef = results_df.loc[burden_idx[0], 'coefficient']
        burden_p = results_df.loc[burden_idx[0], 'p_value']
        logger.info(f"Rank-OLS: burden coefficient = {burden_coef:.6f}, p = {burden_p:.6f}")
    
    return results_df

def apply_benjamini_hochberg(results_df):
    """
    Apply Benjamini-Hochberg correction to p-values.
    
    Modifies the input dataframe in-place and returns it.
    """
    if len(results_df) == 0:
        return results_df
    
    # Get p-values
    p_values = results_df['p_value'].values
    
    # Sort indices by p-value
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    n = len(sorted_p_values)
    
    # Calculate adjusted p-values
    adjusted_p_values = np.zeros(n)
    for i in range(n):
        # BH correction: p_adj = p * n / rank
        # But we need to ensure monotonicity (non-decreasing as rank increases)
        rank = i + 1
        adjusted = sorted_p_values[i] * n / rank
        adjusted_p_values[i] = adjusted
    
    # Enforce monotonicity: work backwards to ensure p_adj[i] <= p_adj[i+1]
    for i in range(n-2, -1, -1):
        adjusted_p_values[i] = min(adjusted_p_values[i], adjusted_p_values[i+1])
    
    # Clip to [0, 1]
    adjusted_p_values = np.clip(adjusted_p_values, 0, 1)
    
    # Assign back to dataframe in original order
    results_df['adjusted_p_value'] = 0.0
    results_df.loc[sorted_indices, 'adjusted_p_value'] = adjusted_p_values
    
    logger.info(f"Applied Benjamini-Hochberg correction to {n} p-values")
    return results_df

def record_secondary_ols_model(df, spearman_results, rank_ols_results):
    """
    Record coefficients and p-values for the secondary OLS model
    and calculate the delta between Spearman and OLS coefficients.
    """
    # This is a secondary model (standard OLS without ranking)
    # We'll create a simple OLS: age ~ burden + sex + PC1 + PC2 + depth
    model_df = df.dropna(subset=['age', 'burden', 'sex', 'PC1', 'PC2', 'depth'])
    
    if len(model_df) < 10:
        logger.warning("Not enough samples for secondary OLS model")
        return pd.DataFrame()
    
    formula = "age ~ burden + C(sex) + PC1 + PC2 + depth"
    model = ols(formula, data=model_df).fit()
    
    results_list = []
    for param_name, param in model.params.items():
        results_list.append({
            'variable': param_name,
            'coefficient': param,
            'std_error': model.bse[param_name],
            't_statistic': model.tvalues[param_name],
            'p_value': model.pvalues[param_name],
            'model_type': 'secondary_ols'
        })
    
    secondary_results = pd.DataFrame(results_list)
    
    # Calculate delta between Spearman and Rank-OLS for burden
    spearman_burden = spearman_results[spearman_results['variable'] == 'burden_vs_age']['correlation'].values
    rank_ols_burden = rank_ols_results[rank_ols_results['variable'] == 'rank_burden']['coefficient'].values
    
    if len(spearman_burden) > 0 and len(rank_ols_burden) > 0:
        delta = abs(spearman_burden[0] - rank_ols_burden[0])
        logger.info(f"Delta between Spearman and Rank-OLS burden coefficients: {delta:.6f}")
    else:
        delta = np.nan
        logger.warning("Could not calculate delta between models")
    
    return secondary_results

def main():
    """Main entry point for statistical modeling."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    paths = get_local_paths()
    
    try:
        # Load processed dataset
        df = load_processed_dataset()
        
        # 1. Calculate unadjusted Spearman correlation
        spearman_results = calculate_unadjusted_spearman(df)
        spearman_path = paths['spearman_results']
        spearman_results.to_csv(spearman_path, index=False)
        logger.info(f"Saved Spearman results to {spearman_path}")
        
        # 2. Calculate Rank-OLS regression
        rank_ols_results = calculate_rank_ols(df)
        
        if len(rank_ols_results) == 0:
            logger.error("Rank-OLS failed to produce results")
            return 1
        
        # 3. Apply Benjamini-Hochberg correction
        rank_ols_results = apply_benjamini_hochberg(rank_ols_results)
        
        # 4. Save Rank-OLS results
        rank_ols_path = paths['rank_ols_results']
        rank_ols_results.to_csv(rank_ols_path, index=False)
        logger.info(f"Saved Rank-OLS results to {rank_ols_path}")
        
        # 5. Record secondary OLS model
        secondary_results = record_secondary_ols_model(df, spearman_results, rank_ols_results)
        if len(secondary_results) > 0:
            secondary_path = paths['secondary_ols_results']
            secondary_results.to_csv(secondary_path, index=False)
            logger.info(f"Saved secondary OLS results to {secondary_path}")
        
        logger.info("Statistical modeling completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Statistical modeling failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
