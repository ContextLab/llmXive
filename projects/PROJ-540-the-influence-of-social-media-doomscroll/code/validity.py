import pandas as pd
import numpy as np
import logging
from typing import Union, List
from exceptions import MathematicalCouplingError

logger = logging.getLogger(__name__)

def check_construct_validity(df: pd.DataFrame) -> None:
    """
    Verify that baseline_anxiety and anxiety_score are distinct constructs.
    Raises MathematicalCouplingError if they are identical or perfectly correlated.
    """
    if 'baseline_anxiety' not in df.columns or 'anxiety_score' not in df.columns:
        logger.warning("Required columns for construct validity check not found. Skipping check.")
        return

    # Check for exact identity
    if df['baseline_anxiety'].equals(df['anxiety_score']):
        logger.error("Construct validity failed: baseline_anxiety and anxiety_score are identical.")
        raise MathematicalCouplingError("Mathematical coupling detected: 'baseline_anxiety' and 'anxiety_score' are identical columns.")

    # Check for perfect correlation (r = 1 or -1)
    clean_data = df[['baseline_anxiety', 'anxiety_score']].dropna()
    if len(clean_data) > 1:
        corr = clean_data['baseline_anxiety'].corr(clean_data['anxiety_score'])
        if np.isclose(abs(corr), 1.0):
            logger.error(f"Construct validity failed: Perfect correlation (r={corr}) between baseline_anxiety and anxiety_score.")
            raise MathematicalCouplingError(f"Mathematical coupling detected: Perfect correlation (r={corr}) between 'baseline_anxiety' and 'anxiety_score'.")
    
    logger.info("Construct validity check passed.")
    return None
