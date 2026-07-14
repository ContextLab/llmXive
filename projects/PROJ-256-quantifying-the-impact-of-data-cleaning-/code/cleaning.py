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
    Rows with values outside [Q1 - k*IQR, Q3 + k*IQR] are removed.
    """
    original_len = len(df)
    cleaned_df = df.copy()

    # Identify numerical columns
    numerical_cols = cleaned_df.select_dtypes(include=[np.number]).columns

    mask = pd.Series([True] * len(cleaned_df), index=cleaned_df.index)

    for col in numerical_cols:
        Q1 = cleaned_df[col].quantile(0.25)
        Q3 = cleaned_df[col].quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR

        col_mask = (cleaned_df[col] >= lower_bound) & (cleaned_df[col] <= upper_bound)
        mask &= col_mask

    cleaned_df = cleaned_df[mask]
    rows_removed = original_len - len(cleaned_df)
    removal_rate = rows_removed / original_len if original_len > 0 else 0.0

    logger.info(f"IQR outlier removal (k={k}): removed {rows_removed} rows ({removal_rate:.2%})")

    if removal_rate >= 0.5:
        logger.warning(f"Bias warning: {removal_rate:.2%} of rows removed. This may introduce bias.")

    return cleaned_df

def apply_mean_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Apply mean imputation to specified columns.
    If columns is None, apply to all numerical columns with missing values.
    """
    df_imputed = df.copy()

    if columns is None:
        # Find numerical columns with missing values
        columns = [col for col in df_imputed.select_dtypes(include=[np.number]).columns
                  if df_imputed[col].isnull().any()]

    for col in columns:
        if df_imputed[col].isnull().any():
            mean_val = df_imputed[col].mean()
            df_imputed[col] = df_imputed[col].fillna(mean_val)
            logger.info(f"Mean imputation for {col}: replaced {df[col].isnull().sum()} missing values with {mean_val:.4f}")

    # Validate zero missing values
    missing_after = df_imputed[columns].isnull().sum().sum()
    if missing_after > 0:
        logger.warning(f"Mean imputation: {missing_after} missing values remain after imputation")

    return df_imputed

def apply_median_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Apply median imputation to specified columns.
    If columns is None, apply to all numerical columns with missing values.
    """
    df_imputed = df.copy()

    if columns is None:
        columns = [col for col in df_imputed.select_dtypes(include=[np.number]).columns
                  if df_imputed[col].isnull().any()]

    for col in columns:
        if df_imputed[col].isnull().any():
            median_val = df_imputed[col].median()
            df_imputed[col] = df_imputed[col].fillna(median_val)
            logger.info(f"Median imputation for {col}: replaced {df[col].isnull().sum()} missing values with {median_val:.4f}")

    # Validate zero missing values
    missing_after = df_imputed[columns].isnull().sum().sum()
    if missing_after > 0:
        logger.warning(f"Median imputation: {missing_after} missing values remain after imputation")

    return df_imputed

def apply_knn_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None, k: int = 5) -> pd.DataFrame:
    """
    Apply KNN imputation to specified columns using scikit-learn.
    If columns is None, apply to all numerical columns with missing values.
    """
    df_imputed = df.copy()

    if columns is None:
        columns = [col for col in df_imputed.select_dtypes(include=[np.number]).columns
                  if df_imputed[col].isnull().any()]

    if not columns:
        logger.info("No numerical columns with missing values found. Skipping KNN imputation.")
        return df_imputed

    # Extract the columns to impute
    X = df_imputed[columns].values

    # Initialize KNN imputer
    imputer = KNNImputer(n_neighbors=k)
    X_imputed = imputer.fit_transform(X)

    # Update the DataFrame
    for i, col in enumerate(columns):
        df_imputed[col] = X_imputed[:, i]

    # Validate zero missing values
    missing_after = df_imputed[columns].isnull().sum().sum()
    if missing_after > 0:
        logger.warning(f"KNN imputation: {missing_after} missing values remain after imputation")

    logger.info(f"KNN imputation (k={k}) applied to {len(columns)} columns")

    return df_imputed

def apply_categorical_recoding(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply categorical recoding (label encoding) to categorical columns.
    This is useful for statistical testing where categorical variables need to be numeric.
    """
    df_recoded = df.copy()
    categorical_cols = df_recoded.select_dtypes(include=['object', 'category']).columns

    encoder = LabelEncoder()
    for col in categorical_cols:
        df_recoded[col] = encoder.fit_transform(df_recoded[col].astype(str))
        logger.info(f"Categorical recoding for {col}: {df[col].nunique()} unique categories")

    return df_recoded

def main():
    """Main entry point for testing cleaning functions."""
    # Create a sample DataFrame
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5, 100],  # 100 is an outlier
        'B': [2, 4, np.nan, 8, 10, 12],
        'C': ['x', 'y', 'x', 'y', 'x', 'z']
    })

    print("Original DataFrame:")
    print(df)

    # Test IQR outlier removal
    df_cleaned = apply_iqr_outlier_removal(df, k=1.5)
    print("\nAfter IQR outlier removal:")
    print(df_cleaned)

    # Test mean imputation
    df_imputed = apply_mean_imputation(df, columns=['B'])
    print("\nAfter mean imputation:")
    print(df_imputed)

    # Test categorical recoding
    df_recoded = apply_categorical_recoding(df)
    print("\nAfter categorical recoding:")
    print(df_recoded)

if __name__ == "__main__":
    main()
