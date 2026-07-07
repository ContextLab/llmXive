import argparse
import logging
import sys
import json
from pathlib import Path
import pandas as pd
from scipy.stats import shapiro
from src.config import get_seed, set_seed
from src.utils.data_loader import fetch_text, load_ratings, validate_schemas, merge_features_and_ratings
from src.utils.edge_case_handler import handle_edge_cases, get_exclusion_summary

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_extraction_mode(args):
    """
    Orchestrate the extraction of linguistic features and perform skewness validation.
    
    1. Load text data and ratings.
    2. Validate schemas.
    3. Handle edge cases (empty/short texts, missing ratings).
    4. Extract features (pronoun rate, hedge density, valence score).
    5. Merge features with ratings.
    6. Perform Shapiro-Wilk test for skewness on each numeric feature.
    7. Write extraction_flags.json to data/derived/.
    8. Write features.csv to data/processed/.
    """
    logger.info("Starting extraction mode with validation.")
    
    # Set seed for reproducibility
    seed = get_seed()
    set_seed(seed)
    logger.info(f"Random seed set to: {seed}")

    # Paths
    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    derived_dir = data_dir / "derived"
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    derived_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    try:
        logger.info("Loading text data...")
        df_text = fetch_text()
        logger.info(f"Loaded {len(df_text)} conversations.")
        
        logger.info("Loading ratings...")
        df_ratings = load_ratings()
        logger.info(f"Loaded {len(df_ratings)} ratings.")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # 2. Validate Schemas
    try:
        logger.info("Validating data schemas...")
        validate_schemas(df_text, df_ratings)
        logger.info("Schemas validated successfully.")
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        sys.exit(1)

    # 3. Handle Edge Cases
    logger.info("Handling edge cases...")
    df_clean, exclusions = handle_edge_cases(df_text, df_ratings)
    if exclusions:
        summary = get_exclusion_summary(exclusions)
        logger.warning(f"Excluded {len(exclusions)} records due to edge cases.")
        logger.debug(f"Exclusion summary: {summary}")
    
    if df_clean.empty:
        logger.error("No valid data remaining after edge case handling.")
        sys.exit(1)

    # 4. Extract Features
    # Importing locally to avoid circular dependencies if any, 
    # though structure suggests these are independent modules.
    from src.extraction.pronoun_extractor import extract_pronoun_features
    from src.extraction.hedge_extractor import extract_hedge_features
    from src.extraction.sentiment_analyzer import extract_sentiment_features

    logger.info("Extracting pronoun features...")
    df_features = extract_pronoun_features(df_clean)
    
    logger.info("Extracting hedge features...")
    df_features = extract_hedge_features(df_features)
    
    logger.info("Extracting sentiment features...")
    df_features = extract_sentiment_features(df_features)

    # 5. Merge with Ratings
    logger.info("Merging features with ratings...")
    df_merged = merge_features_and_ratings(df_features, df_ratings)
    
    if df_merged.empty:
        logger.error("Merged dataset is empty. Cannot proceed with analysis.")
        sys.exit(1)

    # 6. Perform Skewness Validation (Shapiro-Wilk)
    logger.info("Performing Shapiro-Wilk skewness tests...")
    feature_cols = ['pronoun_rate', 'hedge_density', 'valence_score']
    extraction_flags = []

    for col in feature_cols:
        if col not in df_merged.columns:
            logger.warning(f"Column {col} not found in merged data. Skipping.")
            continue
        
        data_series = df_merged[col].dropna()
        if len(data_series) < 3:
            logger.warning(f"Not enough data points for {col} to run Shapiro-Wilk test.")
            continue

        try:
            stat, p_value = shapiro(data_series)
            is_skewed = p_value < 0.05
            
            # Determine suggested transformation
            suggested_transformation = "none"
            if is_skewed:
                # Simple heuristic: if p < 0.05, suggest log or sqrt depending on skew direction
                # Shapiro doesn't give direction, but usually log is safe for right skew
                # For this task, we'll suggest a generic transformation
                suggested_transformation = "log" 
            
            flag_entry = {
                "feature_name": col,
                "p_value": float(p_value),
                "is_skewed": bool(is_skewed),
                "suggested_transformation": suggested_transformation
            }
            extraction_flags.append(flag_entry)
            logger.info(f"Feature {col}: p={p_value:.4f}, skewed={is_skewed}, transform={suggested_transformation}")
            
        except Exception as e:
            logger.error(f"Error running Shapiro-Wilk test on {col}: {e}")
            # Still record a failure flag if possible, or skip
            extraction_flags.append({
                "feature_name": col,
                "p_value": None,
                "is_skewed": None,
                "suggested_transformation": "error"
            })

    # 7. Write extraction_flags.json
    flags_path = derived_dir / "extraction_flags.json"
    with open(flags_path, 'w') as f:
        json.dump(extraction_flags, f, indent=2)
    logger.info(f"Skewness validation flags written to {flags_path}")

    # 8. Write features.csv
    features_path = processed_dir / "features.csv"
    df_merged.to_csv(features_path, index=False)
    logger.info(f"Extracted features written to {features_path}")

    return df_merged

def main():
    parser = argparse.ArgumentParser(description="Linguistic Feature Extraction Pipeline")
    parser.add_argument('--mode', type=str, required=True, choices=['extraction'],
                        help="Operation mode: 'extraction'")
    parser.add_argument('--seed', type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    if args.mode == 'extraction':
        run_extraction_mode(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()