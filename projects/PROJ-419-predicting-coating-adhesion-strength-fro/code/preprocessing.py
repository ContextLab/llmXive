import os
import sys
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_processed_data(file_path: str) -> pd.DataFrame:
    """
    Load the processed dataset from a CSV file.
    
    Args:
        file_path (str): Path to the CSV file.
        
    Returns:
        pd.DataFrame: Loaded dataset.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Processed data file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns from {file_path}")
    return df

def calculate_correlation(series1: pd.Series, series2: pd.Series) -> float:
    """
    Calculate Pearson correlation between two series.
    
    Args:
        series1 (pd.Series): First series.
        series2 (pd.Series): Second series.
        
    Returns:
        float: Correlation coefficient.
    """
    return series1.corr(series2)

def calculate_r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate R-squared value.
    
    Args:
        y_true (np.ndarray): True values.
        y_pred (np.ndarray): Predicted values.
        
    Returns:
        float: R-squared value.
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot)

def perform_construct_validity_check(df: pd.DataFrame, proxy_cols: List[str], target_col: str) -> pd.DataFrame:
    """
    Perform construct validity check on derived proxies.
    
    Args:
        df (pd.DataFrame): Dataset.
        proxy_cols (List[str]): List of proxy column names.
        target_col (str): Target column name.
        
    Returns:
        pd.DataFrame: Validation report.
    """
    report_data = []
    for proxy in proxy_cols:
        if proxy not in df.columns or target_col not in df.columns:
            logger.warning(f"Proxy '{proxy}' or target '{target_col}' not found in dataset. Skipping.")
            continue
        
        valid_data = df[[proxy, target_col]].dropna()
        if len(valid_data) < 2:
            logger.warning(f"Not enough valid data points for proxy '{proxy}'. Skipping.")
            continue
        
        corr = calculate_correlation(valid_data[proxy], valid_data[target_col])
        # Simple linear regression for R^2
        X = valid_data[[proxy]].values
        y = valid_data[target_col].values
        # Fit line
        slope, intercept = np.polyfit(X.flatten(), y, 1)
        y_pred = slope * X.flatten() + intercept
        r_sq = calculate_r_squared(y, y_pred)
        
        status = "PASS" if (abs(corr) >= 0.3 and r_sq >= 0.05) else "EXCLUDED"
        
        report_data.append({
            "proxy_name": proxy,
            "correlation": corr,
            "r_squared": r_sq,
            "status": status
        })
        
        if status == "EXCLUDED":
            logger.error(f"Proxy '{proxy}' failed construct validity check (|r|={abs(corr):.3f}, R²={r_sq:.3f}). HALTING PIPELINE.")
            # In a real pipeline, this would raise an exception or set a halt signal
            raise ValueError(f"Construct validity check failed for proxy '{proxy}'. Pipeline halted.")
    
    report_df = pd.DataFrame(report_data)
    return report_df

def encode_compositional_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode compositional data: one-hot encoding, atomic radius variance, crosslinker density proxy.
    Adheres to T009 interface.
    
    Args:
        df (pd.DataFrame): Input dataset.
        
    Returns:
        pd.DataFrame: Dataset with encoded compositional features.
    """
    logger.info("Encoding compositional data...")
    df_encoded = df.copy()
    
    # Identify categorical columns for one-hot encoding (example logic)
    # In a real scenario, we'd have specific columns defined in specs
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    # Exclude target and known non-compositional columns if any
    categorical_cols = [col for col in categorical_cols if col not in ['target_adhesion_strength', 'sample_id']]
    
    if categorical_cols:
        df_encoded = pd.get_dummies(df_encoded, columns=categorical_cols, drop_first=True)
        logger.info(f"One-hot encoded categorical columns: {categorical_cols}")
    
    # Example: Calculate atomic radius variance if 'atomic_radius' column exists
    if 'atomic_radius' in df_encoded.columns:
        # Assuming atomic_radius is a list or string representation of list in some cells
        # For simplicity, if it's numeric, variance is 0 for single value, or calculate if multiple
        # This is a placeholder for complex logic that would depend on data schema
        if df_encoded['atomic_radius'].apply(lambda x: isinstance(x, (list, np.ndarray))).any():
            df_encoded['atomic_radius_variance'] = df_encoded['atomic_radius'].apply(
                lambda x: np.var(x) if isinstance(x, (list, np.ndarray)) else 0.0
            )
        else:
            df_encoded['atomic_radius_variance'] = 0.0 # Single value per sample
        logger.info("Calculated atomic_radius_variance")
    
    # Example: Crosslinker density proxy
    if 'crosslinker_concentration' in df_encoded.columns and 'curing_time' in df_encoded.columns:
        df_encoded['crosslinker_density_proxy'] = df_encoded['crosslinker_concentration'] * df_encoded['curing_time']
        logger.info("Calculated crosslinker_density_proxy")
    
    return df_encoded

def standardize_surface_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize surface metrics (RMS, skewness, kurtosis) adhering to T009 interface.
    Uses Z-score standardization (mean=0, std=1) for each metric column.
    
    Args:
        df (pd.DataFrame): Input dataset with surface metric columns.
        
    Returns:
        pd.DataFrame: Dataset with standardized surface metrics.
    """
    logger.info("Standardizing surface metrics...")
    df_standardized = df.copy()
    
    # Identify surface metric columns based on common naming conventions or specs
    # Assuming columns like 'surface_rms', 'surface_skewness', 'surface_kurtosis' exist
    surface_metric_cols = [col for col in df_standardized.columns if 'surface_' in col.lower() and col.lower() in ['surface_rms', 'surface_skewness', 'surface_kurtosis']]
    
    # If specific columns are not found, try to infer from data types or other patterns
    # This is a robust fallback, but the primary expectation is explicit column names
    if not surface_metric_cols:
        # Fallback: look for columns with 'rms', 'skew', 'kurt' in name
        surface_metric_cols = [col for col in df_standardized.columns if any(k in col.lower() for k in ['rms', 'skew', 'kurt'])]
    
    if not surface_metric_cols:
        logger.warning("No surface metric columns found to standardize. Returning original dataframe.")
        return df_standardized
    
    logger.info(f"Found surface metric columns to standardize: {surface_metric_cols}")
    
    for col in surface_metric_cols:
        if df_standardized[col].dtype not in [np.float64, np.float32, np.int64, np.int32]:
            logger.warning(f"Column '{col}' is not numeric. Skipping standardization.")
            continue
        
        mean_val = df_standardized[col].mean()
        std_val = df_standardized[col].std()
        
        if std_val == 0 or np.isnan(std_val):
            logger.warning(f"Standard deviation for '{col}' is zero or NaN. Setting standardized values to 0.")
            df_standardized[col + '_standardized'] = 0.0
        else:
            df_standardized[col + '_standardized'] = (df_standardized[col] - mean_val) / std_val
            logger.info(f"Standardized '{col}' (mean={mean_val:.4f}, std={std_val:.4f})")
    
    return df_standardized

def create_preprocessing_pipeline(df: pd.DataFrame, proxy_cols: List[str], target_col: str) -> pd.DataFrame:
    """
    Create a full preprocessing pipeline: construct validity check, compositional encoding, surface standardization.
    
    Args:
        df (pd.DataFrame): Input dataset.
        proxy_cols (List[str]): List of proxy column names for validity check.
        target_col (str): Target column name.
        
    Returns:
        pd.DataFrame: Fully preprocessed dataset.
    """
    logger.info("Starting full preprocessing pipeline...")
    
    # 1. Construct Validity Check (this will halt if any proxy fails)
    try:
        validity_report = perform_construct_validity_check(df, proxy_cols, target_col)
        logger.info("Construct validity check passed.")
        logger.debug(f"Validity report:\n{validity_report}")
    except ValueError as e:
        logger.critical(f"Pipeline halted due to construct validity failure: {e}")
        raise # Re-raise to halt the main process
    
    # 2. Encode Compositional Data
    df_processed = encode_compositional_data(df)
    
    # 3. Standardize Surface Metrics
    df_processed = standardize_surface_metrics(df_processed)
    
    logger.info("Preprocessing pipeline completed successfully.")
    return df_processed

def main():
    """
    Main entry point for preprocessing script.
    Expects command line arguments or environment variables for file paths.
    For this task, we assume the dataset is already at 'data/processed/coating_adhesion_dataset.csv'
    and we output to 'data/processed/coating_adhesion_dataset_processed.csv'.
    """
    input_path = "data/processed/coating_adhesion_dataset.csv"
    output_path = "data/processed/coating_adhesion_dataset_processed.csv"
    
    # Proxy columns and target column names (should be configurable)
    proxy_cols = ['surface_rms', 'surface_skewness', 'surface_kurtosis'] # Example proxies
    target_col = 'target_adhesion_strength'
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}. Please run ingestion first.")
        sys.exit(1)
    
    try:
        df = load_processed_data(input_path)
        df_processed = create_preprocessing_pipeline(df, proxy_cols, target_col)
        
        df_processed.to_csv(output_path, index=False)
        logger.info(f"Preprocessed dataset saved to {output_path}")
        
    except Exception as e:
        logger.critical(f"Preprocessing pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()