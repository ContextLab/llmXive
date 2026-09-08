import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from logging_config import setup_logging

logger = setup_logging(__name__)

def load_feature_importance(path: str) -> pd.DataFrame:
    """Load feature importance CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature importance file not found: {path}")
    return pd.read_csv(path)

def load_correlation_results(path: str) -> Dict[str, Any]:
    """Load correlation results JSON."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Correlation results file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def get_top_features(importance_df: pd.DataFrame, top_n: int = 5) -> List[str]:
    """Get top N features by importance."""
    return importance_df['feature'].head(top_n).tolist()

def summarize_feature_stats(importance_df: pd.DataFrame) -> Dict[str, Any]:
    """Summarize feature importance statistics."""
    return {
        "mean_importance": float(importance_df['importance_mean'].mean()),
        "std_importance": float(importance_df['importance_std'].mean()),
        "top_feature": importance_df.iloc[0]['feature'] if not importance_df.empty else None
    }

def generate_analysis_summary(
    importance_path: str, 
    correlation_path: str, 
    output_path: str,
    top_n: int = 5
) -> None:
    """Generate and save analysis summary."""
    logger.info("Generating analysis summary...")
    
    importance_df = load_feature_importance(importance_path)
    # correlation_results = load_correlation_results(correlation_path) # Optional if needed
    
    top_features = get_top_features(importance_df, top_n)
    stats = summarize_feature_stats(importance_df)
    
    summary = {
        "top_5_features": top_features,
        "adjusted_p_values": {}, # Placeholder, would come from BH correction
        "fdr_method": "benjamini_hochberg",
        "feature_stats": stats
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Analysis summary saved to {output_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate analysis summary.")
    parser.add_argument('--importance', type=str, required=True, help='Path to feature importance CSV')
    parser.add_argument('--correlation', type=str, required=True, help='Path to correlation results JSON')
    parser.add_argument('--output', type=str, required=True, help='Path to output summary JSON')
    args = parser.parse_args()
    
    generate_analysis_summary(args.importance, args.correlation, args.output)

if __name__ == "__main__":
    main()
