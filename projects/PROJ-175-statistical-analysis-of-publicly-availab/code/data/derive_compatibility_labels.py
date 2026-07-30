"""
Task T013e: Derive Compatibility Labels
----------------------------------------
Uses the median rating (or selected threshold from T048) to create a binary
compatibility_label. Fails if the dataset is empty.

Output: data/processed/compatibility_labels.parquet
Dependencies: T013a (raw data), T048 (threshold sensitivity), T013b (marginal counts)
"""
import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_T048_PATH = PROJECT_ROOT / "data" / "threshold_sensitivity.json"
OUTPUT_PATH = DATA_PROCESSED_DIR / "compatibility_labels.parquet"
LOG_PATH = DATA_PROCESSED_DIR / "compatibility_labels_log.json"

def load_threshold_from_t048():
    """
    Load the selected threshold from T048 (threshold_sensitivity.json).
    If T048 hasn't run or is missing, fall back to median calculation from raw data.
    """
    if DATA_T048_PATH.exists():
        try:
            with open(DATA_T048_PATH, 'r') as f:
                t048_data = json.load(f)
            
            # Prefer the 'selected_threshold' if explicitly set in T048
            if 'selected_threshold' in t048_data:
                logger.info(f"Using threshold from T048: {t048_data['selected_threshold']}")
                return t048_data['selected_threshold']
            elif 'median_rating' in t048_data:
                logger.info(f"Using median_rating from T048: {t048_data['median_rating']}")
                return t048_data['median_rating']
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not parse T048 output: {e}. Falling back to median calculation.")
    
    # Fallback: calculate median from raw ratings if available
    # We look for a file that contains ratings. T013a produces recipe1m_raw.parquet
    raw_recipe_path = DATA_RAW_DIR / "recipe1m_raw.parquet"
    if raw_recipe_path.exists():
        try:
            df = pd.read_parquet(raw_recipe_path)
            if 'rating' in df.columns:
                median_val = df['rating'].median()
                logger.info(f"Calculated median rating from raw data: {median_val}")
                return median_val
            else:
                logger.warning("Raw data has no 'rating' column. Cannot calculate median.")
        except Exception as e:
            logger.warning(f"Failed to load raw data for median calculation: {e}")
    
    # Final fallback: raise error
    raise FileNotFoundError(
        "Could not determine a threshold. "
        "Run T048 first to generate threshold_sensitivity.json with a selected_threshold, "
        "or ensure data/raw/recipe1m_raw.parquet contains a 'rating' column."
    )

def main():
    logger.info("Starting T013e: Derive Compatibility Labels")

    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Determine threshold
    threshold = load_threshold_from_t048()

    # 2. Load the processed data that contains ratings
    # We expect T013b/T014 to have produced a file with ingredient pairs and ratings.
    # Based on the task flow, the most likely candidate is a merged file or we need to
    # join raw data with processed ingredient lists.
    # However, T013b produces marginal_counts. T014 produces normalized_ingredients.
    # The most direct source for ratings is the raw dataset (T013a).
    # We will load the raw data, filter for valid ratings, and derive labels.
    
    raw_recipe_path = DATA_RAW_DIR / "recipe1m_raw.parquet"
    if not raw_recipe_path.exists():
        raise FileNotFoundError(f"Raw data not found at {raw_recipe_path}. Run T013a first.")

    logger.info(f"Loading raw data from {raw_recipe_path}")
    try:
        df_raw = pd.read_parquet(raw_recipe_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load raw data: {e}")

    if df_raw.empty:
        logger.error("Dataset is empty. Failing as per task requirement.")
        raise ValueError("Dataset is empty. Cannot derive compatibility labels.")

    # Check for rating column
    if 'rating' not in df_raw.columns:
        raise ValueError("Raw data does not contain a 'rating' column. Cannot derive labels.")

    # 3. Derive binary compatibility_label
    # Logic: rating >= threshold -> 1 (compatible), else 0
    # We assume higher ratings imply better compatibility/substitution potential in this context.
    # If the rating scale is inverted (lower is better), the task spec would need to clarify.
    # Standard assumption: Higher rating = better.
    
    logger.info(f"Applying threshold: {threshold}")
    df_raw['compatibility_label'] = (df_raw['rating'] >= threshold).astype(int)

    # 4. Select relevant columns for output
    # We keep ingredient identifiers and the new label.
    # Assuming 'ingredient_id' or similar exists. If not, we keep all cols except 'rating' if we want to save space,
    # but let's be explicit.
    cols_to_keep = [c for c in df_raw.columns if c != 'rating'] # Remove raw rating if not needed in output
    if 'rating' in cols_to_keep:
        cols_to_keep.remove('rating')
    
    # Ensure we have at least the label and an ID
    if 'compatibility_label' not in df_raw.columns:
        raise RuntimeError("Failed to create compatibility_label column.")

    # If there's no explicit ID, we might need to create one or keep the index.
    # Let's assume 'ingredient_id' or 'id' exists, otherwise we reset index.
    id_col = None
    for candidate in ['ingredient_id', 'id', 'ingredient']:
        if candidate in df_raw.columns:
            id_col = candidate
            break
    
    output_df = df_raw[['compatibility_label']]
    if id_col:
        output_df.insert(0, id_col, df_raw[id_col])
    else:
        output_df.insert(0, 'index', output_df.index)

    # 5. Save output
    logger.info(f"Saving compatibility labels to {OUTPUT_PATH}")
    output_df.to_parquet(OUTPUT_PATH, index=False)

    # 6. Log the operation
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "task": "T013e",
        "status": "SUCCESS",
        "threshold_used": threshold,
        "threshold_source": "T048" if DATA_T048_PATH.exists() else "calculated_from_raw",
        "total_rows": len(output_df),
        "label_distribution": {
            "0": int((output_df['compatibility_label'] == 0).sum()),
            "1": int((output_df['compatibility_label'] == 1).sum())
        },
        "output_file": str(OUTPUT_PATH)
    }

    with open(LOG_PATH, 'w') as f:
        json.dump(log_entry, f, indent=2)

    logger.info(f"T013e completed successfully. Output: {OUTPUT_PATH}")
    print(f"Successfully derived {len(output_df)} compatibility labels.")
    print(f"Threshold: {threshold}")
    print(f"Positive labels: {log_entry['label_distribution']['1']}")
    print(f"Negative labels: {log_entry['label_distribution']['0']}")

if __name__ == "__main__":
    main()