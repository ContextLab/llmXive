import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.impute import KNNImputer

logger = logging.getLogger(__name__)

def apply_iqr_outlier_removal(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    """
    Remove outliers based on IQR method.
    Outliers are values < Q1 - k*IQR or > Q3 + k*IQR.
    """
    df_clean = df.copy()
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    
    removed_rows = 0
    mask = pd.Series([True] * len(df_clean), index=df_clean.index)
    
    for col in numeric_cols:
        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR
        
        col_mask = (df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)
        mask &= col_mask
    
    removed_rows = len(df_clean) - mask.sum()
    df_clean = df_clean[mask]
    
    if removed_rows > 0:
        logger.info(f"Removed {removed_rows} rows ({removed_rows/len(df)*100:.1f}%) using IQR k={k}")
        if removed_rows / len(df) >= 0.5:
            logger.warning(f"High row removal ({removed_rows/len(df)*100:.1f}%) for k={k}. Potential bias.")
    
    return df_clean

def apply_mean_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    df_imp = df.copy()
    if columns is None:
        columns = df_imp.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col in df_imp.columns:
            mean_val = df_imp[col].mean()
            df_imp[col].fillna(mean_val, inplace=True)
    
    logger.info(f"Applied mean imputation to {len(columns)} columns")
    return df_imp

def apply_median_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    df_imp = df.copy()
    if columns is None:
        columns = df_imp.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col in df_imp.columns:
            median_val = df_imp[col].median()
            df_imp[col].fillna(median_val, inplace=True)
    
    logger.info(f"Applied median imputation to {len(columns)} columns")
    return df_imp

def apply_knn_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None, k: int = 5) -> pd.DataFrame:
    df_imp = df.copy()
    if columns is None:
        columns = df_imp.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(columns) == 0:
        return df_imp
    
    imputer = KNNImputer(n_neighbors=k)
    df_imp[columns] = imputer.fit_transform(df_imp[columns])
    
    logger.info(f"Applied KNN imputation (k={k}) to {len(columns)} columns")
    return df_imp

def apply_categorical_recoding(df: pd.DataFrame) -> pd.DataFrame:
    df_rec = df.copy()
    cat_cols = df_rec.select_dtypes(include=['object']).columns
    
    for col in cat_cols:
        le = LabelEncoder()
        df_rec[col] = le.fit_transform(df_rec[col].astype(str))
    
    logger.info(f"Recoded {len(cat_cols)} categorical columns")
    return df_rec

from sklearn.preprocessing import LabelEncoder
