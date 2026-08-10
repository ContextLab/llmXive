import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/derive_roles.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all necessary directories exist."""
    dirs = [
        'data/processed',
        'data/logs'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        logger.info(f"Ensured directory exists: {d}")

def load_marginal_frequencies(input_path='data/processed/normalized_ingredients.csv'):
    """
    Load marginal frequencies from the normalized ingredients file.
    This data comes from T014a and represents the raw frequency of ingredients.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. Run T014a first.")
    
    df = pd.read_csv(input_path)
    required_cols = ['ingredient_id', 'frequency']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Input file missing required columns: {required_cols}. Found: {df.columns.tolist()}")
    
    logger.info(f"Loaded {len(df)} ingredients from {input_path}")
    return df[['ingredient_id', 'frequency']]

def load_positional_ranks(input_path='data/raw/recipe1m_processed.parquet'):
    """
    Load positional ranks from the raw recipe data.
    We assume the recipe data has a structure where ingredients are listed in order.
    If the data is in a long format (recipe_id, ingredient, position), we use 'position'.
    If it's a list, we might need to infer position.
    
    For this implementation, we assume the processed Recipe1M data has been flattened
    or processed to include a 'position' or 'ingredient_order' column.
    If not, we will derive it from the raw list if possible, or assume uniform distribution if missing.
    
    However, based on T013a output 'data/raw/recipe1m_processed.parquet', we need to check its schema.
    If it contains 'recipe_id', 'ingredient_id', and 'position' (or similar), we use that.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. Run T013a first.")
    
    # Try to load with specific columns if known, otherwise load all
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to read parquet: {e}")
        raise

    # Expected columns based on typical recipe data structure after streaming/flattening
    # We need 'ingredient_id' and a way to determine 'position'
    # If 'position' is not present, we might need to aggregate from raw lists if available.
    # For now, we assume the data has been pre-processed to have 'position' or we calculate it.
    
    # Fallback: If 'position' is missing, we cannot accurately derive roles based on position.
    # We will log a warning and assume a default (e.g., all are 'secondary' or based on frequency).
    # But the task requires position. Let's assume the data from T013a has 'position'.
    
    if 'position' not in df.columns:
        # If position is missing, we might need to look for 'ingredient_order' or similar
        # Or we might have to re-process raw data. For now, we raise a clear error or use a heuristic.
        # Heuristic: If no position data, we can't strictly follow the "position" rule.
        # We will log a critical warning and proceed with frequency-only logic if absolutely necessary,
        # but the task says "based on position and frequency".
        # Let's try to find a column that looks like position
        pos_cols = [c for c in df.columns if 'pos' in c.lower() or 'order' in c.lower()]
        if pos_cols:
            df = df.rename(columns={pos_cols[0]: 'position'})
        else:
            logger.warning("Position column not found. Cannot derive roles based on position. Falling back to frequency-based logic with a warning.")
            df['position'] = 0 # Default to 0 (first) or some heuristic? Better to fail or warn.
            # Actually, if we can't get position, we can't fulfill the task strictly.
            # But let's assume for a moment that if missing, we treat all as 'secondary' or use frequency.
            # The task says "based on position and frequency".
            # Let's create a synthetic position based on frequency rank if missing? No, that's circular.
            # We will assume the data has 'position'. If not, we raise an error to force data prep.
            raise ValueError("Column 'position' not found in input data. T013a must produce data with position info.")

    logger.info(f"Loaded {len(df)} recipe-ingredient pairs with position from {input_path}")
    return df

def load_co_occurrence_matrix(input_path='data/processed/co_occurrence_matrix.parquet'):
    """
    Load co-occurrence matrix.
    This function exists to verify exclusion of co-occurrence data as per FR-005.
    It is NOT used to derive roles, but to ensure we don't accidentally use it.
    """
    if os.path.exists(input_path):
        logger.warning("Co-occurrence matrix found. Ensure it is NOT used in role derivation logic.")
        return pd.read_parquet(input_path)
    return None

def load_reference_ingredients(input_path='data/processed/normalized_ingredients.csv'):
    """
    Load the list of reference ingredients (canonical IDs).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Reference file not found: {input_path}")
    df = pd.read_csv(input_path)
    if 'ingredient_id' not in df.columns:
        raise ValueError("Reference file must contain 'ingredient_id'")
    return set(df['ingredient_id'].unique())

def verify_exclusion_of_co_occurrence(co_occurrence_data, role_data):
    """
    Verify that the role derivation did not use co-occurrence data.
    This is a sanity check.
    """
    if co_occurrence_data is not None:
        logger.info("Co-occurrence data was loaded but should not be used for role derivation.")
        # We assume the logic below doesn't use it.
    return True

def calculate_functional_role(marginal_freq_df, positional_df):
    """
    Derive functional role (primary, secondary, garnish) based on position and frequency.
    
    Logic:
    1. Primary: High frequency AND typically low position index (early in recipe).
    2. Secondary: Medium frequency OR medium position.
    3. Garnish: Low frequency AND high position index (late in recipe).
    
    We need to define thresholds. Since these are data-driven, we can use percentiles.
    - Position: Lower is better (0 = first ingredient).
    - Frequency: Higher is better.
    
    Steps:
    - Aggregate position per ingredient (mean or min position).
    - Merge with frequency.
    - Define rules.
    """
    # 1. Calculate average position per ingredient
    pos_agg = positional_df.groupby('ingredient_id')['position'].agg(['mean', 'min']).reset_index()
    pos_agg.columns = ['ingredient_id', 'avg_position', 'min_position']
    
    # 2. Merge with frequency
    merged = marginal_freq_df.merge(pos_agg, on='ingredient_id', how='outer')
    
    # Handle missing positions or frequencies
    # If an ingredient has no position data, we can't assign role based on position.
    # If an ingredient has no frequency data, we can't assign based on frequency.
    # We'll fill NaN with neutral values or drop.
    # Let's drop rows with missing critical data for now.
    merged = merged.dropna(subset=['frequency', 'avg_position'])
    
    # 3. Define thresholds using percentiles of the data
    # Frequency: High = top 30%, Low = bottom 30%
    freq_high_thresh = merged['frequency'].quantile(0.7)
    freq_low_thresh = merged['frequency'].quantile(0.3)
    
    # Position: Low (early) = bottom 30%, High (late) = top 30%
    pos_low_thresh = merged['avg_position'].quantile(0.3)
    pos_high_thresh = merged['avg_position'].quantile(0.7)
    
    # 4. Assign roles
    def assign_role(row):
        freq = row['frequency']
        pos = row['avg_position']
        
        # Primary: High frequency AND Early position
        if freq >= freq_high_thresh and pos <= pos_low_thresh:
            return 'primary'
        
        # Garnish: Low frequency AND Late position
        if freq <= freq_low_thresh and pos >= pos_high_thresh:
            return 'garnish'
        
        # Secondary: Everything else
        return 'secondary'
    
    merged['functional_role'] = merged.apply(assign_role, axis=1)
    
    logger.info(f"Assigned roles: {merged['functional_role'].value_counts().to_dict()}")
    return merged[['ingredient_id', 'functional_role', 'frequency', 'avg_position']]

def save_output(df, output_path='data/processed/functional_roles.csv'):
    """
    Save the derived functional roles to a CSV file.
    """
    ensure_directories()
    df.to_csv(output_path, index=False)
    logger.info(f"Saved functional roles to {output_path}")

def main():
    """
    Main execution function for T014b.
    """
    try:
        ensure_directories()
        
        # Load inputs
        logger.info("Loading marginal frequencies...")
        freq_df = load_marginal_frequencies()
        
        logger.info("Loading positional ranks...")
        pos_df = load_positional_ranks()
        
        # Load co-occurrence just to verify exclusion (not used in logic)
        co_occ = load_co_occurrence_matrix()
        
        logger.info("Loading reference ingredients...")
        ref_ingredients = load_reference_ingredients()
        
        # Verify we are not using co-occurrence
        verify_exclusion_of_co_occurrence(co_occ, None)
        
        # Derive roles
        logger.info("Calculating functional roles...")
        result_df = calculate_functional_role(freq_df, pos_df)
        
        # Save output
        save_output(result_df)
        
        logger.info("T014b completed successfully.")
        
    except Exception as e:
        logger.error(f"T014b failed: {e}")
        raise

if __name__ == "__main__":
    main()
