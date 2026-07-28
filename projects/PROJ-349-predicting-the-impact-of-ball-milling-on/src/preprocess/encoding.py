"""
T016b: One-hot encoding for material_type.
"""
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def apply_one_hot(df: pd.DataFrame) -> pd.DataFrame:
    """
    One-hot encodes the 'material_type' column.
    """
    if 'material_type' not in df.columns:
        logger.warning("'material_type' column not found. Skipping one-hot encoding.")
        return df

    logger.info("Applying one-hot encoding to 'material_type'.")
    df_encoded = pd.get_dummies(df, columns=['material_type'], drop_first=False)
    
    logger.info(f"One-hot encoding completed. New columns: {list(df_encoded.columns)}")
    return df_encoded
