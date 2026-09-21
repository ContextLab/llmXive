import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

from config import INPUT_PATHS, SAMPLE_LIMIT, RANDOM_SEED
from logging_config import get_logger, log_warning, log_provenance

logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """Load the cleaned dataset from the processed directory."""
    input_path = Path(INPUT_PATHS['processed_data'])
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {input_path}")
    
    logger.info(f"Loading processed data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Apply sample limit if configured
    if SAMPLE_LIMIT and len(df) > SAMPLE_LIMIT:
        logger.warning(f"Dataset size ({len(df)}) exceeds SAMPLE_LIMIT ({SAMPLE_LIMIT}). Truncating.")
        df = df.head(SAMPLE_LIMIT)
    
    return df

def check_zero_variance(df: pd.DataFrame, column: str) -> bool:
    """
    Check if a specific column has zero variance (constant values).
    
    Args:
        df: Input DataFrame
        column: Name of the column to check
        
    Returns:
        True if zero variance detected, False otherwise
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")
    
    # Drop NaN values before checking variance
    non_null_values = df[column].dropna()
    
    if len(non_null_values) == 0:
        logger.warning(f"Column '{column}' contains only NaN values")
        return True
    
    # Check variance
    variance = non_null_values.var()
    is_zero_variance = variance == 0 or variance < 1e-10
    
    if is_zero_variance:
        logger.warning(f"Zero variance detected in column '{column}' (variance={variance})")
    
    return is_zero_variance

def compute_spearman_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> Tuple[float, float, int]:
    """
    Compute Spearman rank correlation between two columns.
    
    Args:
        df: Input DataFrame
        x_col: Name of the first column
        y_col: Name of the second column
        
    Returns:
        Tuple of (r_value, p_value, n_obs)
    """
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Columns '{x_col}' or '{y_col}' not found in DataFrame")
    
    # Drop rows with NaN in either column
    valid_data = df[[x_col, y_col]].dropna()
    n_obs = len(valid_data)
    
    if n_obs < 3:
        raise ValueError(f"Insufficient data for correlation: only {n_obs} valid observations")
    
    r_value, p_value = scipy.stats.spearmanr(valid_data[x_col], valid_data[y_col])
    
    logger.info(f"Spearman correlation between '{x_col}' and '{y_col}': r={r_value:.4f}, p={p_value:.4f}")
    
    return float(r_value), float(p_value), n_obs

def run_multivariate_regression(df: pd.DataFrame) -> Any:
    """
    Run multivariate linear regression with Shannon index and covariates.
    
    Args:
        df: Input DataFrame with all required columns
        
    Returns:
        Fitted OLS model results
    """
    import statsmodels.api as sm
    
    # Define formula
    formula = "fluid_intelligence ~ shannon_index + age + bmi + dqs + C(sex)"
    
    # Fit model
    model = sm.formula.ols(formula=formula, data=df)
    results = model.fit()
    
    logger.info("Multivariate regression completed successfully")
    
    return results

def calculate_vif(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for multicollinearity diagnostics.
    
    Args:
        df: Input DataFrame with predictors
        
    Returns:
        DataFrame with VIF values for each predictor
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Select numeric predictors
    predictors = ['shannon_index', 'age', 'bmi', 'dqs']
    
    # Handle categorical variable (sex) by encoding
    df_encoded = df.copy()
    if 'sex' in df.columns:
        df_encoded['sex'] = df_encoded['sex'].astype('category').cat.codes
        predictors.append('sex')
    
    X = df_encoded[predictors].dropna()
    
    if X.shape[0] == 0:
        raise ValueError("No valid data for VIF calculation")
    
    # Add constant
    X_with_const = sm.add_constant(X)
    
    vif_data = []
    for i, col in enumerate(X_with_const.columns):
        vif = variance_inflation_factor(X_with_const.values, i)
        vif_data.append({
            'variable': col,
            'vif': vif
        })
    
    vif_df = pd.DataFrame(vif_data)
    
    logger.info(f"VIF calculation completed. Max VIF: {vif_df['vif'].max():.2f}")
    
    return vif_df

def save_vif_results(vif_df: pd.DataFrame, output_path: str) -> None:
    """Save VIF results to CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    vif_df.to_csv(output_path, index=False)
    logger.info(f"VIF results saved to {output_path}")

def save_regression_results(results, output_path: str) -> None:
    """Save regression results to CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract summary table
    summary = results.summary2().tables[1]
    df_results = pd.DataFrame(summary.data[1:], columns=summary.data[0])
    df_results.to_csv(output_path, index=False)
    
    logger.info(f"Regression results saved to {output_path}")

def run_analysis_pipeline() -> Dict[str, Any]:
    """
    Run the full analysis pipeline:
    1. Load processed data
    2. Check for zero variance in fluid intelligence
    3. Compute Spearman correlation (if no zero variance)
    4. Run multivariate regression
    5. Calculate VIF
    
    Returns:
        Dictionary with analysis results
    """
    import scipy.stats
    
    results = {}
    
    # Load data
    df = load_processed_data()
    results['n_samples'] = len(df)
    
    # Check zero variance in fluid intelligence
    is_zero_var = check_zero_variance(df, 'fluid_intelligence')
    results['zero_variance_detected'] = is_zero_var
    
    if is_zero_var:
        # Log warning and skip correlation
        log_warning(
            "Zero variance detected in fluid_intelligence. Skipping correlation analysis.",
            output_file="data/processed/analysis_warnings.log"
        )
        logger.warning("Zero variance detected. Skipping correlation and regression analysis.")
        results['correlation'] = None
        results['regression'] = None
        results['vif'] = None
        return results
    
    # Compute Spearman correlation
    r_value, p_value, n_obs = compute_spearman_correlation(df, 'shannon_index', 'fluid_intelligence')
    results['correlation'] = {
        'r_value': r_value,
        'p_value': p_value,
        'n_obs': n_obs
    }
    
    # Run multivariate regression
    regression_results = run_multivariate_regression(df)
    results['regression'] = regression_results
    
    # Calculate VIF
    vif_df = calculate_vif(df)
    results['vif'] = vif_df
    
    return results

def main():
    """Main entry point for analysis pipeline."""
    logger.info("Starting analysis pipeline")
    
    try:
        results = run_analysis_pipeline()
        
        # Save results
        if results['correlation']:
            from save_correlation_results import save_correlation_results
            save_correlation_results(
                results['correlation']['r_value'],
                results['correlation']['p_value'],
                results['correlation']['n_obs']
            )
        
        if results['regression']:
            from save_regression_results import save_regression_results
            save_regression_results(results['regression'])
        
        if results['vif'] is not None:
            save_vif_results(results['vif'], 'data/processed/vif_results.csv')
        
        logger.info("Analysis pipeline completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
