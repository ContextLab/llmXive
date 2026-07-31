import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.formula.api import ols
from statsmodels.stats.multitest import multipletests

# Ensure imports from environment config if needed, though not explicitly listed in API surface
# Assuming environment paths are handled by get_local_paths in config.environment
from config.environment import get_local_paths

logger = logging.getLogger(__name__)

def calculate_unadjusted_spearman(df: pd.DataFrame) -> tuple:
    """
    Calculate unadjusted Spearman correlation between heteroplasmy burden and age.
    
    Args:
        df: Processed dataset containing 'burden' and 'age' columns.
        
    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    if 'burden' not in df.columns or 'age' not in df.columns:
        raise ValueError("Dataset must contain 'burden' and 'age' columns")
    
    # Drop rows with missing values in critical columns
    valid_data = df[['burden', 'age']].dropna()
    
    if len(valid_data) < 2:
        logger.warning("Insufficient data for correlation calculation")
        return np.nan, np.nan
    
    corr, p_val = valid_data['burden'].corr(valid_data['age'], method='spearman')
    return corr, p_val

def calculate_rank_ols(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform Rank-OLS regression: rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)
    
    Args:
        df: Processed dataset with necessary columns.
        
    Returns:
        DataFrame containing model coefficients, p-values, and statistics.
    """
    required_cols = ['age', 'burden', 'sex', 'PC1', 'PC2', 'depth']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for Rank-OLS: {missing}")
    
    # Create a copy to avoid modifying original
    data = df.copy()
    
    # Rank-transform continuous variables as per specification
    data['rank_age'] = data['age'].rank()
    data['rank_burden'] = data['burden'].rank()
    data['rank_depth'] = data['depth'].rank()
    
    # Prepare formula: rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)
    # Note: PC1 and PC2 are not rank-transformed per the specific instruction in T024
    formula = "rank_age ~ rank_burden + C(sex) + PC1 + PC2 + rank_depth"
    
    # Fit model
    model = ols(formula, data=data).fit()
    
    # Extract results
    results = []
    for idx, row in model.summary2().tables[1].iterrows():
        results.append({
            'variable': row[0],
            'coef': row[1],
            'std_err': row[2],
            't': row[3],
            'P>|t|': row[4],
            '[0.025': row[5],
            '0.975]': row[6]
        })
    
    results_df = pd.DataFrame(results)
    return results_df

def apply_benjamini_hochberg(df: pd.DataFrame, p_value_col: str = 'P>|t|') -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg correction to p-values.
    
    Args:
        df: DataFrame containing p-values.
        p_value_col: Name of the column containing p-values.
        
    Returns:
        DataFrame with added adjusted p-values.
    """
    if p_value_col not in df.columns:
        raise ValueError(f"Column '{p_value_col}' not found in DataFrame")
    
    p_values = df[p_value_col].values
    # Handle NaN values
    valid_mask = ~np.isnan(p_values)
    adjusted_p_values = np.full_like(p_values, np.nan, dtype=float)
    
    if np.sum(valid_mask) > 0:
        _, adjusted, _, _ = multipletests(p_values[valid_mask], method='fdr_bh')
        adjusted_p_values[valid_mask] = adjusted
    
    df = df.copy()
    df['adj_P_val'] = adjusted_p_values
    return df

def record_secondary_ols_model(df: pd.DataFrame, output_path: Path) -> None:
    """
    Record coefficients and p-values for the secondary OLS model to a log file.
    This implements the requirement from FR-004 to track secondary model metrics.
    
    Args:
        df: DataFrame containing the secondary OLS model results (from calculate_rank_ols).
        output_path: Path to the log file where results will be recorded.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format log entries
    log_entries = []
    log_entries.append(f"Secondary OLS Model Results - {pd.Timestamp.now().isoformat()}")
    log_entries.append("=" * 60)
    
    for _, row in df.iterrows():
        variable = row['variable']
        coef = row['coef']
        p_val = row['P>|t|']
        adj_p_val = row.get('adj_P_val', np.nan)
        
        entry = (
            f"Variable: {variable:<20} | "
            f"Coefficient: {coef:>12.6f} | "
            f"P-value: {p_val:>12.6f}"
        )
        if not np.isnan(adj_p_val):
            entry += f" | Adj. P-value: {adj_p_val:>12.6f}"
        
        log_entries.append(entry)
    
    log_entries.append("=" * 60)
    log_entries.append(f"Total variables: {len(df)}")
    
    # Write to log file
    with open(output_path, 'w') as f:
        f.write('\n'.join(log_entries))
    
    logger.info(f"Secondary OLS model results recorded to {output_path}")

def main():
    """
    Main execution function for statistical modeling and recording.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('code/logs/model_analysis.log')
        ]
    )
    
    logger.info("Starting statistical modeling pipeline")
    
    # Get paths
    paths = get_local_paths()
    processed_data_path = paths['processed_data'] / 'mito_aging_dataset.csv'
    model_results_path = paths['processed_data'] / 'model_results.csv'
    secondary_log_path = paths['logs'] / 'model_comparison.log'
    
    # Load processed dataset
    if not processed_data_path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {processed_data_path}")
    
    df = pd.read_csv(processed_data_path)
    logger.info(f"Loaded dataset with {len(df)} samples")
    
    # Calculate unadjusted Spearman correlation
    spearman_corr, spearman_p = calculate_unadjusted_spearman(df)
    logger.info(f"Unadjusted Spearman correlation: {spearman_corr:.4f} (p={spearman_p:.4f})")
    
    # Calculate Rank-OLS model
    try:
        rank_ols_results = calculate_rank_ols(df)
        rank_ols_results = apply_benjamini_hochberg(rank_ols_results)
        
        # Save model results to CSV
        rank_ols_results.to_csv(model_results_path, index=False)
        logger.info(f"Model results saved to {model_results_path}")
        
        # Record secondary OLS model to log
        record_secondary_ols_model(rank_ols_results, secondary_log_path)
        
    except Exception as e:
        logger.error(f"Error during Rank-OLS calculation: {e}")
        raise
    
    logger.info("Statistical modeling pipeline completed successfully")

if __name__ == "__main__":
    main()
