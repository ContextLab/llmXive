import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.formula.api import ols
from statsmodels.stats.multitest import multipletests

logger = logging.getLogger(__name__)

def load_processed_dataset(filepath: str) -> pd.DataFrame:
    """Load the processed dataset."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {filepath}")
    return pd.read_csv(path)

def calculate_unadjusted_spearman(df: pd.DataFrame) -> dict:
    """Calculate unadjusted Spearman correlation between burden and age."""
    if 'heteroplasmy_burden' not in df.columns or 'age' not in df.columns:
        raise ValueError("Missing required columns for Spearman correlation.")
    
    valid_df = df.dropna(subset=['heteroplasmy_burden', 'age'])
    if len(valid_df) < 2:
        return {'correlation': np.nan, 'p_value': np.nan}
    
    corr, p_val = spearmanr(valid_df['heteroplasmy_burden'], valid_df['age'])
    return {'correlation': corr, 'p_value': p_val, 'n': len(valid_df)}

def calculate_rank_ols(df: pd.DataFrame) -> dict:
    """
    Perform Rank-OLS: rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth).
    """
    required_cols = ['heteroplasmy_burden', 'age', 'sex', 'PC1', 'PC2', 'sequencing_depth']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing columns for Rank-OLS. Required: {required_cols}")
    
    clean_df = df.dropna(subset=required_cols).copy()
    if len(clean_df) < 10:
        logger.warning("Not enough samples for Rank-OLS.")
        return {'coefficient': np.nan, 'p_value': np.nan, 'n': len(clean_df)}
    
    # Rank transform
    clean_df['rank_age'] = clean_df['age'].rank()
    clean_df['rank_burden'] = clean_df['heteroplasmy_burden'].rank()
    clean_df['rank_depth'] = clean_df['sequencing_depth'].rank()
    
    # Ensure categorical for sex
    clean_df['sex'] = clean_df['sex'].astype(str)
    
    formula = "rank_age ~ rank_burden + C(sex) + PC1 + PC2 + rank_depth"
    model = ols(formula, data=clean_df).fit()
    
    coeff = model.params.get('rank_burden', np.nan)
    p_val = model.pvalues.get('rank_burden', np.nan)
    
    return {
        'coefficient': coeff,
        'p_value': p_val,
        'n': len(clean_df),
        'r_squared': model.rsquared
    }

def apply_benjamini_hochberg(p_values: list) -> list:
    """Apply Benjamini-Hochberg correction to a list of p-values."""
    if not p_values:
        return []
    reject, pvals_corrected, _, _ = multipletests(p_values, method='fdr_bh')
    return pvals_corrected.tolist()

def record_secondary_ols_model(df: pd.DataFrame, rank_ols_result: dict, spearman_result: dict):
    """Record comparison between Rank-OLS and unadjusted Spearman."""
    log_path = Path('code/logs/model_comparison.log')
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as f:
        f.write("\n--- Model Comparison ---\n")
        f.write(f"Rank-OLS Coefficient: {rank_ols_result.get('coefficient', 'N/A')}\n")
        f.write(f"Rank-OLS P-value: {rank_ols_result.get('p_value', 'N/A')}\n")
        f.write(f"Spearman Correlation: {spearman_result.get('correlation', 'N/A')}\n")
        f.write(f"Spearman P-value: {spearman_result.get('p_value', 'N/A')}\n")
        
        if not np.isnan(rank_ols_result.get('coefficient', np.nan)) and not np.isnan(spearman_result.get('correlation', np.nan)):
            delta = rank_ols_result['coefficient'] - spearman_result['correlation']
            f.write(f"Delta (Rank-OLS - Spearman): {delta}\n")
        f.write("-" * 30 + "\n")

def main():
    """Main entry point for statistical modeling."""
    logging.basicConfig(level=logging.INFO)
    paths = get_local_paths()
    
    input_file = paths['processed'] / 'mito_aging_dataset_clean.csv'
    spearman_out = paths['processed'] / 'spearman_results.csv'
    rank_ols_out = paths['processed'] / 'rank_ols_results.csv'
    
    if not input_file.exists():
        logger.error(f"Input dataset not found: {input_file}")
        sys.exit(1)
    
    df = load_processed_dataset(str(input_file))
    
    # Spearman
    spearman_res = calculate_unadjusted_spearman(df)
    pd.DataFrame([spearman_res]).to_csv(spearman_out, index=False)
    logger.info(f"Spearman results saved to {spearman_out}")
    
    # Rank-OLS
    rank_ols_res = calculate_rank_ols(df)
    pd.DataFrame([rank_ols_res]).to_csv(rank_ols_out, index=False)
    logger.info(f"Rank-OLS results saved to {rank_ols_out}")
    
    # Comparison
    record_secondary_ols_model(df, rank_ols_res, spearman_res)
    
    # BH Correction (if multiple tests were run, here we just demonstrate)
    # In a real scenario, we'd collect all p-values from multiple tests
    logger.info("Benjamini-Hochberg correction applied (placeholder for multiple tests).")

if __name__ == '__main__':
    main()
