"""
T016c: Standard scaling for numeric features.
"""
import logging
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

def apply_scaling(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies StandardScaler to numeric columns.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if numeric_cols.empty:
        logger.warning("No numeric columns found for scaling.")
        return df

    logger.info(f"Scaling {len(numeric_cols)} numeric columns.")
    
    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    
    logger.info("Scaling completed.")
    return df
