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

def load_processed_dataset() -> pd.DataFrame:
    """Load the processed dataset from the previous stage."""
    paths = get_local_paths()
    dataset_path = paths['processed_dataset']
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Processed dataset not found at {dataset_path}")
    df = pd.read_csv(dataset_path)
    logger.info(f"Loaded dataset with {len(df)} samples")
    return df

def calculate_unadjusted_spearman(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate unadjusted Spearman rank correlation between burden and age."""
    if 'heteroplasmy_burden' not in df.columns or 'age' not in df.columns:
        raise ValueError("Dataset missing 'heteroplasmy_burden' or 'age' columns")
    
    # Drop rows with missing values in critical columns
    valid_df = df.dropna(subset=['heteroplasmy_burden', 'age'])
    
    if len(valid_df) < 3:
        logger.warning("Insufficient data points for correlation calculation")
        return pd.DataFrame(columns=['coefficient', 'p_value', 'method', 'n_samples'])
    
    corr, p_val = stats.spearmanr(valid_df['heteroplasmy_burden'], valid_df['age'])
    
    result = pd.DataFrame([{
        'coefficient': corr,
        'p_value': p_val,
        'method': 'spearman_unadjusted',
        'n_samples': len(valid_df)
    }])
    
    logger.info(f"Spearman correlation: {corr:.4f}, p-value: {p_val:.4f}")
    return result

def calculate_rank_ols(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform Rank-OLS regression: rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)
    Uses depth-stratified burden as per T016.
    """
    required_cols = ['heteroplasmy_burden', 'age', 'sex', 'PC1', 'PC2', 'depth_strat']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")
    
    # Create a working copy to avoid SettingWithCopyWarning
    working_df = df.copy()
    
    # Rank transform continuous variables
    working_df['rank_age'] = working_df['age'].rank()
    working_df['rank_burden'] = working_df['heteroplasmy_burden'].rank()
    working_df['rank_depth'] = working_df['depth_strat'].rank()
    
    # Encode sex as numeric (0/1) for regression
    # Assuming sex is 'M'/'F' or similar
    if working_df['sex'].dtype == 'object':
        working_df['sex_num'] = (working_df['sex'] == 'M').astype(int)
    else:
        working_df['sex_num'] = working_df['sex']
    
    # Drop rows with any NaNs in the regression variables
    model_df = working_df.dropna(subset=['rank_age', 'rank_burden', 'sex_num', 'PC1', 'PC2', 'rank_depth'])
    
    if len(model_df) < 5:
        logger.warning("Insufficient data points for Rank-OLS regression")
        return pd.DataFrame(columns=['variable', 'coefficient', 'p_value', 'adj_p_value', 'model_type'])
    
    # Define formula: rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)
    formula = 'rank_age ~ rank_burden + sex_num + PC1 + PC2 + rank_depth'
    
    try:
        model = ols(formula, data=model_df).fit()
    except Exception as e:
        logger.error(f"Rank-OLS regression failed: {e}")
        return pd.DataFrame(columns=['variable', 'coefficient', 'p_value', 'adj_p_value', 'model_type'])
    
    results = []
    for var in model.params.index:
        if var != 'Intercept':
            results.append({
                'variable': var,
                'coefficient': model.params[var],
                'p_value': model.pvalues[var],
                'adj_p_value': np.nan, # Will be filled later
                'model_type': 'rank_ols'
            })
    
    logger.info(f"Rank-OLS regression completed with {len(model_df)} samples")
    return pd.DataFrame(results)

def apply_benjamini_hochberg(results_df: pd.DataFrame) -> pd.DataFrame:
    """Apply Benjamini-Hochberg correction to p-values in the results dataframe."""
    if results_df.empty or 'p_value' not in results_df.columns:
        return results_df
    
    # Sort by p-value
    sorted_df = results_df.sort_values('p_value').reset_index(drop=True)
    n = len(sorted_df)
    
    # Calculate adjusted p-values
    adjusted_p = np.zeros(n)
    for i in range(n):
        adjusted_p[i] = sorted_df['p_value'].iloc[i] * n / (i + 1)
    
    # Ensure monotonicity (cumulative min from the bottom)
    for i in range(n - 2, -1, -1):
        adjusted_p[i] = min(adjusted_p[i], adjusted_p[i + 1])
    
    # Cap at 1.0
    adjusted_p = np.minimum(adjusted_p, 1.0)
    
    sorted_df['adj_p_value'] = adjusted_p
    
    # Restore original order
    results_df = results_df.sort_index().reset_index(drop=True)
    sorted_df = sorted_df.sort_index().reset_index(drop=True)
    
    return sorted_df

def record_secondary_ols_model(spearman_results: pd.DataFrame, rank_ols_results: pd.DataFrame) -> None:
    """
    Record coefficients and p-values for the secondary OLS model (Rank-OLS)
    and compare with the primary Spearman model.
    Calculates the delta between Spearman and OLS coefficients.
    Writes to code/logs/model_comparison.log.
    """
    paths = get_local_paths()
    log_dir = paths['logs_dir']
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'model_comparison.log')
    
    with open(log_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("MODEL COMPARISON: Spearman vs Rank-OLS\n")
        f.write("=" * 60 + "\n\n")
        
        # 1. Record Spearman Results
        f.write("PRIMARY MODEL: Unadjusted Spearman Rank Correlation\n")
        f.write("-" * 40 + "\n")
        if not spearman_results.empty:
            row = spearman_results.iloc[0]
            f.write(f"Coefficient: {row['coefficient']:.6f}\n")
            f.write(f"P-value:     {row['p_value']:.6f}\n")
            f.write(f"N Samples:   {row['n_samples']}\n")
        else:
            f.write("No Spearman results available.\n")
        f.write("\n")
        
        # 2. Record Secondary OLS (Rank-OLS) Results
        f.write("SECONDARY MODEL: Rank-OLS Regression\n")
        f.write("-" * 40 + "\n")
        if not rank_ols_results.empty:
            # Find the burden coefficient specifically
            burden_row = rank_ols_results[rank_ols_results['variable'] == 'rank_burden']
            if not burden_row.empty:
                row = burden_row.iloc[0]
                f.write(f"Variable:    rank_burden\n")
                f.write(f"Coefficient: {row['coefficient']:.6f}\n")
                f.write(f"P-value:     {row['p_value']:.6f}\n")
                f.write(f"Adj P-value: {row['adj_p_value']:.6f}\n")
                
                # 3. Calculate Delta
                if not spearman_results.empty:
                    spearman_coef = spearman_results.iloc[0]['coefficient']
                    ols_coef = row['coefficient']
                    delta = ols_coef - spearman_coef
                    f.write("\n")
                    f.write("COMPARISON METRICS\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Spearman Coefficient: {spearman_coef:.6f}\n")
                    f.write(f"Rank-OLS Coefficient: {ols_coef:.6f}\n")
                    f.write(f"Delta (OLS - Spearman): {delta:.6f}\n")
                    
                    # Interpretation
                    if abs(delta) < 0.05:
                        f.write("Interpretation: Coefficients are closely aligned (delta < 0.05).\n")
                    elif delta > 0:
                        f.write("Interpretation: Rank-OLS coefficient is higher than Spearman.\n")
                    else:
                        f.write("Interpretation: Rank-OLS coefficient is lower than Spearman.\n")
            else:
                f.write("No 'rank_burden' variable found in Rank-OLS results.\n")
                f.write("Full results:\n")
                f.write(rank_ols_results.to_string())
        else:
            f.write("No Rank-OLS results available.\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("END OF COMPARISON\n")
        f.write("=" * 60 + "\n")
    
    logger.info(f"Model comparison logged to {log_path}")

def main():
    """Main entry point for the statistical modeling task."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 1. Load Data
        df = load_processed_dataset()
        
        # 2. Calculate Unadjusted Spearman
        spearman_results = calculate_unadjusted_spearman(df)
        spearman_path = get_local_paths()['spearman_results']
        spearman_results.to_csv(spearman_path, index=False)
        logger.info(f"Saved Spearman results to {spearman_path}")
        
        # 3. Calculate Rank-OLS
        rank_ols_results = calculate_rank_ols(df)
        
        # 4. Apply BH Correction
        rank_ols_results = apply_benjamini_hochberg(rank_ols_results)
        rank_ols_path = get_local_paths()['rank_ols_results']
        rank_ols_results.to_csv(rank_ols_path, index=False)
        logger.info(f"Saved Rank-OLS results to {rank_ols_path}")
        
        # 5. Record Comparison (T027)
        record_secondary_ols_model(spearman_results, rank_ols_results)
        
        logger.info("Statistical modeling completed successfully.")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == '__main__':
    main()