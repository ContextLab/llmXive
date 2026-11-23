from code.utils.constants import get_metallic_radius
from typing import Optional
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def calculate_size_mismatch(solute_symbol: str, host_symbol: str) -> float:
    """
    Calculate size_mismatch = (solute_r - host_r) / host_r
    using Metallic Radii from constants.py.
    """
    solute_r = get_metallic_radius(solute_symbol)
    host_r = get_metallic_radius(host_symbol)

    if solute_r is None or host_r is None:
        raise ValueError(f"Missing metallic radius for solute={solute_symbol} or host={host_symbol}")

    if host_r == 0:
        raise ValueError(f"Host radius is zero for {host_symbol}")

    return (solute_r - host_r) / host_r

def compute_descriptors_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute descriptors for the entire dataframe.
    Returns a DataFrame with features.
    """
    features = []
    for idx, row in df.iterrows():
        try:
            size_mismatch = calculate_size_mismatch(row['solute_symbol'], row['host_symbol'])
            features.append({'size_mismatch': size_mismatch})
        except ValueError as e:
            logger.warning(f"Skipping row {idx} due to descriptor calculation error: {e}")
            features.append({'size_mismatch': np.nan})

    feature_df = pd.DataFrame(features)
    return feature_df.dropna()
