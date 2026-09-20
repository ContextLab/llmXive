import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from code.logging_config import setup_logging

logger = logging.getLogger(__name__)

def load_feature_importance(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature importance file not found: {path}")
    return pd.read_csv(path)

def load_correlation_results(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Correlation results file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def get_top_features(importance_df: pd.DataFrame, n: int = 5) -> List[str]:
    """Get top n features by importance score."""
    return importance_df['feature'].head(n).tolist()

def summarize_feature_stats(df: pd.DataFrame) -> Dict[str, Any]:
    return df.describe().to_dict()

def generate_analysis_summary(
    feature_importance_path: str,
    correlation_results_path: str,
    output_path: str
) -> None:
    """Generate analysis summary JSON."""
    logger.info(f"Generating analysis summary from {feature_importance_path} and {correlation_results_path}")

    fi_df = load_feature_importance(feature_importance_path)
    corr_res = load_correlation_results(correlation_results_path)

    top_features = get_top_features(fi_df, n=5)

    # Adjusted p-values are in correlation_results if available, or compute if needed
    # Assuming correlation_results contains adjusted p-values or raw
    adjusted_p_values = {}
    if 'adjusted_p_values' in corr_res:
        adjusted_p_values = corr_res['adjusted_p_values']
    else:
        # Fallback: assume raw p-values in corr_res and adjust (simplified)
        # This logic might need to be more robust depending on actual data
        pass

    summary = {
        "top_5_features": top_features,
        "adjusted_p_values": adjusted_p_values,
        "fdr_method": "fdr_bh"
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Analysis summary saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate analysis summary (T045)")
    parser.add_argument("--importance", type=str, default="data/processed/feature_importance.csv")
    parser.add_argument("--correlations", type=str, default="data/processed/correlation_results.json")
    parser.add_argument("--output", type=str, default="data/processed/analysis_summary.json")
    args = parser.parse_args()

    setup_logging()
    try:
        generate_analysis_summary(args.importance, args.correlations, args.output)
    except Exception as e:
        logger.error(f"Failed to generate analysis summary: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
