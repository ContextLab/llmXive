"""
Feature importance aggregation and top-k extraction.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def aggregate_importance(importance_dicts: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Aggregate feature importances from multiple models or folds.
    
    Args:
        importance_dicts: List of dicts mapping feature names to importance scores
        
    Returns:
        Dictionary of aggregated (mean) importance scores
    """
    if not importance_dicts:
        logger.warning("Empty importance list provided")
        return {}
        
    # Convert to DataFrame for easy aggregation
    df = pd.DataFrame(importance_dicts).fillna(0)
    mean_importance = df.mean(axis=0).to_dict()
    
    logger.info(f"Aggregated importance for {len(mean_importance)} features")
    return mean_importance

def get_top_features(
    importance_dict: Dict[str, float], 
    exclude: Optional[List[str]] = None, 
    top_n: int = 3
) -> List[Tuple[str, float]]:
    """
    Extract top N most important features, optionally excluding specified ones.
    
    Args:
        importance_dict: Dictionary of feature names to importance scores
        exclude: List of feature names to exclude from ranking
        top_n: Number of top features to return
        
    Returns:
        List of (feature_name, importance_score) tuples sorted by importance
    """
    if exclude is None:
        exclude = []
        
    # Filter out excluded features
    filtered = {k: v for k, v in importance_dict.items() if k not in exclude}
    
    if not filtered:
        logger.warning("No features remaining after exclusion")
        return []
        
    # Sort by importance descending
    sorted_features = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
    
    # Return top N
    result = sorted_features[:top_n]
    logger.info(f"Selected top {len(result)} features: {[f[0] for f in result]}")
    return result
