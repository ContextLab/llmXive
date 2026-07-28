"""
T016a: Multiple Imputation for missing values.
"""
import logging
import pandas as pd
import numpy as np
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer

logger = logging.getLogger(__name__)

def apply_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies IterativeImputer to all required predictors.
    
    Excludes targets: d10, d50, d90.
    """
    # Define predictors (exclude targets)
    target_cols = ['d10', 'd50', 'd90']
    predictor_cols = [col for col in df.columns if col not in target_cols]
    
    # Filter to numeric columns for imputation
    numeric_predictors = df[predictor_cols].select_dtypes(include=[np.number])
    
    if numeric_predictors.empty:
        logger.warning("No numeric predictor columns found for imputation.")
        return df

    logger.info(f"Applying imputation to {len(numeric_predictors.columns)} numeric predictors.")
    
    imputer = IterativeImputer(random_state=42, max_iter=10, tol=0.1)
    
    try:
        imputed_values = imputer.fit_transform(numeric_predictors)
        imputed_df = pd.DataFrame(imputed_values, columns=numeric_predictors.columns, index=df.index)
        
        # Reconstruct dataframe
        # Keep non-numeric columns (like material_type) as is
        non_numeric_cols = [col for col in df.columns if col not in numeric_predictors.columns]
        non_numeric_data = df[non_numeric_cols]
        
        # Combine
        result_df = pd.concat([imputed_df, non_numeric_data], axis=1)
        
        # Reorder columns to match original
        result_df = result_df[df.columns]
        
        logger.info("Imputation completed.")
        return result_df
    except Exception as e:
        logger.error(f"Imputation failed: {e}")
        raise e
