"""
Statistical modeling module for MITO-AGING correlation analysis.
Implements Rank-OLS and Spearman correlation as per plan.md Decision Log.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.formula.api import ols
from statsmodels.stats.multitest import multipletests
from scipy.stats import spearmanr

# Ensure paths are set up correctly for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.environment import get_local_paths

logger = logging.getLogger(__name__)

def load_processed_dataset():
    """
    Load the processed dataset from code/data/processed/mito_aging_dataset.csv.
    Returns a pandas DataFrame.
    """
    paths = get_local_paths()
    input_path = paths['processed_data'] / 'mito_aging_dataset.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at {input_path}. "
            "Ensure T018/T020 (data processing) has completed successfully."
        )
    
    logger.info(f"Loading processed dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    # Verify critical columns exist
    required_cols = ['sample_id', 'heteroplasmy_burden', 'age', 'sex', 'PC1', 'PC2', 'sequencing_depth']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
    
    return df

def calculate_unadjusted_spearman(df):
    """
    Calculate unadjusted Spearman rank correlation between heteroplasmy_burden and age.
    Returns a DataFrame with coefficient and p-value.
    """
    logger.info("Calculating unadjusted Spearman correlation")
    
    # Drop rows with missing values in critical columns
    clean_df = df.dropna(subset=['heteroplasmy_burden', 'age'])
    
    if len(clean_df) < 2:
        raise ValueError("Insufficient data for Spearman correlation (need at least 2 non-null pairs)")
    
    corr, p_value = spearmanr(clean_df['heteroplasmy_burden'], clean_df['age'])
    
    result = pd.DataFrame({
        'model': ['unadjusted_spearman'],
        'coefficient': [corr],
        'p_value': [p_value],
        'n_samples': [len(clean_df)]
    })
    
    return result

def calculate_rank_ols(df):
    """
    Implement Rank-OLS as the primary adjusted analysis per plan.md Decision Log.
    
    Steps:
    1. Rank-transform: heteroplasmy_burden, age, sequencing_depth, PC1, PC2
    2. Fit OLS: rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)
    3. Extract coefficient and p-value for rank(burden)
    
    Returns a DataFrame with model results.
    """
    logger.info("Calculating Rank-OLS adjusted analysis")
    
    # Drop rows with missing values in critical columns
    clean_df = df.dropna(subset=['heteroplasmy_burden', 'age', 'sequencing_depth', 'PC1', 'PC2', 'sex'])
    
    if len(clean_df) < 10:
        raise ValueError("Insufficient data for Rank-OLS regression (need at least 10 samples)")
    
    # Rank-transform the continuous variables
    # Note: We rank the variables as specified, but keep sex as categorical
    df_ranked = clean_df.copy()
    df_ranked['rank_burden'] = df_ranked['heteroplasmy_burden'].rank(method='average')
    df_ranked['rank_age'] = df_ranked['age'].rank(method='average')
    df_ranked['rank_depth'] = df_ranked['sequencing_depth'].rank(method='average')
    df_ranked['rank_PC1'] = df_ranked['PC1'].rank(method='average')
    df_ranked['rank_PC2'] = df_ranked['PC2'].rank(method='average')
    
    # Ensure sex is treated as categorical
    df_ranked['sex'] = df_ranked['sex'].astype('category')
    
    # Fit the OLS model: rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)
    # Note: The formula uses the rank-transformed variables
    formula = "rank_age ~ rank_burden + C(sex) + rank_PC1 + rank_PC2 + rank_depth"
    
    try:
        model = ols(formula, data=df_ranked).fit()
    except Exception as e:
        logger.error(f"OLS model fitting failed: {e}")
        raise RuntimeError(f"Failed to fit Rank-OLS model: {e}")
    
    # Extract results for rank_burden
    rank_burden_result = model.summary2().tables[1].loc['rank_burden']
    coef = rank_burden_result['Coef.']
    p_val = rank_burden_result['P>|t|']
    
    result = pd.DataFrame({
        'model': ['rank_ols_adjusted'],
        'coefficient': [coef],
        'p_value': [p_val],
        'n_samples': [len(clean_df)],
        'formula': [formula]
    })
    
    logger.info(f"Rank-OLS completed: coefficient={coef:.6f}, p-value={p_val:.6e}")
    return result

def apply_benjamini_hochberg(results_df):
    """
    Apply Benjamini-Hochberg correction to a DataFrame of p-values.
    Expects a DataFrame with 'p_value' column.
    Returns the DataFrame with added 'p_value_adj' column.
    """
    if results_df.empty:
        return results_df
    
    p_values = results_df['p_value'].values
    reject, p_adj, _, _ = multipletests(p_values, method='fdr_bh')
    
    results_df = results_df.copy()
    results_df['p_value_adj'] = p_adj
    results_df['rejected'] = reject
    
    return results_df

def record_secondary_ols_model(df, rank_ols_result, spearman_result):
    """
    Record coefficients and p-values for secondary OLS model comparison.
    Calculates delta between Rank-OLS and unadjusted Spearman coefficients.
    Writes comparison to code/logs/model_comparison.log.
    """
    paths = get_local_paths()
    log_path = paths['logs'] / 'model_comparison.log'
    
    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        f.write("Model Comparison Report: Rank-OLS vs Unadjusted Spearman\n")
        f.write("=" * 60 + "\n\n")
        
        if not rank_ols_result.empty:
            rank_coef = rank_ols_result['coefficient'].iloc[0]
            rank_pval = rank_ols_result['p_value'].iloc[0]
            f.write(f"Rank-OLS (Adjusted):\n")
            f.write(f"  Coefficient: {rank_coef:.6f}\n")
            f.write(f"  P-value: {rank_pval:.6e}\n")
            f.write(f"  N samples: {rank_ols_result['n_samples'].iloc[0]}\n\n")
        
        if not spearman_result.empty:
            spearman_coef = spearman_result['coefficient'].iloc[0]
            spearman_pval = spearman_result['p_value'].iloc[0]
            f.write(f"Unadjusted Spearman:\n")
            f.write(f"  Coefficient: {spearman_coef:.6f}\n")
            f.write(f"  P-value: {spearman_pval:.6e}\n")
            f.write(f"  N samples: {spearman_result['n_samples'].iloc[0]}\n\n")
        
        if not rank_ols_result.empty and not spearman_result.empty:
            delta = rank_coef - spearman_coef
            f.write(f"Comparison:\n")
            f.write(f"  Delta (Rank-OLS - Spearman): {delta:.6f}\n")
            f.write(f"  Interpretation: {'Rank-OLS effect is larger' if delta > 0 else 'Spearman effect is larger'}\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("Note: Rank-OLS was selected as primary method per plan.md Decision Log.\n")
        f.write("This resolves the methodological contradiction between spec's 'Partial Spearman'\n")
        f.write("mention and plan's 'Rank-OLS' decision.\n")
    
    logger.info(f"Model comparison logged to {log_path}")

def main():
    """
    Main entry point for statistical modeling.
    Executes Spearman and Rank-OLS analyses, saves results, and logs comparisons.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load dataset
        df = load_processed_dataset()
        logger.info(f"Loaded dataset with {len(df)} samples")
        
        # Calculate unadjusted Spearman
        spearman_result = calculate_unadjusted_spearman(df)
        
        # Calculate Rank-OLS
        rank_ols_result = calculate_rank_ols(df)
        
        # Combine results for BH correction
        combined_results = pd.concat([spearman_result, rank_ols_result], ignore_index=True)
        corrected_results = apply_benjamini_hochberg(combined_results)
        
        # Save individual results
        paths = get_local_paths()
        
        # Save Spearman results
        spearman_path = paths['processed_data'] / 'spearman_results.csv'
        spearman_result.to_csv(spearman_path, index=False)
        logger.info(f"Spearman results saved to {spearman_path}")
        
        # Save Rank-OLS results (PRIMARY OUTPUT FOR THIS TASK)
        rank_ols_path = paths['processed_data'] / 'rank_ols_results.csv'
        rank_ols_result.to_csv(rank_ols_path, index=False)
        logger.info(f"Rank-OLS results saved to {rank_ols_path}")
        
        # Save combined corrected results
        corrected_path = paths['processed_data'] / 'model_results_corrected.csv'
        corrected_results.to_csv(corrected_path, index=False)
        logger.info(f"Corrected model results saved to {corrected_path}")
        
        # Record model comparison
        record_secondary_ols_model(df, rank_ols_result, spearman_result)
        
        logger.info("Statistical modeling completed successfully")
        
    except Exception as e:
        logger.error(f"Statistical modeling failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
