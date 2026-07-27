import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from code.config import SEED
from code.logging_config import setup_logging

# Ensure logging is configured
setup_logging()
logger = logging.getLogger(__name__)


def load_feature_importance(path: str = "data/processed/feature_importance.csv") -> pd.DataFrame:
    """Load feature importance data from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature importance file not found: {path}")
    df = pd.read_csv(path)
    return df


def load_correlation_results(path: str = "data/processed/correlation_results.json") -> Dict[str, Any]:
    """Load correlation results from JSON."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Correlation results file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)


def get_top_features(importance_df: pd.DataFrame, n: int = 5) -> List[Dict[str, Any]]:
    """Get top N features based on importance score."""
    if importance_df.empty:
        logger.warning("Feature importance DataFrame is empty.")
        return []
    
    # Sort by importance score descending
    sorted_df = importance_df.sort_values(by='importance_score', ascending=False)
    top_n = sorted_df.head(n)
    
    top_features = []
    for _, row in top_n.iterrows():
        top_features.append({
            'feature_name': row['feature_name'],
            'importance_score': float(row['importance_score']),
            'rank': int(row['rank'])
        })
    return top_features


def summarize_feature_stats(importance_df: pd.DataFrame, corr_results: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize feature statistics including correlation info."""
    if importance_df.empty:
        return {"total_features": 0, "summary": "No features found."}
    
    stats = {
        "total_features": len(importance_df),
        "mean_importance": float(importance_df['importance_score'].mean()),
        "std_importance": float(importance_df['importance_score'].std()),
        "max_importance": float(importance_df['importance_score'].max()),
        "min_importance": float(importance_df['importance_score'].min())
    }
    
    # Add correlation summary if available
    if corr_results and 'correlations' in corr_results:
        corr_data = corr_results['correlations']
        if corr_data:
            p_values = [item.get('p_value', 0) for item in corr_data if 'p_value' in item]
            if p_values:
                stats['min_p_value'] = float(min(p_values))
                stats['significant_features_count'] = sum(1 for p in p_values if p < 0.05)
            else:
                stats['significant_features_count'] = 0
        else:
            stats['significant_features_count'] = 0
    else:
        stats['significant_features_count'] = 0
        
    return stats


def generate_analysis_summary(
    importance_path: str = "data/processed/feature_importance.csv",
    corr_path: str = "data/processed/correlation_results.json",
    output_path: str = "data/processed/analysis_summary.json"
) -> Dict[str, Any]:
    """
    Generate final analysis summary with adjusted p-values and top features.
    Saves to data/processed/analysis_summary.json.
    """
    # Load data
    logger.info(f"Loading feature importance from {importance_path}")
    importance_df = load_feature_importance(importance_path)
    
    logger.info(f"Loading correlation results from {corr_path}")
    corr_results = load_correlation_results(corr_path)
    
    # Get top features
    top_features = get_top_features(importance_df, n=5)
    
    # Summarize stats
    feature_stats = summarize_feature_stats(importance_df, corr_results)
    
    # Extract adjusted p-values if available
    adjusted_pvalues = []
    if corr_results and 'correlations' in corr_results:
        for item in corr_results['correlations']:
            if 'adj_p_value' in item:
                adjusted_pvalues.append({
                    'feature': item.get('feature_name', 'unknown'),
                    'adj_p_value': item['adj_p_value']
                })
    
    # Build summary
    summary = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "seed_used": SEED,
        "feature_statistics": feature_stats,
        "top_features": top_features,
        "adjusted_p_values": adjusted_pvalues,
        "total_features_analyzed": len(importance_df),
        "methodology_notes": [
            "Feature importance derived from Random Forest and Gradient Boosting models.",
            "Correlation p-values adjusted using Benjamini-Hochberg FDR correction.",
            "Top 5 features ranked by importance score."
        ]
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")
    
    # Save summary
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Analysis summary saved to {output_path}")
    return summary


def main():
    """Main entry point for analysis summary generation."""
    logger.info("Starting analysis summary generation (T045)...")
    try:
        summary = generate_analysis_summary()
        logger.info("Analysis summary generation completed successfully.")
        print(f"Summary saved to: data/processed/analysis_summary.json")
        print(f"Top features: {[f['feature_name'] for f in summary['top_features']]}")
    except Exception as e:
        logger.error(f"Failed to generate analysis summary: {e}")
        raise


if __name__ == "__main__":
    main()
