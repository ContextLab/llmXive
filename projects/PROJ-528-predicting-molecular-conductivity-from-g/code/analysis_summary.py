"""
analysis_summary.py

Generates the final analysis summary (T045) by combining feature importance rankings
with adjusted p-values.

Logic:
1. Load feature importance from `data/processed/feature_importance.csv`.
2. Load adjusted p-values from `data/processed/correlation_results.json`.
3. Select top 5 features by importance (descending), ties broken alphabetically.
4. Save summary to `data/processed/analysis_summary.json`.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from code.logging_config import setup_logging
from code.config import DATA_PATH

# Setup logging
logger = setup_logging(__name__)

def load_feature_importance(path: str = None) -> pd.DataFrame:
    """
    Load the feature importance CSV.
    Expects columns: 'feature', 'importance_score' (and potentially 'rank').
    """
    if path is None:
        path = os.path.join(DATA_PATH, "processed", "feature_importance.csv")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature importance file not found at {path}. "
                                "Ensure T040 has been executed successfully.")
    
    df = pd.read_csv(path)
    # Ensure we have the expected columns
    required_cols = ['feature', 'importance_score']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Feature importance CSV missing required columns: {missing_cols}")
    
    return df

def load_correlation_results(path: str = None) -> Dict[str, Any]:
    """
    Load the correlation results JSON containing adjusted p-values.
    Expected structure: {'adjusted_p_values': {feature: p_value, ...}, ...}
    """
    if path is None:
        # T042 saves to correlation_results.json based on standard patterns in this project
        path = os.path.join(DATA_PATH, "processed", "correlation_results.json")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Correlation results file not found at {path}. "
                                "Ensure T042 has been executed successfully.")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if 'adjusted_p_values' not in data:
        raise KeyError("Correlation results JSON missing 'adjusted_p_values' key.")
    
    return data['adjusted_p_values']

def get_top_features(importance_df: pd.DataFrame, top_n: int = 5) -> List[str]:
    """
    Select top N features by importance score.
    Sort order: importance_score DESC, then feature name ASC (alphabetical).
    """
    # Sort by importance descending, then by feature name ascending
    sorted_df = importance_df.sort_values(
        by=['importance_score', 'feature'], 
        ascending=[False, True]
    )
    
    top_features = sorted_df['feature'].head(top_n).tolist()
    return top_features

def summarize_feature_stats(importance_df: pd.DataFrame, top_features: List[str]) -> Dict[str, Any]:
    """
    (Optional) Summarize stats for the top features if needed.
    Currently returns basic info to satisfy structure requirements.
    """
    stats = {}
    for feat in top_features:
        row = importance_df[importance_df['feature'] == feat].iloc[0]
        stats[feat] = {
            'importance_score': float(row['importance_score']),
            'rank': int(row.get('rank', 0))
        }
    return stats

def generate_analysis_summary(
    top_features: List[str], 
    adjusted_p_values: Dict[str, float],
    fdr_method: str = "fdr_bh"
) -> Dict[str, Any]:
    """
    Construct the final summary dictionary.
    Keys: 'top_5_features', 'adjusted_p_values', 'fdr_method'.
    """
    # Filter adjusted p-values to only include the top features
    top_p_values = {feat: adjusted_p_values.get(feat, np.nan) for feat in top_features}
    
    summary = {
        "top_5_features": top_features,
        "adjusted_p_values": top_p_values,
        "fdr_method": fdr_method
    }
    return summary

def main():
    """
    Main entry point for T045.
    """
    logger.info("Starting Analysis Summary Generation (T045)...")
    
    try:
        # 1. Load Feature Importance
        logger.info("Loading feature importance data...")
        importance_df = load_feature_importance()
        
        # 2. Load Adjusted P-values
        logger.info("Loading adjusted p-values...")
        adjusted_p_values = load_correlation_results()
        
        # 3. Select Top Features
        logger.info("Selecting top 5 features by importance...")
        top_features = get_top_features(importance_df, top_n=5)
        logger.info(f"Top 5 features selected: {top_features}")
        
        # 4. Generate Summary
        logger.info("Generating analysis summary...")
        summary = generate_analysis_summary(top_features, adjusted_p_values)
        
        # 5. Write Output
        output_path = os.path.join(DATA_PATH, "processed", "analysis_summary.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Analysis summary successfully written to {output_path}")
        print(f"Success: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating analysis summary: {e}")
        raise

if __name__ == "__main__":
    main()