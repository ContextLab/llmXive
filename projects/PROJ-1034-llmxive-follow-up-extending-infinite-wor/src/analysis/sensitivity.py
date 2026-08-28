"""
Sensitivity Analysis: Sweeps coherence decision cutoffs.
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def run_sensitivity_analysis(data: pd.DataFrame, cutoffs: list = [0.1, 0.3, 0.5, 0.7, 0.9]) -> pd.DataFrame:
    """
    Analyze sensitivity of results to different coherence cutoffs.
    """
    results = []
    for cutoff in cutoffs:
        mask = data["coherence_score"] > cutoff
        count = mask.sum()
        results.append({
            "cutoff": cutoff,
            "count": count,
            "fraction": count / len(data)
        })
    
    return pd.DataFrame(results)
