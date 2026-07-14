import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

def apply_iqr_outlier_removal(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    """
    Remove outliers based on the IQR method.
    Outliers are defined as points outside [Q1 - k*IQR, Q3 + k*IQR].
    """
    if df.empty:
        return df
    
    df_clean = df.copy()
    numerical_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numerical_cols:
        logger.warning("No numerical columns found for outlier removal.")
        return df_clean
    
    rows_removed = 0
    mask = pd.Series([True] * len(df_clean), index=df_clean.index)
    
    for col in numerical_cols:
        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR
        
        col_mask = (df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)
        mask &= col_mask
    
    rows_before = len(df_clean)
    df_clean = df_clean[mask]
    rows_removed = rows_before - len(df_clean)
    
    if rows_removed > 0:
        logger.info(f"Removed {rows_removed} rows ({rows_removed/rows_before*100:.2f}%) due to outliers (k={k}).")
        if rows_removed / rows_before >= 0.5:
            logger.warning(f"WARNING: >= 50% of rows removed. Potential bias introduced.")
    
    return df_clean


def apply_mean_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Apply mean imputation to specified columns.
    If columns is None, impute all numerical columns with missing values.
    """
    if df.empty:
        return df
    
    df_clean = df.copy()
    
    if columns is None:
        columns = df_clean.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col in df_clean.columns:
            mean_val = df_clean[col].mean()
            df_clean[col].fillna(mean_val, inplace=True)
            logger.info(f"Imputed missing values in '{col}' with mean {mean_val:.4f}.")
        
    # Validate zero missing values
    missing_counts = df_clean[columns].isnull().sum()
    if missing_counts.sum() > 0:
        logger.warning(f"Missing values still present after mean imputation: {missing_counts[missing_counts > 0].to_dict()}")
    
    return df_clean


def apply_median_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Apply median imputation to specified columns.
    """
    if df.empty:
        return df
    
    df_clean = df.copy()
    
    if columns is None:
        columns = df_clean.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col in df_clean.columns:
            median_val = df_clean[col].median()
            df_clean[col].fillna(median_val, inplace=True)
            logger.info(f"Imputed missing values in '{col}' with median {median_val:.4f}.")
    
    # Validate zero missing values
    missing_counts = df_clean[columns].isnull().sum()
    if missing_counts.sum() > 0:
        logger.warning(f"Missing values still present after median imputation: {missing_counts[missing_counts > 0].to_dict()}")
    
    return df_clean


def apply_knn_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None, k: int = 5) -> pd.DataFrame:
    """
    Apply KNN imputation to specified columns using scikit-learn.
    """
    if df.empty:
        return df
    
    df_clean = df.copy()
    
    if columns is None:
        columns = df_clean.select_dtypes(include=[np.number]).columns.tolist()
    
    if not columns:
        logger.warning("No numerical columns found for KNN imputation.")
        return df_clean
    
    # Extract only the columns to impute
    X = df_clean[columns].values
    
    imputer = KNNImputer(n_neighbors=k)
    X_imputed = imputer.fit_transform(X)
    
    df_clean[columns] = X_imputed
    logger.info(f"Applied KNN imputation (k={k}) to columns: {columns}")
    
    # Validate zero missing values
    missing_counts = df_clean[columns].isnull().sum()
    if missing_counts.sum() > 0:
        logger.warning(f"Missing values still present after KNN imputation: {missing_counts[missing_counts > 0].to_dict()}")
    
    return df_clean


def apply_categorical_recoding(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply label encoding to categorical columns for statistical testing.
    """
    if df.empty:
        return df
    
    df_clean = df.copy()
    categorical_cols = df_clean.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if not categorical_cols:
        logger.info("No categorical columns found for recoding.")
        return df_clean
    
    encoder = LabelEncoder()
    for col in categorical_cols:
        if df_clean[col].nunique() > 0:
            df_clean[col] = encoder.fit_transform(df_clean[col].astype(str))
            logger.info(f"Encoded categorical column '{col}' with {df_clean[col].nunique()} unique values.")
    
    return df_clean


def main():
    """Main entry point for direct execution."""
    logging.basicConfig(level=logging.INFO)
    # Example usage
    df = pd.DataFrame({
        'A': [1, 2, np.nan, 4, 5],
        'B': ['x', 'y', 'z', 'x', 'y']
    })
    print("Original:")
    print(df)
    print("\nAfter Mean Imputation:")
    print(apply_mean_imputation(df, ['A']))
    print("\nAfter Categorical Recoding:")
    print(apply_categorical_recoding(df))

if __name__ == "__main__":
    main()
