import pandas as pd
import numpy as np
from typing import List, Optional, Tuple

class PowerError(Exception):
    """Raised when insufficient adopters remain after filtering."""
    pass

def filter_low_income(df: pd.DataFrame) -> pd.DataFrame:
    raise NotImplementedError("T016: Filter logic not implemented yet")

def winsorize(df: pd.DataFrame, lower: float = 0.01, upper: float = 0.99) -> pd.DataFrame:
    raise NotImplementedError("T017: Winsorization logic not implemented yet")

def construct_treatment(df: pd.DataFrame) -> pd.DataFrame:
    raise NotImplementedError("T016: Treatment construction logic not implemented yet")

def check_adopter_power(df: pd.DataFrame, min_adopters: int = 50) -> None:
    raise NotImplementedError("T018: Power check logic not implemented yet")

def _impute_missing_values(df: pd.DataFrame, continuous_cols: List[str], categorical_cols: List[str]) -> pd.DataFrame:
    """
    Internal helper to handle missing values.
    
    - Continuous variables: Median Imputation
    - Categorical variables: Fill with 'Missing' category
    
    Returns a copy of the dataframe with imputed values.
    """
    df_imputed = df.copy()
    
    # Track original missing counts for verification
    missing_before = {}
    for col in continuous_cols + categorical_cols:
        if col in df_imputed.columns:
            missing_before[col] = df_imputed[col].isna().sum()
    
    # Handle Continuous Variables (Median Imputation)
    for col in continuous_cols:
        if col in df_imputed.columns:
            if df_imputed[col].dtype in ['float64', 'int64', 'float32', 'int32']:
                median_val = df_imputed[col].median()
                if pd.isna(median_val):
                    # If all values are NaN, fill with 0 or raise? 
                    # For robustness, we fill with 0 if median is NaN (all missing)
                    median_val = 0.0
                df_imputed[col] = df_imputed[col].fillna(median_val)
            else:
                # If it's object/numeric but not standard int/float, try to convert or skip
                # For safety in this specific task, we assume standard numeric types
                pass
    
    # Handle Categorical Variables ('Missing' flag)
    for col in categorical_cols:
        if col in df_imputed.columns:
            # Ensure it's treated as object/string to allow 'Missing' string
            if df_imputed[col].dtype == 'object':
                df_imputed[col] = df_imputed[col].fillna('Missing')
            elif df_imputed[col].dtype.name == 'category':
                # For categorical dtype, add 'Missing' to categories first
                if 'Missing' not in df_imputed[col].cat.categories:
                    df_imputed[col] = df_imputed[col].cat.add_categories(['Missing'])
                df_imputed[col] = df_imputed[col].fillna('Missing')
            else:
                # Fallback for other types: convert to string then fill
                df_imputed[col] = df_imputed[col].astype(str).fillna('Missing')
    
    # Verification: Ensure no silent data loss (no NAs remain in targeted cols)
    for col in continuous_cols + categorical_cols:
        if col in df_imputed.columns:
            if df_imputed[col].isna().sum() > 0:
                raise ValueError(f"Silent data loss detected: Column '{col}' still has {df_imputed[col].isna().sum()} missing values after imputation.")
    
    return df_imputed

def preprocess_pipeline(
    df: pd.DataFrame,
    continuous_cols: Optional[List[str]] = None,
    categorical_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Main pipeline entry point for preprocessing, including missing value handling.
    
    This function:
    1. Identifies missing values.
    2. Applies Median Imputation for continuous variables.
    3. Applies 'Missing' category flag for categorical variables.
    4. Verifies no silent data loss remains in the specified columns.
    
    Args:
        df: Input DataFrame.
        continuous_cols: List of column names to treat as continuous (median imputation).
        categorical_cols: List of column names to treat as categorical ('Missing' flag).
        
    Returns:
        DataFrame with missing values handled.
        
    Raises:
        ValueError: If missing values remain in specified columns after imputation.
        PowerError: (Delegated to check_adopter_power if called within pipeline)
    """
    if continuous_cols is None:
        continuous_cols = []
    if categorical_cols is None:
        categorical_cols = []
        
    # Filter to only columns that exist in the dataframe
    valid_continuous = [c for c in continuous_cols if c in df.columns]
    valid_categorical = [c for c in categorical_cols if c in df.columns]
    
    if not valid_continuous and not valid_categorical:
        # No imputation needed if no columns specified or found
        return df
    
    # Perform Imputation
    df_clean = _impute_missing_values(df, valid_continuous, valid_categorical)
    
    return df_clean
