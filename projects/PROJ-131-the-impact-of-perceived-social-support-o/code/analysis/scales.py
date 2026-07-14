"""
Scoring logic for psychological scales (CES-D, GAD-7, PCL-5).

This module implements the scoring functions defined in config/scales.yaml.
It handles reverse coding and total score calculation.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import logging

logger = logging.getLogger(__name__)

def load_scale_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load scale configuration from YAML file."""
    if config_path is None:
        config_path = "config/scales.yaml"
    
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Scale config not found at {config_path}")
    
    with open(path, "r") as f:
        return yaml.safe_load(f)


def score_cesd(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score the CES-D scale.
    
    Args:
        df: DataFrame containing CES-D items (depressed1 to depressed20).
        config: Configuration dictionary for CES-D.
        
    Returns:
        Dictionary with 'total_score' and 'n_items'.
    """
    items = config["items"]
    reverse_items = config.get("reverse_items", [])
    max_score_per_item = 3  # 0-3 scale
    
    # Ensure all items are present
    missing_items = [item for item in items if item not in df.columns]
    if missing_items:
        raise ValueError(f"Missing CES-D items in data: {missing_items}")
    
    scores = []
    for item in items:
        val = df[item].iloc[0]
        
        if pd.isna(val):
            # Handle missing values: return NaN or raise error based on policy
            # Here we return NaN for the total if any item is missing
            return {"total_score": np.nan, "n_items": len(items), "status": "missing_data"}
        
        if item in reverse_items:
            # Reverse score: max - val
            score = max_score_per_item - val
        else:
            score = val
        
        scores.append(score)
    
    total = sum(scores)
    return {"total_score": total, "n_items": len(items), "status": "complete"}


def score_gad7(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score the GAD-7 scale.
    
    Args:
        df: DataFrame containing GAD-7 items (gad1 to gad7).
        config: Configuration dictionary for GAD-7.
        
    Returns:
        Dictionary with 'total_score' and 'n_items'.
    """
    items = config["items"]
    reverse_items = config.get("reverse_items", [])
    max_score_per_item = 3
    
    missing_items = [item for item in items if item not in df.columns]
    if missing_items:
        raise ValueError(f"Missing GAD-7 items in data: {missing_items}")
    
    scores = []
    for item in items:
        val = df[item].iloc[0]
        
        if pd.isna(val):
            return {"total_score": np.nan, "n_items": len(items), "status": "missing_data"}
        
        if item in reverse_items:
            score = max_score_per_item - val
        else:
            score = val
        
        scores.append(score)
    
    total = sum(scores)
    return {"total_score": total, "n_items": len(items), "status": "complete"}


def score_pcl5(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score the PCL-5 scale.
    
    Args:
        df: DataFrame containing PCL-5 items (pcl1 to pcl25).
        config: Configuration dictionary for PCL-5.
        
    Returns:
        Dictionary with 'total_score' and 'n_items'.
    """
    items = config["items"]
    reverse_items = config.get("reverse_items", [])
    max_score_per_item = 4
    
    missing_items = [item for item in items if item not in df.columns]
    if missing_items:
        # PCL-5 might have conditional items. Log warning but proceed if possible.
        logger.warning(f"Missing PCL-5 items in data: {missing_items}. Returning NaN.")
        return {"total_score": np.nan, "n_items": len(items), "status": "missing_data"}
    
    scores = []
    for item in items:
        val = df[item].iloc[0]
        
        if pd.isna(val):
            return {"total_score": np.nan, "n_items": len(items), "status": "missing_data"}
        
        if item in reverse_items:
            score = max_score_per_item - val
        else:
            score = val
        
        scores.append(score)
    
    total = sum(scores)
    return {"total_score": total, "n_items": len(items), "status": "complete"}