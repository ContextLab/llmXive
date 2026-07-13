import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.impute import KNNImputer

logger = logging.getLogger(__name__)

def apply_iqr_outlier_removal(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    """
    Remove outliers based on IQR method.
    """
    logger.info(f"Applying IQR outlier removal with k={k}")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    cleaned_df = df.copy()

    removed_count = 0
    for col in numeric_cols:
        Q1 = cleaned_df[col].quantile(0.25)
        Q3 = cleaned_df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR
        mask = (cleaned_df[col] >= lower_bound) & (cleaned_df[col] <= upper_bound)
        cleaned_df = cleaned_df[mask]
    
    removed_count = len(df) - len(cleaned_df)
    logger.info(f"Removed {removed_count} rows due to outliers.")

    if removed_count >= len(df) * 0.5:
        logger.warning(f"Removed >= 50% of rows ({removed_count}/{len(df)}). Potential bias introduced.")

    return cleaned_df

def apply_mean_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Apply mean imputation for missing values.
    """
    logger.info("Applying mean imputation")
    cleaned_df = df.copy()
    if columns is None:
        columns = cleaned_df.select_dtypes(include=[np.number]).columns

    for col in columns:
        if cleaned_df[col].isnull().any():
            mean_val = cleaned_df[col].mean()
            cleaned_df[col] = cleaned_df[col].fillna(mean_val)
            logger.info(f"Imputed {col} with mean: {mean_val}")

    if cleaned_df.isnull().any().any():
        logger.warning("Mean imputation did not resolve all missing values.")
    else:
        logger.info("Mean imputation complete: zero missing values in target columns.")

    return cleaned_df

def apply_median_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Apply median imputation for missing values.
    """
    logger.info("Applying median imputation")
    cleaned_df = df.copy()
    if columns is None:
        columns = cleaned_df.select_dtypes(include=[np.number]).columns

    for col in columns:
        if cleaned_df[col].isnull().any():
            median_val = cleaned_df[col].median()
            cleaned_df[col] = cleaned_df[col].fillna(median_val)
            logger.info(f"Imputed {col} with median: {median_val}")

    if cleaned_df.isnull().any().any():
        logger.warning("Median imputation did not resolve all missing values.")
    else:
        logger.info("Median imputation complete: zero missing values in target columns.")

    return cleaned_df

def apply_knn_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None, k: int = 5) -> pd.DataFrame:
    """
    Apply KNN imputation for missing values.
    """
    logger.info(f"Applying KNN imputation with k={k}")
    cleaned_df = df.copy()
    if columns is None:
        columns = cleaned_df.select_dtypes(include=[np.number]).columns

    if len(columns) == 0:
        logger.warning("No numeric columns found for KNN imputation.")
        return cleaned_df

    imputer = KNNImputer(n_neighbors=k)
    cleaned_df[columns] = imputer.fit_transform(cleaned_df[columns])

    if cleaned_df.isnull().any().any():
        logger.warning("KNN imputation did not resolve all missing values.")
    else:
        logger.info("KNN imputation complete: zero missing values in target columns.")

    return cleaned_df

def apply_categorical_recoding(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recode categorical variables using factor encoding.
    """
    logger.info("Applying categorical recoding")
    cleaned_df = df.copy()
    cat_cols = cleaned_df.select_dtypes(include=['object', 'category']).columns

    for col in cat_cols:
        cleaned_df[col] = cleaned_df[col].astype('category').cat.codes
        logger.info(f"Factor encoded {col}")

    return cleaned_df
