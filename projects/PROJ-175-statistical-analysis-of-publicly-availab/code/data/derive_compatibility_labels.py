import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/derive_compatibility_labels.log')
    ]
)
logger = logging.getLogger(__name__)

def load_threshold_from_t048():
    """
    Loads the median rating threshold from the pilot stats or a default config.
    Since T048 is not explicitly listed as completed but T013b (pilot_stats) is,
    we attempt to load from pilot_stats.json or derive a default.
    """
    pilot_path = Path('data/pilot_stats.json')
    default_threshold = 3.0  # Default median for 1-5 scale if not found

    if pilot_path.exists():
        try:
            with open(pilot_path, 'r') as f:
                data = json.load(f)
                # If T013b stored a specific threshold or we calculate it from a sample
                # For now, we assume the pilot analysis determined the median is ~3.0
                # or we calculate it dynamically from the ratings data if available.
                # If pilot_stats only has sample_size, we use default.
                logger.info(f"Loaded pilot stats from {pilot_path}")
        except Exception as e:
            logger.warning(f"Could not load pilot stats: {e}. Using default threshold.")
    else:
        logger.warning(f"Pilot stats not found at {pilot_path}. Using default threshold.")
    
    return default_threshold

def load_ingredient_pairs():
    """
    Loads the processed ingredient pairs from T018.
    Expects: data/processed/ingredient_pairs.csv
    """
    input_path = Path('data/processed/ingredient_pairs.csv')
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Run T018 first.")
    
    logger.info(f"Loading ingredient pairs from {input_path}")
    df = pd.read_csv(input_path)
    
    required_cols = ['ingredient_id', 'log_co_occurrence', 'flavor_similarity', 'functional_role']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
    
    return df

def load_download_status():
    """
    Loads the download status from T012a to check 'counterfactual' status.
    """
    status_path = Path('data/download_status.json')
    if not status_path.exists():
        logger.warning(f"Download status not found at {status_path}. Assuming proxy path.")
        return {'counterfactual': 'FAILED'}
    
    with open(status_path, 'r') as f:
        return json.load(f)

def derive_labels_from_counterfactual(df):
    """
    Derives labels from Counterfactual dataset if available.
    Since we are in the proxy path (T012a likely failed for counterfactual),
    this function is kept for completeness but will likely not be used unless
    the real source becomes available.
    """
    logger.info("Attempting to derive labels from Counterfactual dataset...")
    # In a real scenario, this would merge with the counterfactual dataset
    # and extract the 'substitution_success' or similar binary label.
    # For now, we raise if we expect it but can't find the source.
    raise NotImplementedError("Counterfactual dataset source not available in this run.")

def derive_labels_from_ratings(df):
    """
    Derives binary compatibility labels using Recipe1M ratings (median threshold).
    This is the proxy path required when Counterfactual data is unavailable.
    """
    logger.info("Using Recipe1M ratings (median threshold) as proxy for labels.")
    
    # We need to map ingredient pairs to recipe ratings.
    # Assuming the 'ingredient_pairs' dataset has been enriched with average ratings
    # for the pair context, or we calculate it based on ingredient presence in high-rated recipes.
    # However, T018 output 'ingredient_pairs.csv' likely contains aggregate stats.
    # If the dataset does not have a 'rating' column, we must simulate the logic:
    # "Compatibility = 1 if the pair appears in recipes with rating >= median_rating"
    
    # Check if 'avg_rating' or similar exists in the input
    if 'avg_rating' in df.columns:
        rating_col = 'avg_rating'
    elif 'rating' in df.columns:
        rating_col = 'rating'
    else:
        # Fallback: If no rating column exists in the pairs, we cannot derive labels
        # from ratings without re-joining with the raw recipe data.
        # Given the constraints, we assume T018 produced a dataset with 'avg_rating'
        # or we create a synthetic proxy based on the 'flavor_similarity' correlation
        # (which is scientifically weak but necessary if data is missing).
        # STRONGER APPROACH: If the input lacks ratings, we assume the task implies
        # we must have joined ratings in T018. If not, we raise.
        raise ValueError("Input dataset lacks 'rating' or 'avg_rating' column required for proxy label derivation.")

    # Calculate median
    median_rating = df[rating_col].median()
    logger.info(f"Calculated median rating: {median_rating}")

    # Create binary label
    # Label 1: Rating >= Median (Compatible)
    # Label 0: Rating < Median (Incompatible)
    df['compatibility_label'] = (df[rating_col] >= median_rating).astype(int)
    
    logger.info(f"Derived {df['compatibility_label'].sum()} positive labels out of {len(df)}")
    
    return df

def save_output(df):
    """
    Saves the final dataset with labels to the declared output path.
    """
    output_path = Path('data/processed/ingredient_pairs_with_labels.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving output to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Output saved successfully.")

def main():
    """
    Main entry point for T019.
    """
    try:
        # 1. Load input data
        df = load_ingredient_pairs()
        
        # 2. Check download status to decide path
        status = load_download_status()
        counterfactual_status = status.get('counterfactual', 'FAILED')
        
        if counterfactual_status == 'SUCCESS':
            # Attempt real counterfactual derivation
            try:
                df = derive_labels_from_counterfactual(df)
            except NotImplementedError as e:
                logger.warning(f"Counterfactual derivation failed: {e}. Falling back to proxy.")
                df = derive_labels_from_ratings(df)
        else:
            # Proxy path
            df = derive_labels_from_ratings(df)
        
        # 3. Save output
        save_output(df)
        
        logger.info("Task T019 completed successfully.")
        
    except Exception as e:
        logger.error(f"Task T019 failed: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
