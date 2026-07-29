"""
Feature Save Module (T016).
Merges linguistic features with validation data and saves the final feature-rich dataset.
Ensures `data/processed/features.csv` is written to disk with all required columns.
"""
import os
import csv
import logging
import sys
from pathlib import Path
import pandas as pd

from config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def ensure_feature_data_exists():
    """Verify that intermediate feature data exists before proceeding."""
    config = get_config()
    feature_path = Path(config['paths']['processed']) / 'features_raw.csv'
    
    if not feature_path.exists():
        raise FileNotFoundError(
            f"Intermediate feature data not found at {feature_path}. "
            "Please run feature extraction (T014) first."
        )
    return feature_path

def ensure_validation_data_exists():
    """Verify that human pilot validation data exists."""
    config = get_config()
    validation_path = Path(config['paths']['interim']) / 'human_pilot_cleaned.csv'
    
    if not validation_path.exists():
        # This is optional for T016, but we log a warning if missing
        logger.warning(f"Validation data not found at {validation_path}. "
                     "Proceeding without human pilot correlation data.")
        return None
    return validation_path

def merge_and_save_features(feature_path, validation_path=None):
    """
    Merge linguistic features with optional validation data and save to final CSV.
    
    Args:
        feature_path: Path to raw features CSV
        validation_path: Optional path to cleaned human pilot data
    
    Returns:
        Path to the saved final features CSV
    """
    logger.info(f"Loading features from {feature_path}")
    df_features = pd.read_csv(feature_path)
    
    # Ensure required columns exist
    required_cols = ['prompt_id', 'modal_verb_freq', 'imperative_ratio', 
                    'citation_density', 'is_ratio_undefined']
    missing_cols = [col for col in required_cols if col not in df_features.columns]
    if missing_cols:
        raise ValueError(f"Feature file missing required columns: {missing_cols}")
    
    df_final = df_features.copy()
    
    if validation_path:
        logger.info(f"Loading validation data from {validation_path}")
        df_validation = pd.read_csv(validation_path)
        
        # Aggregate rater scores by prompt_id
        if 'authority_density_score' in df_validation.columns:
            agg_scores = df_validation.groupby('prompt_id')['authority_density_score'].mean().reset_index()
            agg_scores.rename(columns={'authority_density_score': 'human_authority_density'}, inplace=True)
            df_final = df_final.merge(agg_scores, on='prompt_id', how='left')
            logger.info(f"Merged human pilot data. Rows with scores: {df_final['human_authority_density'].notna().sum()}")
    
    # Save to final location
    config = get_config()
    output_path = Path(config['paths']['processed']) / 'features.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_final.to_csv(output_path, index=False)
    logger.info(f"Saved final feature-rich dataset to {output_path}")
    logger.info(f"Dataset shape: {df_final.shape}")
    logger.info(f"Columns: {list(df_final.columns)}")
    
    return output_path

def run_feature_save_pipeline():
    """Execute the full feature save pipeline (T016)."""
    logger.info("Starting Feature Save Pipeline (T016)")
    
    feature_path = ensure_feature_data_exists()
    validation_path = ensure_validation_data_exists()
    
    output_path = merge_and_save_features(feature_path, validation_path)
    
    # Verify output
    if not output_path.exists():
        raise RuntimeError("Failed to write features.csv output file.")
    
    df_check = pd.read_csv(output_path)
    if df_check.empty:
        raise RuntimeError("Output features.csv is empty.")
    
    logger.info("Feature Save Pipeline completed successfully.")
    return output_path

def main():
    """Entry point for T016."""
    try:
        run_feature_save_pipeline()
    except Exception as e:
        logger.error(f"Feature save pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
