"""
T017: Functional Role Derivation.

Derives functional role using 'positional rank' and 'marginal frequency' only.
Explicitly excludes 'co-occurrence frequency' from derivation logic (FR-005).
Checks for circularity correlation between derived role and co-occurrence frequency.
"""
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
        logging.FileHandler("data/role_derivation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

def load_marginal_frequencies():
    """
    Load marginal counts from T013b.
    Input: data/raw/marginal_counts.parquet
    """
    path = RAW_DIR / "marginal_counts.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    
    df = pd.read_parquet(path)
    logger.info(f"Loaded marginal counts: {len(df)} ingredients")
    return df

def load_positional_ranks():
    """
    Load normalized ingredients which contain positional rank info from T014.
    Input: data/processed/normalized_ingredients.parquet
    Note: The normalized ingredients file should contain 'ingredient_id' and
          potentially 'positional_rank' or 'recipe_length' if computed in T014.
          If not, we compute it here assuming the file contains recipe-level
          sequence data or we derive it from the marginal counts context.
    
    Based on T014 description, it outputs normalized_ingredients.parquet.
    We assume it contains 'ingredient_id', 'positional_rank' (1-based index / recipe length).
    If 'positional_rank' is missing, we compute a proxy or raise error if data structure unknown.
    """
    path = PROCESSED_DIR / "normalized_ingredients.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    
    df = pd.read_parquet(path)
    logger.info(f"Loaded normalized ingredients: {len(df)} rows")
    
    # Ensure we have the necessary columns for positional rank
    # If the file is ingredient-level aggregated, we might need to derive rank differently.
    # Assuming the file contains 'ingredient_id' and 'positional_rank' as per T014 output spec.
    if 'positional_rank' not in df.columns:
        # Fallback: If the data is just a list of unique ingredients without rank,
        # we cannot derive a meaningful positional rank without recipe-level data.
        # However, T014 description says it outputs 'normalized_ingredients.parquet'.
        # We will assume it has 'positional_rank' or 'recipe_length' and 'index_in_recipe'.
        # If missing, we try to infer or fail.
        logger.warning("positional_rank column missing in normalized_ingredients.parquet. Attempting fallback.")
        # If we only have unique ingredients, we can't compute a specific rank per occurrence.
        # We might need to join with raw data or assume a default.
        # For now, we raise an error if the expected structure is missing.
        raise ValueError("Expected 'positional_rank' column in normalized_ingredients.parquet but it is missing.")
    
    return df

def load_co_occurrence_matrix():
    """
    Load co-occurrence matrix to check for circularity correlation.
    Input: data/processed/co_occurrence_matrix.parquet (from T015)
    """
    path = PROCESSED_DIR / "co_occurrence_matrix.parquet"
    if not path.exists():
        logger.warning(f"Co-occurrence matrix not found at {path}. Skipping circularity check.")
        return None
    
    df = pd.read_parquet(path)
    logger.info(f"Loaded co-occurrence matrix: {len(df)} pairs")
    return df

def calculate_functional_role(marginal_df, normalized_df):
    """
    Calculate functional role based on:
    1. Positional rank (1-based index / recipe length)
    2. Marginal frequency (frequency of single ingredient)
    
    Formula: 
    role_score = alpha * normalized_pos_rank + beta * normalized_marginal_freq
    We will use equal weights (0.5, 0.5) for simplicity unless specified otherwise.
    """
    # Merge marginal frequencies with normalized ingredients
    # normalized_df should have 'ingredient_id' and 'positional_rank'
    # marginal_df should have 'ingredient_id' and 'count' (or 'frequency')
    
    if 'count' in marginal_df.columns:
        marginal_df = marginal_df.rename(columns={'count': 'marginal_freq'})
    elif 'frequency' not in marginal_df.columns:
        # Assume count is the frequency
        marginal_df['marginal_freq'] = marginal_df.iloc[:, 1] if len(marginal_df.columns) > 1 else 0
    
    # Ensure we have the right columns
    if 'ingredient_id' not in marginal_df.columns:
        raise ValueError("marginal_counts.parquet must contain 'ingredient_id'")
    
    merged_df = pd.merge(normalized_df, marginal_df[['ingredient_id', 'marginal_freq']], on='ingredient_id', how='left')
    
    # Normalize positional rank (assuming it's between 0 and 1 or 1 and N)
    # If it's 1-based index / length, it should be between 0 and 1.
    # If it's raw index, we normalize it.
    if merged_df['positional_rank'].max() > 1.0:
        # Normalize to [0, 1]
        merged_df['normalized_pos_rank'] = merged_df['positional_rank'] / merged_df['positional_rank'].max()
    else:
        merged_df['normalized_pos_rank'] = merged_df['positional_rank']
    
    # Normalize marginal frequency
    max_freq = merged_df['marginal_freq'].max()
    if max_freq > 0:
        merged_df['normalized_marginal_freq'] = merged_df['marginal_freq'] / max_freq
    else:
        merged_df['normalized_marginal_freq'] = 0.0
    
    # Calculate functional role score
    # Using equal weights
    alpha = 0.5
    beta = 0.5
    merged_df['functional_role_score'] = (alpha * merged_df['normalized_pos_rank']) + (beta * merged_df['normalized_marginal_freq'])
    
    return merged_df

def verify_exclusion_of_co_occurrence(role_df, co_occurrence_df):
    """
    Verify that co-occurrence frequency was NOT used in derivation.
    Check correlation between derived role and co-occurrence frequency.
    If correlation > 0.1, flag for exclusion in T023.
    """
    if co_occurrence_df is None:
        return {"correlation": None, "flagged": False, "reason": "Co-occurrence data not available"}
    
    # We need to map role scores to pairs or aggregate.
    # For simplicity, we compute correlation between mean role score per ingredient
    # and mean co-occurrence frequency per ingredient (or total co-occurrence).
    
    # Aggregate role scores by ingredient_id
    role_by_ingredient = role_df.groupby('ingredient_id')['functional_role_score'].mean().reset_index()
    role_by_ingredient = role_by_ingredient.rename(columns={'functional_role_score': 'mean_role_score'})
    
    # Aggregate co-occurrence by ingredient_id (sum of counts for each ingredient in pairs)
    # co_occurrence_df likely has 'ingredient_id_1', 'ingredient_id_2', 'count'
    # We sum counts for each ingredient appearing in either column.
    if 'ingredient_id_1' in co_occurrence_df.columns and 'ingredient_id_2' in co_occurrence_df.columns:
        # Reshape to long format
        long_df = pd.concat([
            co_occurrence_df[['ingredient_id_1', 'count']].rename(columns={'ingredient_id_1': 'ingredient_id'}),
            co_occurrence_df[['ingredient_id_2', 'count']].rename(columns={'ingredient_id_2': 'ingredient_id'})
        ])
        co_occurrence_by_ingredient = long_df.groupby('ingredient_id')['count'].sum().reset_index()
        co_occurrence_by_ingredient = co_occurrence_by_ingredient.rename(columns={'count': 'total_co_occurrence'})
        
        # Merge
        merged = pd.merge(role_by_ingredient, co_occurrence_by_ingredient, on='ingredient_id', how='inner')
        
        if len(merged) < 3:
            return {"correlation": None, "flagged": False, "reason": "Insufficient data for correlation"}
        
        # Calculate Pearson correlation
        corr = merged['mean_role_score'].corr(merged['total_co_occurrence'])
        
        flagged = False
        if corr is not None and abs(corr) > 0.1:
            flagged = True
            logger.warning(f"Circularity detected: Correlation between role and co-occurrence is {corr:.4f} (>0.1). Flagged for T023.")
        else:
            logger.info(f"Circularity check passed: Correlation is {corr:.4f} (<=0.1).")
        
        return {
            "correlation": float(corr) if corr is not None else None,
            "flagged": flagged,
            "reason": "Correlation > 0.1" if flagged else "Correlation <= 0.1"
        }
    else:
        return {"correlation": None, "flagged": False, "reason": "Co-occurrence dataframe structure unknown"}

def save_output(role_df, circularity_check):
    """
    Save the output to data/processed/ingredient_roles_residuals.parquet
    and log the circularity check.
    """
    output_path = PROCESSED_DIR / "ingredient_roles_residuals.parquet"
    
    # Ensure directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save role dataframe
    role_df.to_parquet(output_path, index=False)
    logger.info(f"Saved functional role derivation to {output_path}")
    
    # Save circularity check log
    log_path = PROCESSED_DIR / "circularity_check_log.json"
    with open(log_path, 'w') as f:
        json.dump(circularity_check, f, indent=2)
    logger.info(f"Saved circularity check log to {log_path}")

def main():
    logger.info("Starting T017: Functional Role Derivation")
    
    try:
        # Load inputs
        marginal_df = load_marginal_frequencies()
        normalized_df = load_positional_ranks()
        co_occurrence_df = load_co_occurrence_matrix()
        
        # Calculate functional role
        role_df = calculate_functional_role(marginal_df, normalized_df)
        
        # Verify exclusion of co-occurrence (circularity check)
        circularity_check = verify_exclusion_of_co_occurrence(role_df, co_occurrence_df)
        
        # Save outputs
        save_output(role_df, circularity_check)
        
        logger.info("T017 completed successfully.")
        
    except Exception as e:
        logger.error(f"T017 failed: {e}")
        raise

if __name__ == "__main__":
    main()
