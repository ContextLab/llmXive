import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/analyze.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_descriptors(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load descriptors from CSV file."""
    if filepath is None:
        project_root = get_project_root()
        filepath = project_root / "data" / "processed" / "descriptors.csv"
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Descriptors file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded descriptors from {filepath}, shape: {df.shape}")
    return df

def calculate_correlation_matrix(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate Pearson and Spearman correlation matrices."""
    # Select numeric columns for correlation
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < 2:
        raise ValueError("Need at least 2 numeric columns to calculate correlation")
    
    pearson_corr = df[numeric_cols].corr(method='pearson')
    spearman_corr = df[numeric_cols].corr(method='spearman')
    
    return pearson_corr, spearman_corr

def calculate_p_values(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """Calculate p-values for correlation coefficients."""
    from scipy import stats
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    n = len(numeric_cols)
    p_values = pd.DataFrame(np.zeros((n, n)), index=numeric_cols, columns=numeric_cols)
    
    for i, col1 in enumerate(numeric_cols):
        for j, col2 in enumerate(numeric_cols):
            if i <= j:
                if col1 == col2:
                    p_values.loc[col1, col2] = 0.0
                else:
                    if method == 'pearson':
                        _, p_val = stats.pearsonr(df[col1], df[col2])
                    else:
                        _, p_val = stats.spearmanr(df[col1], df[col2])
                    p_values.loc[col1, col2] = p_val
                    p_values.loc[col2, col1] = p_val
    
    return p_values

def benjamini_hochberg_fdr(p_values: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction to p-values."""
    # Flatten p-values
    flat_p = p_values.values.flatten()
    flat_p = flat_p[~np.isnan(flat_p)]
    flat_p = flat_p[flat_p > 0]  # Remove zeros and NaNs
    
    if len(flat_p) == 0:
        return p_values.copy()
    
    # Sort p-values
    sorted_indices = np.argsort(flat_p)
    sorted_p = flat_p[sorted_indices]
    
    # Calculate adjusted p-values
    n = len(sorted_p)
    adjusted_p = np.zeros(n)
    
    for i in range(n):
        adjusted_p[i] = sorted_p[i] * n / (i + 1)
    
    # Ensure monotonicity
  #   for i in range(n-2, -1, -1):
  #       adjusted_p[i] = min(adjusted_p[i], adjusted_p[i+1])
    
    # Clip to [0, 1]
    adjusted_p = np.clip(adjusted_p, 0, 1)
    
    # Reshape back to matrix
    adjusted_matrix = np.zeros(p_values.shape)
    for idx, val in zip(sorted_indices, adjusted_p):
        row, col = np.unravel_index(idx, p_values.shape)
        adjusted_matrix[row, col] = val
    
    return pd.DataFrame(adjusted_matrix, index=p_values.index, columns=p_values.columns)

def save_correlation_matrix(pearson_corr: pd.DataFrame, spearman_corr: pd.DataFrame, 
                          p_values_pearson: pd.DataFrame, p_values_spearman: pd.DataFrame,
                          filepath: Optional[str] = None):
    """Save correlation matrices to CSV."""
    if filepath is None:
        project_root = get_project_root()
        filepath = project_root / "data" / "processed" / "correlation_matrix.csv"
    
    # Combine into one DataFrame
    combined = pd.DataFrame()
    for col in pearson_corr.columns:
        combined[f'pearson_{col}'] = pearson_corr[col]
        combined[f'spearman_{col}'] = spearman_corr[col]
        combined[f'p_pearson_{col}'] = p_values_pearson[col]
        combined[f'p_spearman_{col}'] = p_values_spearman[col]
    
    combined.to_csv(filepath, index=True)
    logger.info(f"Saved correlation matrix to {filepath}")

def verify_correlation_matrix(filepath: Optional[str] = None):
    """Verify correlation matrix file exists and has expected content."""
    if filepath is None:
        project_root = get_project_root()
        filepath = project_root / "data" / "processed" / "correlation_matrix.csv"
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Correlation matrix file not found: {filepath}")
    
    df = pd.read_csv(filepath, index_col=0)
    if df.empty:
        raise ValueError("Correlation matrix is empty")
    
    expected_cols = [col for col in df.columns if col.startswith('pearson_') or col.startswith('spearman_')]
    if len(expected_cols) == 0:
        raise ValueError("Correlation matrix missing expected columns")
    
    logger.info(f"Verified correlation matrix: {len(expected_cols)} correlation columns found")

def calculate_vif(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Variance Inflation Factor for predictors.
    
    Excludes 'weighted mean radius' from calculation as per specification.
    Flags predictors with VIF > 5 for diagnostic review.
    """
    # Select numeric columns, excluding 'weighted mean radius'
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    exclude_cols = ['weighted mean radius']
    feature_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    if len(feature_cols) < 2:
        logger.warning("Less than 2 features available for VIF calculation")
        return pd.DataFrame()
    
    X = df[feature_cols].values
    
    # Add intercept for VIF calculation
    X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
    
    vif_data = []
    for i, col in enumerate(feature_cols):
        # VIF for feature i is 1 / (1 - R^2_i) where R^2_i is from regressing feature i on all other features
        # Using the formula: VIF = 1 / (1 - R^2) where R^2 is from the regression of that feature on others
        # Simple implementation: VIF = 1 / (1 - r^2) where r is correlation with others? No, that's not correct.
        
        # Correct approach: regress feature i on all other features
        y = X[:, i]
        X_others = np.column_stack([X[:, j] for j in range(X.shape[1]) if j != i])
        X_others_with_intercept = np.column_stack([np.ones(X_others.shape[0]), X_others])
        
        # OLS regression
        try:
            beta = np.linalg.lstsq(X_others_with_intercept, y, rcond=None)[0]
            y_pred = X_others_with_intercept @ beta
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            vif = 1 / (1 - r_squared) if (1 - r_squared) > 1e-10 else np.inf
        except np.linalg.LinAlgError:
            vif = np.inf
        
        vif_data.append({
            'feature': col,
            'VIF': vif,
            'flagged': vif > 5
        })
    
    vif_df = pd.DataFrame(vif_data)
    return vif_df

def save_vif_diagnostic_log(vif_df: pd.DataFrame, filepath: Optional[str] = None):
    """Save VIF diagnostic log to JSON."""
    if filepath is None:
        project_root = get_project_root()
        filepath = project_root / "data" / "processed" / "vif_diagnostic_log.json"
    
    result = {
        'vif_values': vif_df.to_dict(orient='records'),
        'flagged_features': vif_df[vif_df['flagged']]['feature'].tolist()
    }
    
    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved VIF diagnostic log to {filepath}")

def calculate_condition_number(df: pd.DataFrame) -> float:
    """Calculate the collinearity condition number for predictors.
    
    This supplements VIF analysis by providing a global measure of 
    multicollinearity in the design matrix.
    
    Args:
        df: DataFrame containing predictor variables.
        
    Returns:
        Condition number of the design matrix (ratio of largest to smallest singular value).
    """
    # Select numeric columns, excluding target variables if any
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < 2:
        logger.warning("Less than 2 numeric columns for condition number calculation")
        return float('inf')
    
    X = df[numeric_cols].values
    
    # Add intercept column for design matrix
    X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
    
    # Calculate singular values
    try:
        _, s, _ = np.linalg.svd(X_with_intercept, full_matrices=False)
        
        # Condition number is ratio of largest to smallest singular value
        if s[-1] < 1e-10:
            condition_number = float('inf')
        else:
            condition_number = s[0] / s[-1]
        
        return condition_number
    except np.linalg.LinAlgError:
        logger.error("SVD failed during condition number calculation")
        return float('inf')

def log_collinearity_analysis(df: pd.DataFrame, filepath: Optional[str] = None):
    """Perform and log collinearity analysis including VIF and condition number.
    
    This function supplements VIF analysis with the condition number to provide
    a comprehensive view of multicollinearity in the predictors.
    
    Args:
        df: DataFrame containing predictor variables.
        filepath: Optional path to save the analysis log. Defaults to 
                 data/processed/collinearity_diagnostic_log.json
    """
    logger.info("Starting collinearity analysis...")
    
    # Calculate VIF
    vif_df = calculate_vif(df)
    logger.info(f"VIF calculation complete. {len(vif_df)} features analyzed.")
    
    # Calculate condition number
    condition_number = calculate_condition_number(df)
    logger.info(f"Condition number: {condition_number:.4f}")
    
    # Interpret condition number
    if condition_number < 10:
        interpretation = "No multicollinearity"
    elif condition_number < 30:
        interpretation = "Moderate multicollinearity"
    elif condition_number < 100:
        interpretation = "Strong multicollinearity"
    else:
        interpretation = "Severe multicollinearity"
    
    logger.info(f"Multicollinearity interpretation: {interpretation}")
    
    # Prepare diagnostic log
    diagnostic_log = {
        'condition_number': condition_number,
        'interpretation': interpretation,
        'vif_summary': {
            'total_features': len(vif_df),
            'flagged_count': len(vif_df[vif_df['flagged']]),
            'flagged_features': vif_df[vif_df['flagged']]['feature'].tolist()
        },
        'vif_details': vif_df.to_dict(orient='records')
    }
    
    # Save to file
    if filepath is None:
        project_root = get_project_root()
        filepath = project_root / "data" / "processed" / "collinearity_diagnostic_log.json"
    
    with open(filepath, 'w') as f:
        json.dump(diagnostic_log, f, indent=2)
    
    logger.info(f"Collinearity analysis log saved to {filepath}")
    return diagnostic_log

def main():
    """Main entry point for collinearity analysis."""
    try:
        # Load descriptors
        df = load_descriptors()
        
        # Perform collinearity analysis
        log_collinearity_analysis(df)
        
        logger.info("Collinearity analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during collinearity analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main()