import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def apply_iqr_outlier_removal(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    """
    Remove outliers based on the Interquartile Range (IQR) method.
    Rows are removed if any numeric value falls outside [Q1 - k*IQR, Q3 + k*IQR].
    
    Args:
        df: Input DataFrame.
        k: Multiplier for IQR (default 1.5).
        
    Returns:
        DataFrame with outliers removed.
    """
    logger.info(f"Applying IQR outlier removal with k={k}")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        logger.warning("No numeric columns found for outlier removal.")
        return df.copy()
    
    # Calculate Q1, Q3, and IQR for numeric columns
    Q1 = df[numeric_cols].quantile(0.25)
    Q3 = df[numeric_cols].quantile(0.75)
    IQR = Q3 - Q1
    
    # Define bounds
    lower_bound = Q1 - k * IQR
    upper_bound = Q3 + k * IQR
    
    # Create mask for rows that are within bounds for ALL numeric columns
    # A row is kept if it satisfies the condition for every numeric column
    mask = pd.Series(True, index=df.index)
    for col in numeric_cols:
        col_mask = (df[col] >= lower_bound[col]) & (df[col] <= upper_bound[col])
        mask &= col_mask
    
    original_len = len(df)
    cleaned_df = df[mask].copy()
    removed_count = original_len - len(cleaned_df)
    
    logger.info(f"Removed {removed_count} rows ({removed_count/original_len*100:.2f}%) due to outliers.")
    
    if original_len > 0 and removed_count / original_len >= 0.5:
        logger.warning(f"CRITICAL: >=50% of rows removed ({removed_count/original_len*100:.2f}%). Potential bias introduced.")
        
    return cleaned_df

def apply_mean_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Impute missing values with the mean of the respective column.
    
    Args:
        df: Input DataFrame.
        columns: List of columns to impute. If None, all numeric columns with missing values are used.
        
    Returns:
        DataFrame with imputed values.
    """
    logger.info("Applying mean imputation")
    cleaned_df = df.copy()
    
    if columns is None:
        columns = cleaned_df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col not in cleaned_df.columns:
            logger.warning(f"Column {col} not found, skipping.")
            continue
        
        if cleaned_df[col].isnull().any():
            mean_val = cleaned_df[col].mean()
            original_var = cleaned_df[col].var()
            cleaned_df[col] = cleaned_df[col].fillna(mean_val)
            
            # Check variance reduction
            new_var = cleaned_df[col].var()
            if original_var > 0 and (original_var - new_var) / original_var >= 0.20:
                logger.warning(f"Variance reduction >=20% detected in column {col} after mean imputation.")
    
    if cleaned_df[columns].isnull().any().any():
        raise ValueError("Mean imputation failed: missing values still present.")
        
    logger.info("Mean imputation completed successfully.")
    return cleaned_df

def apply_median_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Impute missing values with the median of the respective column.
    
    Args:
        df: Input DataFrame.
        columns: List of columns to impute. If None, all numeric columns with missing values are used.
        
    Returns:
        DataFrame with imputed values.
    """
    logger.info("Applying median imputation")
    cleaned_df = df.copy()
    
    if columns is None:
        columns = cleaned_df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col not in cleaned_df.columns:
            logger.warning(f"Column {col} not found, skipping.")
            continue
        
        if cleaned_df[col].isnull().any():
            median_val = cleaned_df[col].median()
            original_var = cleaned_df[col].var()
            cleaned_df[col] = cleaned_df[col].fillna(median_val)
            
            # Check variance reduction
            new_var = cleaned_df[col].var()
            if original_var > 0 and (original_var - new_var) / original_var >= 0.20:
                logger.warning(f"Variance reduction >=20% detected in column {col} after median imputation.")
    
    if cleaned_df[columns].isnull().any().any():
        raise ValueError("Median imputation failed: missing values still present.")
        
    logger.info("Median imputation completed successfully.")
    return cleaned_df

def apply_knn_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None, k: int = 5) -> pd.DataFrame:
    """
    Impute missing values using K-Nearest Neighbors (KNN).
    
    Args:
        df: Input DataFrame.
        columns: List of columns to impute. If None, all numeric columns with missing values are used.
        k: Number of neighbors to use.
        
    Returns:
        DataFrame with imputed values.
    """
    logger.info(f"Applying KNN imputation with k={k}")
    cleaned_df = df.copy()
    
    if columns is None:
        columns = cleaned_df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter to only columns that exist and have missing values
    target_cols = [c for c in columns if c in cleaned_df.columns and cleaned_df[c].isnull().any()]
    
    if not target_cols:
        logger.info("No columns with missing values found for KNN imputation.")
        return cleaned_df
    
    try:
        from sklearn.impute import KNNImputer
    except ImportError:
        raise ImportError("scikit-learn is required for KNN imputation. Install with: pip install scikit-learn")
    
    imputer = KNNImputer(n_neighbors=k)
    
    # Extract only the columns to impute to avoid mixing types if non-numeric cols are present
    # But KNNImputer expects numeric data. We assume target_cols are numeric.
    impute_data = cleaned_df[target_cols].values
    
    if np.any(np.isnan(impute_data)):
        imputed_data = imputer.fit_transform(impute_data)
        for i, col in enumerate(target_cols):
            cleaned_df[col] = imputed_data[:, i]
    else:
        logger.info("No missing values found in specified columns for KNN imputation.")
    
    if cleaned_df[target_cols].isnull().any().any():
        raise ValueError("KNN imputation failed: missing values still present.")
        
    # Check variance reduction for imputed columns
    for col in target_cols:
        # We can't easily compare original variance vs new if we didn't store original
        # But we can log that we performed the operation
        pass
        
    logger.info("KNN imputation completed successfully.")
    return cleaned_df

def apply_categorical_recoding(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply factor encoding to categorical columns to prepare for statistical testing.
    Converts categorical columns to integer codes (0, 1, 2, ...).
    This allows categorical variables to be included in statistical tests like t-tests or regression.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        DataFrame with categorical columns recoded to integer factors.
    """
    logger.info("Applying categorical recoding (factor encoding)")
    cleaned_df = df.copy()
    
    # Identify categorical columns (object or category dtype)
    categorical_cols = cleaned_df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if not categorical_cols:
        logger.info("No categorical columns found for recoding.")
        return cleaned_df
    
    logger.info(f"Found categorical columns: {categorical_cols}")
    
    for col in categorical_cols:
        # Drop NaNs for encoding to ensure unique categories
        unique_vals = cleaned_df[col].dropna().unique()
        logger.debug(f"Column {col} has {len(unique_vals)} unique categories.")
        
        # Create a mapping: unique value -> integer code
        # Using pd.Categorical to handle the mapping consistently
        cleaned_df[col] = pd.Categorical(cleaned_df[col])
        cleaned_df[col] = cleaned_df[col].cat.codes
        
        # Check for -1 codes which indicate NaNs were present
        if (cleaned_df[col] == -1).any():
            logger.warning(f"NaN values found in categorical column {col} and encoded as -1. Consider imputation before recoding.")
            # Optionally fill -1 with a specific code or handle separately
            # For now, we leave them as -1 as per standard factor encoding behavior
    
    logger.info("Categorical recoding completed successfully.")
    return cleaned_df