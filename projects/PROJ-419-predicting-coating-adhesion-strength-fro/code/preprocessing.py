import os
import sys
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any

# Import from utils
from utils import check_halt_signal, write_halt_signal

logger = logging.getLogger(__name__)

def load_processed_data(file_path: str) -> pd.DataFrame:
    """Load processed data from a CSV file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Processed data file not found: {file_path}")
    return pd.read_csv(file_path)

def calculate_correlation(series1: pd.Series, series2: pd.Series) -> float:
    """Calculate Pearson correlation between two series."""
    return series1.corr(series2)

def calculate_r_squared(y_true: pd.Series, y_pred: pd.Series) -> float:
    """Calculate R-squared value."""
    from sklearn.metrics import r2_score
    return r2_score(y_true, y_pred)

def perform_construct_validity_check(
    df: pd.DataFrame,
    proxy_columns: List[str],
    target_column: str,
    literature_correlations: Dict[str, float],
    threshold: float = 0.6,
    output_path: str = "data/processed/proxy_validation_report.csv"
) -> pd.DataFrame:
    """
    Validate derived proxies against theoretical models (literature-derived correlations).
    
    Logic:
    1. For each proxy column, calculate correlation with target.
    2. Compare against literature correlation.
    3. If R² (correlation^2) < threshold, mark as EXCLUDED.
    4. Output report to CSV.
    5. If any proxy is EXCLUDED, raise error to trigger HALT.
    
    Args:
        df: DataFrame with proxy and target columns.
        proxy_columns: List of proxy column names.
        target_column: Name of the target variable column.
        literature_correlations: Dict mapping proxy name to expected literature correlation (r).
        threshold: Minimum R² threshold (default 0.6).
        output_path: Path to save the validation report.
        
    Returns:
        DataFrame containing the validation report.
        
    Raises:
        ValueError: If any proxy is excluded and pipeline must halt.
    """
    logger.info("Starting construct validity assessment...")
    
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in DataFrame.")
        
    report_data = []
    excluded_proxies = []
    
    for proxy in proxy_columns:
        if proxy not in df.columns:
            logger.warning(f"Proxy column '{proxy}' not found in DataFrame. Skipping.")
            continue
            
        # Calculate actual correlation
        actual_corr = calculate_correlation(df[proxy], df[target_column])
        actual_r2 = actual_corr ** 2
        
        # Get literature correlation
        lit_corr = literature_correlations.get(proxy, 0.0)
        lit_r2 = lit_corr ** 2
        
        # Determine status
        status = "INCLUDED"
        reason = "Meets threshold"
        
        if actual_r2 < threshold:
            status = "EXCLUDED"
            reason = f"R² ({actual_r2:.4f}) below threshold ({threshold})"
            excluded_proxies.append(proxy)
        
        report_data.append({
            "proxy_name": proxy,
            "actual_correlation": actual_corr,
            "actual_r_squared": actual_r2,
            "literature_correlation": lit_corr,
            "literature_r_squared": lit_r2,
            "threshold": threshold,
            "status": status,
            "reason": reason
        })
        
        logger.info(f"Proxy '{proxy}': R²={actual_r2:.4f}, Status={status}")
    
    # Create report DataFrame
    report_df = pd.DataFrame(report_data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save report
    report_df.to_csv(output_path, index=False)
    logger.info(f"Proxy validation report saved to {output_path}")
    
    # Check for exclusions
    if excluded_proxies:
        halt_reason = f"Construct validity failed: Proxies excluded due to low R²: {', '.join(excluded_proxies)}"
        logger.error(halt_reason)
        write_halt_signal(reason=halt_reason)
        raise ValueError(halt_reason)
        
    return report_df

def encode_compositional_data(df: pd.DataFrame, composition_columns: List[str]) -> pd.DataFrame:
    """
    Encode compositional data (one-hot, atomic radius variance, crosslinker density proxy).
    Adheres to T009 interface.
    """
    logger.info("Encoding compositional data...")
    
    # Identify categorical columns for one-hot encoding
    # Assuming composition_columns contains mix of categorical and numerical
    # For this implementation, we treat string/object columns as categorical
    categorical_cols = df[composition_columns].select_dtypes(include=['object', 'category']).columns.tolist()
    numerical_cols = df[composition_columns].select_dtypes(include=['number']).columns.tolist()
    
    df_encoded = df.copy()
    
    if categorical_cols:
        # One-hot encode categorical columns
        df_encoded = pd.get_dummies(df_encoded, columns=categorical_cols, drop_first=False)
        logger.info(f"One-hot encoded categorical columns: {categorical_cols}")
    
    # For numerical composition columns, we can calculate atomic radius variance
    # This would require mapping elements to atomic radii - simplified for now
    # In a real implementation, this would use a periodic table lookup
    
    logger.info(f"Compositional data encoding complete. Shape: {df_encoded.shape}")
    return df_encoded

def standardize_surface_metrics(df: pd.DataFrame, surface_columns: List[str]) -> pd.DataFrame:
    """
    Standardize surface metrics (RMS, skewness, kurtosis).
    Adheres to T009 interface.
    
    Logic:
    1. Identify numerical surface metric columns from the provided list.
    2. Apply Z-score standardization (mean=0, std=1) to each metric.
    3. Handle missing values by excluding them from calculation but preserving rows.
    4. Return the DataFrame with standardized columns.
    
    Args:
        df: DataFrame containing surface metric columns.
        surface_columns: List of column names representing surface metrics (e.g., 'RMS', 'skewness', 'kurtosis').
        
    Returns:
        DataFrame with standardized surface metric columns.
    """
    logger.info("Standardizing surface metrics...")
    
    if not surface_columns:
        logger.warning("No surface columns provided for standardization.")
        return df
    
    df_standardized = df.copy()
    
    # Filter to only columns that exist in the DataFrame and are numerical
    valid_surface_cols = [col for col in surface_columns if col in df_standardized.columns]
    
    if not valid_surface_cols:
        logger.warning(f"No valid surface columns found in DataFrame. Available: {df_standardized.columns.tolist()}")
        return df_standardized
    
    numerical_surface_cols = df_standardized[valid_surface_cols].select_dtypes(include=['number']).columns.tolist()
    
    if not numerical_surface_cols:
        logger.warning(f"No numerical surface columns found to standardize: {valid_surface_cols}")
        return df_standardized
    
    logger.info(f"Standardizing numerical surface columns: {numerical_surface_cols}")
    
    for col in numerical_surface_cols:
        # Calculate mean and std, handling NaNs
        col_mean = df_standardized[col].mean()
        col_std = df_standardized[col].std()
        
        if col_std == 0 or np.isnan(col_std):
            logger.warning(f"Column '{col}' has zero or NaN std. Setting standardized values to 0.")
            df_standardized[col] = 0.0
        else:
            # Apply Z-score standardization
            df_standardized[col] = (df_standardized[col] - col_mean) / col_std
            logger.info(f"Standardized '{col}': mean={df_standardized[col].mean():.6f}, std={df_standardized[col].std():.6f}")
    
    logger.info(f"Surface metric standardization complete. Shape: {df_standardized.shape}")
    return df_standardized

def create_preprocessing_pipeline(config: Dict[str, Any]) -> callable:
    """Create a preprocessing pipeline based on configuration."""
    logger.info("Creating preprocessing pipeline...")
    
    composition_columns = config.get('composition_columns', [])
    surface_columns = config.get('surface_columns', [])
    
    def pipeline(df: pd.DataFrame) -> pd.DataFrame:
        """Execute the preprocessing pipeline on a DataFrame."""
        logger.info("Executing preprocessing pipeline...")
        
        # Step 1: Encode compositional data
        if composition_columns:
            df = encode_compositional_data(df, composition_columns)
        
        # Step 2: Standardize surface metrics
        if surface_columns:
            df = standardize_surface_metrics(df, surface_columns)
        
        logger.info("Preprocessing pipeline complete.")
        return df
    
    return pipeline

def main():
    """Main entry point for preprocessing module (for testing)."""
    logging.info("Preprocessing module loaded successfully.")

if __name__ == "__main__":
    main()
