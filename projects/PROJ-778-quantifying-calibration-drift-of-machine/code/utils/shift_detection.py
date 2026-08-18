"""
Shift Detection Utilities.

Implements BIC-based change-point detection using the ruptures library.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Union
from statsmodels.regression.linear_model import WLS
from statsmodels.tools import add_constant
import ruptures as rpt

import logging
logger = logging.getLogger(__name__)


def detect_change_point_bic(
    metrics: List[float], 
    alpha: float = 0.05, 
    years: Optional[List[int]] = None
) -> Optional[int]:
    """
    Perform BIC-based change-point detection on a time series of metrics.
    
    Args:
        metrics: List of metric values (e.g., ECE) over time.
        alpha: Significance level (currently used for logging context, 
               ruptures uses penalty selection internally).
        years: Optional list of years corresponding to metrics. If provided, 
               returns the year of the change point.
    
    Returns:
        The index (if years is None) or the year (if years is provided) of the 
        detected change point. Returns None if no change point is found.
    
    Note:
        Implements Plan's architectural override of FR-006 (BIC-based detection).
        Uses ruptures with 'rbf' kernel and 'bic' penalty.
    """
    if not metrics or len(metrics) < 3:
        logger.warning("Insufficient data for change-point detection (need at least 3 points).")
        return None
    
    signal = np.array(metrics)
    
    try:
        # Use ruptures Pelt algorithm with BIC penalty for optimal change point detection
        # The 'jump' parameter is the minimum distance between change points
        # 'n_bkps' is not fixed for Pelt, it finds the optimal number based on penalty
        model = "rbf" # Gaussian distribution assumption for metric values
        algo = rpt.Pelt(model=model).fit(signal)
        
        # We need to select the penalty. 
        # ruptures.bic_penalty(signal) calculates an automatic penalty based on BIC.
        # Alternatively, we can use a fixed penalty or 'silhouette'. 
        # The task specifies BIC-based.
        penalty = rpt.bic_penalty(signal)
        
        result = algo.predict(penalty=penalty)
        
        # result is a list of segment end indices. 
        # If len(result) > 1, a change point was detected.
        # The change point is at result[0] (0-indexed, exclusive end of first segment).
        if len(result) > 1:
            change_point_index = result[0] - 1 # Index of the last point of the first segment
            
            if years:
                # Ensure we don't go out of bounds
                if 0 <= change_point_index < len(years):
                    return years[change_point_index]
                else:
                    logger.warning("Change point index out of bounds for years list.")
                    return None
            else:
                return change_point_index
        else:
            logger.info("No change point detected by BIC criterion.")
            return None
            
    except Exception as e:
        logger.error(f"Change-point detection failed: {e}")
        return None
