"""
Analysis Summary Module (T045)
Generates the final analysis summary with adjusted p-values and top features.
Saves the result to data/processed/analysis_summary.json.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

# Import from existing modules based on API surface
from code.config import DATA_PATH, SEED, TARGET_VAR
from code.logging_config import setup_logging

# Ensure logging is configured
logger = setup_logging()

def load_feature_importance(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load feature importance data from CSV."""
    if filepath is None:
        filepath = os.path.join(DATA_PATH, "processed", "feature_importance.csv")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Feature importance file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded feature importance from {filepath}, shape: {df.shape}")
    return df

def load_correlation_results(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load correlation results (including adjusted p-values) from CSV/JSON."""
    # Try CSV first, then JSON if needed
    csv_path = os.path.join(DATA_PATH, "processed", "correlation_results.csv")
    json_path = os.path.join(DATA_PATH, "processed", "correlation_results.json")
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded correlation results from {csv_path}")
    elif os.path.exists(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
            df = pd.DataFrame(data)
        logger.info(f"Loaded correlation results from {json_path}")
    else:
        # Fallback: try to load from analysis outputs if available
        # This might happen if the file is named differently
        raise FileNotFoundError("Correlation results file not found in expected locations.")
    
    return df

def get_top_features(feature_importance_df: pd.DataFrame, n: int = 10) -> List[Dict[str, Any]]:
    """Get top N features by importance score."""
    if 'importance' not in feature_importance_df.columns:
        # Try to find the importance column (might be named differently)
        importance_cols = [col for col in feature_importance_df.columns if 'importance' in col.lower()]
        if importance_cols:
            importance_col = importance_cols[0]
        else:
            raise ValueError("No importance column found in feature importance DataFrame")
    else:
        importance_col = 'importance'
    
    top_features = feature_importance_df.nlargest(n, importance_col)
    result = []
    for _, row in top_features.iterrows():
        result.append({
            'feature': row['feature'],
            'importance': float(row[importance_col]),
            'rank': len(result) + 1
        })
    return result

def summarize_feature_stats(correlation_df: pd.DataFrame) -> Dict[str, Any]:
    """Summarize statistical properties of feature correlations."""
    stats = {}
    
    # Look for correlation coefficient and p-value columns
    corr_cols = [col for col in correlation_df.columns if 'correlation' in col.lower() or 'coeff' in col.lower()]
    pval_cols = [col for col in correlation_df.columns if 'p_value' in col.lower() or 'pval' in col.lower() or 'p-value' in col.lower()]
    
    if not corr_cols or not pval_cols:
        logger.warning("Could not find correlation or p-value columns in correlation results")
        return stats
    
    corr_col = corr_cols[0]
    pval_col = pval_cols[0]
    
    # Check for adjusted p-values
    adj_pval_col = None
    adj_pval_candidates = [col for col in correlation_df.columns if 'adj' in col.lower() and 'p' in col.lower()]
    if adj_pval_candidates:
        adj_pval_col = adj_pval_candidates[0]
    
    stats['total_features'] = len(correlation_df)
    stats['mean_correlation'] = float(correlation_df[corr_col].mean())
    stats['std_correlation'] = float(correlation_df[corr_col].std())
    stats['min_correlation'] = float(correlation_df[corr_col].min())
    stats['max_correlation'] = float(correlation_df[corr_col].max())
    
    if adj_pval_col:
        significant_count = (correlation_df[adj_pval_col] < 0.05).sum()
        stats['significant_features_at_0.05'] = int(significant_count)
        stats['fdr_adjusted'] = True
        stats['fdr_method'] = 'benjamini_hochberg'
    else:
        # Use raw p-values if adjusted not available
        significant_count = (correlation_df[pval_col] < 0.05).sum()
        stats['significant_features_at_0.05'] = int(significant_count)
        stats['fdr_adjusted'] = False
    
    return stats

def generate_analysis_summary(
    feature_importance_df: pd.DataFrame,
    correlation_df: pd.DataFrame,
    top_n: int = 10
) -> Dict[str, Any]:
    """Generate the final analysis summary."""
    summary = {
        'metadata': {
            'target_variable': TARGET_VAR,
            'seed': SEED,
            'generated_at': pd.Timestamp.now().isoformat(),
            'analysis_version': '1.0.0'
        },
        'feature_statistics': summarize_feature_stats(correlation_df),
        'top_features': get_top_features(feature_importance_df, n=top_n),
        'correlation_summary': {
            'total_correlations': len(correlation_df),
            'features_with_positive_correlation': int((correlation_df['correlation_coefficient'] > 0).sum()),
            'features_with_negative_correlation': int((correlation_df['correlation_coefficient'] < 0).sum()),
            'features_with_significant_correlation': int((correlation_df['adj_p_value'] < 0.05).sum()) if 'adj_p_value' in correlation_df.columns else None
        }
    }
    
    # Add detailed top features with p-values
    top_features_details = []
    for feat in summary['top_features']:
        feat_name = feat['feature']
        feat_row = correlation_df[correlation_df['feature'] == feat_name]
        if not feat_row.empty:
            row = feat_row.iloc[0]
            top_features_details.append({
                'feature': feat_name,
                'importance_rank': feat['rank'],
                'importance_score': feat['importance'],
                'correlation_coefficient': float(row['correlation_coefficient']),
                'p_value': float(row['p_value']),
                'adjusted_p_value': float(row['adj_p_value']) if 'adj_p_value' in row else float(row['p_value']),
                'is_significant': bool(row['adj_p_value'] < 0.05) if 'adj_p_value' in row else bool(row['p_value'] < 0.05)
            })
    
    summary['detailed_top_features'] = top_features_details
    
    return summary

def main(
    feature_importance_path: Optional[str] = None,
    correlation_path: Optional[str] = None,
    output_path: Optional[str] = None,
    top_n: int = 10
):
    """Main function to generate and save the analysis summary."""
    # Set default paths if not provided
    if output_path is None:
        output_path = os.path.join(DATA_PATH, "processed", "analysis_summary.json")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info(f"Generating analysis summary, output will be saved to: {output_path}")
    
    try:
        # Load data
        feature_importance_df = load_feature_importance(feature_importance_path)
        correlation_df = load_correlation_results(correlation_path)
        
        # Generate summary
        summary = generate_analysis_summary(feature_importance_df, correlation_df, top_n=top_n)
        
        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Analysis summary successfully saved to {output_path}")
        logger.info(f"Summary contains {len(summary['top_features'])} top features")
        logger.info(f"Summary contains {summary['feature_statistics']['total_features']} total feature correlations")
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate analysis summary: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate final analysis summary")
    parser.add_argument("--feature-importance", type=str, default=None, help="Path to feature importance CSV")
    parser.add_argument("--correlation", type=str, default=None, help="Path to correlation results")
    parser.add_argument("--output", type=str, default=None, help="Path to output JSON file")
    parser.add_argument("--top-n", type=int, default=10, help="Number of top features to include")
    
    args = parser.parse_args()
    
    main(
        feature_importance_path=args.feature_importance,
        correlation_path=args.correlation,
        output_path=args.output,
        top_n=args.top_n
    )
