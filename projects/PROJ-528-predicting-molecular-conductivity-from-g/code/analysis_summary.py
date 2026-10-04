import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from code.logging_config import setup_logging

# Configure logging
logger = setup_logging(__name__)

# Constants
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
FEATURE_IMPORTANCE_PATH = os.path.join(DATA_PATH, 'feature_importance.csv')
CORRELATION_RESULTS_PATH = os.path.join(DATA_PATH, 'correlation_results.json')
ANALYSIS_SUMMARY_PATH = os.path.join(DATA_PATH, 'analysis_summary.json')

def load_feature_importance(path: str = FEATURE_IMPORTANCE_PATH) -> pd.DataFrame:
    """Load feature importance data from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature importance file not found: {path}")
    df = pd.read_csv(path)
    return df

def load_correlation_results(path: str = CORRELATION_RESULTS_PATH) -> Dict[str, Any]:
    """Load correlation results from JSON."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Correlation results file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def get_top_features(importance_df: pd.DataFrame, n: int = 5) -> List[str]:
    """
    Select top features by permutation importance score (descending).
    Ties are broken by alphabetical feature name.
    """
    # Sort by importance_score descending, then by feature name ascending
    sorted_df = importance_df.sort_values(
        by=['importance_score', 'feature'],
        ascending=[False, True]
    )
    top_features = sorted_df['feature'].head(n).tolist()
    return top_features

def summarize_feature_stats(importance_df: pd.DataFrame, correlation_results: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize basic statistics for features."""
    stats = {
        'total_features': len(importance_df),
        'mean_importance': float(importance_df['importance_score'].mean()),
        'std_importance': float(importance_df['importance_score'].std()),
        'max_importance': float(importance_df['importance_score'].max()),
        'min_importance': float(importance_df['importance_score'].min()),
    }
    return stats

def generate_analysis_summary(
    importance_df: pd.DataFrame,
    correlation_results: Dict[str, Any],
    top_n: int = 5
) -> Dict[str, Any]:
    """
    Generate the final analysis summary with adjusted p-values and top features.
    
    Keys:
      - top_features: List of top N features by importance (ties broken alphabetically)
      - adjusted_p_values: Dictionary mapping feature names to adjusted p-values
      - fdr_method: String indicating the FDR correction method used ('fdr_bh')
    """
    top_features = get_top_features(importance_df, n=top_n)
    
    # Extract adjusted p-values from correlation results
    # The correlation_results should contain 'adjusted_p_values' key from T042
    adjusted_p_values = correlation_results.get('adjusted_p_values', {})
    
    # Filter adjusted p-values to only include top features for clarity, 
    # but the task requires the full mapping if available or at least the top ones.
    # The spec says "adjusted_p_values" key in the summary. We'll include all available.
    
    summary = {
        'top_features': top_features,
        'adjusted_p_values': adjusted_p_values,
        'fdr_method': 'fdr_bh',
        'feature_statistics': summarize_feature_stats(importance_df, correlation_results)
    }
    
    return summary

def main():
    """Main entry point for generating the analysis summary."""
    logger.info("Starting analysis summary generation...")
    
    try:
        # Load required data
        logger.info(f"Loading feature importance from {FEATURE_IMPORTANCE_PATH}")
        importance_df = load_feature_importance()
        
        logger.info(f"Loading correlation results from {CORRELATION_RESULTS_PATH}")
        correlation_results = load_correlation_results()
        
        # Generate summary
        logger.info("Generating analysis summary...")
        summary = generate_analysis_summary(importance_df, correlation_results, top_n=5)
        
        # Save summary to file
        logger.info(f"Saving analysis summary to {ANALYSIS_SUMMARY_PATH}")
        with open(ANALYSIS_SUMMARY_PATH, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Analysis summary successfully written to {ANALYSIS_SUMMARY_PATH}")
        print(f"SUCCESS: Analysis summary saved to {ANALYSIS_SUMMARY_PATH}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating analysis summary: {e}")
        raise

if __name__ == '__main__':
    main()