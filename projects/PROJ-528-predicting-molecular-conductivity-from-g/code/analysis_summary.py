"""
Generate final analysis summary with adjusted p-values and top features.
Saves results to data/processed/analysis_summary.json
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from logging_config import setup_logging
from feature_importance import run_feature_importance_analysis, extract_tree_importance
from correlation_analysis import calculate_correlation_pvalues
from feature_analysis import apply_bh_correction_to_df, benjamini_hochberg
from config import DATA_PATH, TARGET_VAR

logger = logging.getLogger(__name__)

def load_feature_importance(filepath: str = "data/processed/feature_importance.csv") -> pd.DataFrame:
    """Load feature importance data from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Feature importance file not found: {filepath}")
    df = pd.read_csv(filepath)
    return df

def load_correlation_results(filepath: str = "data/processed/correlation_results.csv") -> pd.DataFrame:
    """Load correlation results with p-values."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Correlation results file not found: {filepath}")
    df = pd.read_csv(filepath)
    return df

def get_top_features(importance_df: pd.DataFrame, n: int = 5) -> List[str]:
    """Get top N features by importance."""
    if importance_df.empty:
        return []
    sorted_df = importance_df.sort_values(by='importance', ascending=False)
    return sorted_df['feature'].head(n).tolist()

def summarize_feature_stats(importance_df: pd.DataFrame, corr_df: pd.DataFrame) -> Dict[str, Any]:
    """Create summary statistics for top features."""
    top_features = get_top_features(importance_df, n=5)
    
    summary = {
        "top_features": top_features,
        "feature_details": []
    }
    
    for feature in top_features:
        imp_row = importance_df[importance_df['feature'] == feature]
        corr_row = corr_df[corr_df['feature'] == feature] if not corr_df.empty else None
        
        detail = {
            "feature": feature,
            "importance": float(imp_row['importance'].iloc[0]) if not imp_row.empty else None,
            "rank": int(imp_row['rank'].iloc[0]) if not imp_row.empty else None
        }
        
        if not corr_row.empty and len(corr_row) > 0:
            detail["correlation"] = float(corr_row['correlation'].iloc[0])
            detail["p_value_raw"] = float(corr_row['p_value'].iloc[0])
            detail["p_value_adjusted"] = float(corr_row['p_value_adjusted'].iloc[0]) if 'p_value_adjusted' in corr_row.columns else None
        else:
            detail["correlation"] = None
            detail["p_value_raw"] = None
            detail["p_value_adjusted"] = None
        
        summary["feature_details"].append(detail)
    
    return summary

def generate_analysis_summary(
    importance_path: str = "data/processed/feature_importance.csv",
    correlation_path: str = "data/processed/correlation_results.csv",
    output_path: str = "data/processed/analysis_summary.json"
) -> Dict[str, Any]:
    """
    Generate comprehensive analysis summary combining feature importance and
    correlation analysis with adjusted p-values.
    
    Args:
        importance_path: Path to feature importance CSV
        correlation_path: Path to correlation results CSV
        output_path: Path to save the summary JSON
        
    Returns:
        Dictionary containing the analysis summary
    """
    logger.info(f"Loading feature importance from {importance_path}")
    importance_df = load_feature_importance(importance_path)
    
    logger.info(f"Loading correlation results from {correlation_path}")
    corr_df = load_correlation_results(correlation_path)
    
    # Ensure p-values are adjusted if not already
    if not corr_df.empty and 'p_value_adjusted' not in corr_df.columns:
        logger.info("Applying Benjamini-Hochberg correction to p-values")
        corr_df = apply_bh_correction_to_df(corr_df, 'p_value', 'p_value_adjusted')
        corr_df.to_csv(correlation_path, index=False)
    
    # Get summary statistics
    summary = summarize_feature_stats(importance_df, corr_df)
    
    # Add metadata
    summary["metadata"] = {
        "target_variable": TARGET_VAR,
        "total_features_analyzed": len(importance_df),
        "top_n_features": 5,
        "correlation_method": "spearman",
        "p_value_correction": "benjamini-hochberg"
    }
    
    # Add model performance context if available
    try:
        results_path = "data/processed/model_results.json"
        if os.path.exists(results_path):
            with open(results_path, 'r') as f:
                model_results = json.load(f)
            summary["model_performance"] = {
                "r2_rf": model_results.get("rf_r2"),
                "r2_gb": model_results.get("gb_r2"),
                "mae": model_results.get("mae")
            }
    except Exception as e:
        logger.warning(f"Could not load model results: {e}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save summary to JSON
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Analysis summary saved to {output_path}")
    return summary

def main():
    """Main entry point for generating analysis summary."""
    setup_logging()
    logger.info("Starting analysis summary generation (T045)")
    
    try:
        summary = generate_analysis_summary(
            importance_path="data/processed/feature_importance.csv",
            correlation_path="data/processed/correlation_results.csv",
            output_path="data/processed/analysis_summary.json"
        )
        
        logger.info(f"Top 5 features: {summary['top_features']}")
        logger.info("Analysis summary generation completed successfully")
        
        return summary
        
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating analysis summary: {e}")
        raise

if __name__ == "__main__":
    main()