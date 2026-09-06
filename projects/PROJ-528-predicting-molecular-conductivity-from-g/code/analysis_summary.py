import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from code.logging_config import setup_logging

logger = setup_logging(__name__)

def load_feature_importance(path: str) -> pd.DataFrame:
    """Load feature importance from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature importance file not found: {path}")
    return pd.read_csv(path)

def load_correlation_results(path: str) -> Dict[str, Any]:
    """Load correlation results from JSON."""
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def get_top_features(importance_df, n=5):
    """Get top N features by importance."""
    return importance_df.head(n)['feature'].tolist()

def summarize_feature_stats(importance_df):
    """Summarize feature importance statistics."""
    return {
        'mean_importance': float(importance_df['importance'].mean()),
        'std_importance': float(importance_df['importance'].std()),
        'max_importance': float(importance_df['importance'].max()),
        'min_importance': float(importance_df['importance'].min())
    }

def generate_analysis_summary(importance_path, output_path):
    """Generate and save analysis summary."""
    logger.info(f"Loading feature importance from {importance_path}")
    importance_df = load_feature_importance(importance_path)
    
    top_features = get_top_features(importance_df, n=5)
    stats = summarize_feature_stats(importance_df)
    
    summary = {
        'top_5_features': top_features,
        'feature_stats': stats,
        'total_features': len(importance_df),
        'fdr_method': 'benjamini_hochberg'
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Analysis summary saved to {output_path}")
    return summary

def main():
    parser = argparse.ArgumentParser(description="Generate analysis summary.")
    parser.add_argument('--feature-importance', type=str, required=True, help='Path to feature importance CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to save analysis summary JSON')
    args = parser.parse_args()
    
    generate_analysis_summary(args.feature_importance, args.output)

if __name__ == "__main__":
    main()