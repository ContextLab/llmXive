import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr

from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_feature_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the processed features dataset."""
    feature_path = Path(config['paths']['processed_features'])
    if not feature_path.exists():
        raise FileNotFoundError(f"Feature file not found: {feature_path}")
    
    logger.info(f"Loading feature data from {feature_path}")
    df = pd.read_csv(feature_path)
    
    # Ensure required columns exist
    required_cols = ['prompt_id', 'modal_verb_freq', 'imperative_ratio', 'citation_density']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Feature file missing required columns: {missing_cols}")
    
    return df

def load_annotation_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the aggregated annotation pilot data."""
    annotation_path = Path(config['paths']['annotation_pilot_us1'])
    if not annotation_path.exists():
        raise FileNotFoundError(f"Annotation file not found: {annotation_path}")
    
    logger.info(f"Loading annotation data from {annotation_path}")
    df = pd.read_csv(annotation_path)
    
    # Ensure required columns exist
    required_cols = ['prompt_id', 'authority_density_score']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Annotation file missing required columns: {missing_cols}")
    
    return df

def merge_data_for_correlation(features_df: pd.DataFrame, annotation_df: pd.DataFrame) -> pd.DataFrame:
    """Merge feature and annotation data on prompt_id."""
    logger.info("Merging feature and annotation data")
    
    # Drop rows with missing values in key columns
    features_clean = features_df.dropna(subset=['prompt_id', 'modal_verb_freq', 'imperative_ratio', 'citation_density'])
    annotation_clean = annotation_df.dropna(subset=['prompt_id', 'authority_density_score'])
    
    merged = pd.merge(
        features_clean,
        annotation_clean,
        on='prompt_id',
        how='inner'
    )
    
    logger.info(f"Merged dataset size: {len(merged)} rows")
    return merged

def compute_correlations(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute Pearson and Spearman correlations between features and authority density."""
    logger.info("Computing correlations")
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'sample_size': len(df),
        'correlations': {}
    }
    
    features = ['modal_verb_freq', 'imperative_ratio', 'citation_density']
    
    for feature in features:
        if feature in df.columns:
            # Pearson correlation
            pearson_corr, pearson_p = pearsonr(df[feature], df['authority_density_score'])
            
            # Spearman correlation
            spearman_corr, spearman_p = spearmanr(df[feature], df['authority_density_score'])
            
            results['correlations'][feature] = {
                'pearson': {
                    'r': float(pearson_corr),
                    'p_value': float(pearson_p)
                },
                'spearman': {
                    'rho': float(spearman_corr),
                    'p_value': float(spearman_p)
                }
            }
            logger.info(f"{feature}: Pearson r={pearson_corr:.4f} (p={pearson_p:.4f}), Spearman rho={spearman_corr:.4f} (p={spearman_p:.4f})")
        else:
            logger.warning(f"Feature {feature} not found in dataset")
    
    return results

def aggregate_rater_responses(raw_annotation_path: Path, output_path: Path) -> pd.DataFrame:
    """Aggregate raw rater responses into a single score per prompt."""
    # This function is a placeholder for the aggregation logic that should have been
    # implemented in T017c. For T017d, we assume the aggregated file already exists.
    # However, if we need to support the full pipeline, we would implement it here.
    raise NotImplementedError("Aggregation should be handled by T017c. This function is for reference.")

def run_annotation_analyze_pipeline(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run the full annotation analysis pipeline for T017d."""
    if config is None:
        config = get_config()
    
    logger.info("Starting annotation analysis pipeline (T017d)")
    
    # Load data
    features_df = load_feature_data(config)
    annotation_df = load_annotation_data(config)
    
    # Merge data
    merged_df = merge_data_for_correlation(features_df, annotation_df)
    
    if len(merged_df) == 0:
        raise ValueError("No overlapping data between features and annotations. Cannot compute correlations.")
    
    # Compute correlations
    correlation_results = compute_correlations(merged_df)
    
    # Save results
    output_path = Path(config['paths']['annotation_correlation_raw'])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(correlation_results, f, indent=2)
    
    logger.info(f"Correlation results saved to {output_path}")
    return correlation_results

def main():
    """Entry point for T017d."""
    config = get_config()
    
    try:
        results = run_annotation_analyze_pipeline(config)
        logger.info("Annotation analysis pipeline completed successfully")
        print(f"Analysis complete. Results written to {config['paths']['annotation_correlation_raw']}")
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
