"""
Analysis Summary Module for US3
Generates final analysis summary with adjusted p-values and top features.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from code.config import SEED
from code.logging_config import setup_logging

# Setup logging
logger = setup_logging(__name__)

def load_feature_importance(filepath: str = "data/processed/feature_importance.csv") -> pd.DataFrame:
    """Load feature importance rankings."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Feature importance file not found: {filepath}")
    df = pd.read_csv(filepath)
    return df

def load_correlation_results(filepath: str = "data/processed/correlation_results.json") -> Dict[str, Any]:
    """Load correlation results with p-values."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Correlation results file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def get_top_features(feature_importance_df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Select top N features by permutation importance score (descending).
    Ties are broken by alphabetical feature name.
    """
    # Sort by importance (descending), then by feature name (ascending) for ties
    sorted_df = feature_importance_df.sort_values(
        by=['importance_score', 'feature'],
        ascending=[False, True]
    )
    top_features = sorted_df.head(top_n).to_dict('records')
    return top_features

def summarize_feature_stats(correlation_results: Dict[str, Any], top_features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize statistics for top features including adjusted p-values."""
    summary = []
    for feat in top_features:
        feat_name = feat['feature']
        corr_data = correlation_results.get(feat_name, {})
        summary.append({
            'feature': feat_name,
            'importance_score': feat['importance_score'],
            'correlation_coefficient': corr_data.get('correlation_coefficient'),
            'raw_p_value': corr_data.get('raw_p_value'),
            'adjusted_p_value': corr_data.get('adjusted_p_value')
        })
    return summary

def generate_analysis_summary(top_features: List[Dict[str, Any]], summary_stats: List[Dict[str, Any]], output_path: str) -> None:
    """Generate and save the final analysis summary JSON."""
    summary_data = {
        'top_features': top_features,
        'feature_summary_stats': summary_stats,
        'total_features_analyzed': len(summary_stats),
        'selection_criteria': 'Top 5 by permutation importance (descending), ties broken alphabetically'
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    logger.info(f"Analysis summary saved to {output_path}")

def main():
    """Main entry point for generating analysis summary."""
    logger.info("Starting analysis summary generation...")
    
    try:
        # Load feature importance
        feature_importance_df = load_feature_importance()
        logger.info(f"Loaded {len(feature_importance_df)} features from importance file")
        
        # Load correlation results
        correlation_results = load_correlation_results()
        logger.info(f"Loaded correlation results for {len(correlation_results)} features")
        
        # Get top 5 features
        top_features = get_top_features(feature_importance_df, top_n=5)
        logger.info(f"Selected top 5 features: {[f['feature'] for f in top_features]}")
        
        # Summarize stats
        summary_stats = summarize_feature_stats(correlation_results, top_features)
        
        # Generate and save summary
        output_path = "data/processed/analysis_summary.json"
        generate_analysis_summary(top_features, summary_stats, output_path)
        
        logger.info("Analysis summary generation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during analysis summary generation: {e}")
        raise

if __name__ == "__main__":
    main()