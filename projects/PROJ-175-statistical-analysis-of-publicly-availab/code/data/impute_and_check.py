"""
Task T018: Imputation & Bias Check
Handles missing values in embeddings, similarity scores, and functional roles.
Imputes missing similarity scores with 0.
Logs exclusion counts.
Outputs: data/processed/ingredient_pairs.csv
"""
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure output directories exist."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def load_processed_data():
    """
    Load the necessary intermediate data files produced by T016 and T017.
    Expected files:
      - data/processed/similarity_scores.parquet (from T016)
      - data/processed/functional_roles.parquet (from T017)
    """
    output_dir = Path("data/processed")
    
    sim_file = output_dir / "similarity_scores.parquet"
    role_file = output_dir / "functional_roles.parquet"

    if not sim_file.exists():
        raise FileNotFoundError(f"Required file not found: {sim_file}. Run T016 first.")
    if not role_file.exists():
        raise FileNotFoundError(f"Required file not found: {role_file}. Run T017 first.")

    logger.info(f"Loading similarity scores from {sim_file}")
    df_sim = pd.read_parquet(sim_file)
    
    logger.info(f"Loading functional roles from {role_file}")
    df_roles = pd.read_parquet(role_file)

    return df_sim, df_roles

def merge_datasets(df_sim, df_roles):
    """
    Merge similarity scores and functional roles on ingredient pairs.
    Assumes both datasets share 'ingredient_a' and 'ingredient_b' columns.
    """
    # Identify common columns for merging
    merge_keys = ['ingredient_a', 'ingredient_b']
    
    # Check if merge keys exist in both
    if not all(col in df_sim.columns for col in merge_keys):
        missing = [col for col in merge_keys if col not in df_sim.columns]
        raise ValueError(f"Similarity scores missing merge keys: {missing}")
    if not all(col in df_roles.columns for col in merge_keys):
        missing = [col for col in merge_keys if col not in df_roles.columns]
        raise ValueError(f"Functional roles missing merge keys: {missing}")

    # Perform outer join to capture all pairs, then we can see what's missing
    df_merged = pd.merge(
        df_sim, 
        df_roles, 
        on=merge_keys, 
        how='outer', 
        suffixes=('_sim', '_role')
    )

    logger.info(f"Merged dataset shape: {df_merged.shape}")
    return df_merged

def impute_missing(df_merged):
    """
    Handle missing values:
    1. Impute missing 'flavor_similarity' (or similar score column) with 0.
    2. Identify rows where functional role is missing (excluded from analysis).
    3. Log exclusion counts.
    """
    # Identify the similarity column. T016 outputs 'similarity_scores.parquet'.
    # We need to find the column name that holds the similarity value.
    # Assuming standard schema: 'flavor_similarity' or 'similarity'.
    # Let's look for a column that is float and likely the score.
    similarity_col = None
    for col in df_merged.columns:
        if 'similarity' in col.lower() or 'score' in col.lower():
            # Avoid column names that are obviously IDs
            if 'id' not in col.lower():
                similarity_col = col
                break
    
    if similarity_col is None:
        # Fallback: assume 'flavor_similarity' based on T007 schema
        similarity_col = 'flavor_similarity'
        if similarity_col not in df_merged.columns:
            # If it doesn't exist, create it as NaN to be imputed
            df_merged[similarity_col] = np.nan

    # Count missing before imputation
    missing_sim_count = df_merged[similarity_col].isna().sum()
    missing_role_count = df_merged['functional_role'].isna().sum() if 'functional_role' in df_merged.columns else 0

    logger.info(f"Missing similarity scores before imputation: {missing_sim_count}")
    logger.info(f"Missing functional roles before imputation: {missing_role_count}")

    # Impute similarity scores with 0
    # "Impute missing similarity scores with 0"
    df_merged[similarity_col] = df_merged[similarity_col].fillna(0.0)

    # For functional roles, we cannot impute with a meaningful value without more logic.
    # The task says "Handle missing values... Log exclusion counts."
    # We will drop rows where functional_role is missing, as they cannot be used for modeling.
    initial_rows = len(df_merged)
    df_final = df_merged.dropna(subset=['functional_role'])
    excluded_rows = initial_rows - len(df_final)

    logger.info(f"Excluded {excluded_rows} rows due to missing functional_role.")

    # Log exclusion counts to a JSON file
    log_data = {
        "task": "T018",
        "description": "Imputation & Bias Check",
        "missing_similarity_imputed": int(missing_sim_count),
        "missing_role_excluded": int(excluded_rows),
        "total_rows_before": int(initial_rows),
        "total_rows_after": int(len(df_final)),
        "similarity_column_used": similarity_col,
        "imputation_value": 0.0
    }

    log_path = Path("data/processed/imputation_log.json")
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Imputation log written to {log_path}")

    return df_final

def save_output(df_final, output_dir):
    """
    Save the final dataset to data/processed/ingredient_pairs.csv.
    """
    output_path = output_dir / "ingredient_pairs.csv"
    df_final.to_csv(output_path, index=False)
    logger.info(f"Final dataset saved to {output_path}")
    return output_path

def main():
    """Main entry point for T018."""
    try:
        logger.info("Starting T018: Imputation & Bias Check")
        
        # Ensure directories
        output_dir = ensure_directories()
        
        # Load data
        df_sim, df_roles = load_processed_data()
        
        # Merge
        df_merged = merge_datasets(df_sim, df_roles)
        
        # Impute and check
        df_final = impute_missing(df_merged)
        
        # Save output
        save_output(df_final, output_dir)
        
        logger.info("T018 completed successfully.")
        
    except Exception as e:
        logger.error(f"T018 failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
