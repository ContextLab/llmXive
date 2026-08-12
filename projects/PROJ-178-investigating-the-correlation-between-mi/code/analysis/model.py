import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.formula.api as smf

from config.environment import get_local_paths

logger = logging.getLogger(__name__)

def load_processed_dataset():
    """Load the processed dataset from the expected path."""
    paths = get_local_paths()
    dataset_path = paths['processed_dataset']
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Processed dataset not found at {dataset_path}. "
                                "Run the data pipeline (T018) first.")
    return pd.read_csv(dataset_path)

def calculate_unadjusted_spearman(df):
    """Calculate unadjusted Spearman rank correlation between age and burden."""
    # Ensure we have the necessary columns
    if 'age' not in df.columns or 'burden' not in df.columns:
        raise ValueError("Dataset must contain 'age' and 'burden' columns.")
    
    # Remove rows with missing values in critical columns
    clean_df = df.dropna(subset=['age', 'burden'])
    
    if len(clean_df) < 3:
        logger.warning("Insufficient data for correlation calculation.")
        return pd.DataFrame(columns=['method', 'coefficient', 'p_value'])
    
    corr, p_val = stats.spearmanr(clean_df['age'], clean_df['burden'])
    
    results = pd.DataFrame([{
        'method': 'spearman_unadjusted',
        'coefficient': corr,
        'p_value': p_val
    }])
    
    return results

def calculate_rank_ols(df):
    """
    Perform Rank-OLS regression: rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)
    
    As per plan.md Decision Log, Rank-OLS is used as a robust multivariate alternative
    to Partial Spearman. All continuous variables are rank-transformed before fitting.
    """
    required_cols = ['age', 'burden', 'sex', 'PC1', 'PC2', 'depth']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for Rank-OLS: {missing}")
    
    # Clean data
    clean_df = df.dropna(subset=required_cols).copy()
    
    if len(clean_df) < 10:
        logger.warning("Insufficient data for Rank-OLS regression.")
        return pd.DataFrame(columns=['term', 'coefficient', 'p_value', 'p_adj'])
    
    # Rank-transform continuous variables
    clean_df['rank_age'] = clean_df['age'].rank(method='average')
    clean_df['rank_burden'] = clean_df['burden'].rank(method='average')
    clean_df['rank_depth'] = clean_df['depth'].rank(method='average')
    
    # Prepare formula: rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)
    # Note: sex is categorical, PC1/PC2 are already numeric
    formula = "rank_age ~ rank_burden + C(sex) + PC1 + PC2 + rank_depth"
    
    try:
        model = smf.ols(formula, data=clean_df).fit()
    except Exception as e:
        logger.error(f"Rank-OLS regression failed: {e}")
        raise
    
    # Extract results
    results_list = []
    for term, row in model.summary2().tables[1].iterrows():
        coef = row['Coef.']
        p_val = row['P>|t|']
        results_list.append({
            'term': term,
            'coefficient': coef,
            'p_value': p_val,
            'p_adj': np.nan  # Will be filled by BH correction later
        })
    
    return pd.DataFrame(results_list)

def apply_benjamini_hochberg(results_df, p_value_col='p_value'):
    """
    Apply Benjamini-Hochberg correction to p-values.
    
    Parameters:
        results_df: DataFrame with p-values
        p_value_col: Column name containing p-values
        
    Returns:
        DataFrame with additional 'p_adj' column
    """
    if results_df.empty:
        return results_df
    
    p_values = results_df[p_value_col].values
    n = len(p_values)
    
    if n == 0:
        results_df['p_adj'] = np.nan
        return results_df
    
    # Sort indices by p-value
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate BH adjusted p-values
    rank = np.arange(1, n + 1)
    bh_threshold = (rank / n) * sorted_p_values[-1] if sorted_p_values[-1] > 0 else 1.0
    # Standard BH: p_adj = p * n / rank, then enforce monotonicity
    raw_adj = sorted_p_values * n / rank
    # Enforce monotonicity (cumulative min from the end)
    adj_p = np.minimum.accumulate(raw_adj[::-1])[::-1]
    adj_p = np.clip(adj_p, 0, 1)
    
    # Place adjusted p-values back in original order
    adj_p_final = np.empty(n)
    adj_p_final[sorted_indices] = adj_p
    
    results_df = results_df.copy()
    results_df['p_adj'] = adj_p_final
    
    return results_df

def record_secondary_ols_model(df, spearman_results):
    """
    Record coefficients and p-values for the secondary OLS model.
    
    This function:
    1. Fits a secondary OLS model (rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth))
    2. Extracts the coefficient for the burden term
    3. Calculates the delta between Spearman and OLS coefficients
    4. Logs the comparison to code/logs/model_comparison.log
    
    Note: The "secondary OLS" in FR-004 refers to the Rank-OLS model described in T024.
    We are comparing the primary Spearman correlation with this multivariate Rank-OLS.
    """
    paths = get_local_paths()
    log_dir = paths['logs_dir']
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'model_comparison.log')
    
    logger.info(f"Recording secondary OLS model comparison to {log_path}")
    
    # Get the rank-OLS results (which includes the burden coefficient)
    rank_ols_results = calculate_rank_ols(df)
    
    if rank_ols_results.empty:
        logger.error("Rank-OLS results are empty; cannot record comparison.")
        with open(log_path, 'w') as f:
            f.write("ERROR: Rank-OLS regression failed or produced no results.\n")
        return
    
    # Extract the burden coefficient (term should be 'rank_burden')
    burden_row = rank_ols_results[rank_ols_results['term'] == 'rank_burden']
    
    if burden_row.empty:
        logger.error("Could not find 'rank_burden' term in Rank-OLS results.")
        with open(log_path, 'w') as f:
            f.write("ERROR: 'rank_burden' term not found in Rank-OLS results.\n")
        return
    
    ols_coef = burden_row['coefficient'].values[0]
    ols_p_val = burden_row['p_value'].values[0]
    
    # Get Spearman coefficient
    if spearman_results.empty:
        logger.error("Spearman results are empty.")
        with open(log_path, 'w') as f:
            f.write("ERROR: Spearman correlation results are empty.\n")
        return
    
    spearman_coef = spearman_results['coefficient'].values[0]
    
    # Calculate delta
    delta = ols_coef - spearman_coef
    
    # Write to log file
    with open(log_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("MODEL COMPARISON: Spearman vs. Secondary OLS (Rank-OLS)\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("PRIMARY MODEL (Spearman Rank Correlation):\n")
        f.write(f"  Variable: age vs. burden (unadjusted)\n")
        f.write(f"  Coefficient: {spearman_coef:.6f}\n\n")
        
        f.write("SECONDARY MODEL (Rank-OLS Regression):\n")
        f.write(f"  Formula: rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)\n")
        f.write(f"  Burden Term: rank_burden\n")
        f.write(f"  Coefficient: {ols_coef:.6f}\n")
        f.write(f"  P-value: {ols_p_val:.6f}\n\n")
        
        f.write("COMPARISON:\n")
        f.write(f"  Delta (OLS - Spearman): {delta:.6f}\n")
        f.write(f"  Interpretation: {'Similar direction' if (ols_coef > 0 and spearman_coef > 0) or (ols_coef < 0 and spearman_coef < 0) else 'Opposite direction'}\n")
        f.write("=" * 60 + "\n")
    
    logger.info(f"Model comparison logged to {log_path}")

def main():
    """Main entry point for the model analysis."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load dataset
        logger.info("Loading processed dataset...")
        df = load_processed_dataset()
        logger.info(f"Loaded {len(df)} samples.")
        
        # Calculate unadjusted Spearman
        logger.info("Calculating unadjusted Spearman correlation...")
        spearman_results = calculate_unadjusted_spearman(df)
        
        # Save Spearman results
        paths = get_local_paths()
        spearman_path = paths['spearman_results']
        spearman_results.to_csv(spearman_path, index=False)
        logger.info(f"Spearman results saved to {spearman_path}")
        
        # Calculate Rank-OLS
        logger.info("Calculating Rank-OLS regression...")
        rank_ols_results = calculate_rank_ols(df)
        
        # Apply Benjamini-Hochberg correction
        if not rank_ols_results.empty:
            rank_ols_results = apply_benjamini_hochberg(rank_ols_results)
        
        # Save Rank-OLS results
        rank_ols_path = paths['rank_ols_results']
        rank_ols_results.to_csv(rank_ols_path, index=False)
        logger.info(f"Rank-OLS results saved to {rank_ols_path}")
        
        # Record secondary model comparison (T027)
        logger.info("Recording secondary OLS model comparison...")
        record_secondary_ols_model(df, spearman_results)
        
        logger.info("Model analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Model analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
