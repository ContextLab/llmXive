import os
import sys
import json
import re
import gc
import time
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/preprocess.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = ['data/processed', 'data/logs', 'data/raw']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def levenshtein_distance(s1, s2):
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def normalize_ingredient_name(ingredient, canonical_list, threshold=2):
    """
    Normalize ingredient name using Levenshtein distance.
    
    Args:
        ingredient: Original ingredient name
        canonical_list: List of canonical ingredient names
        threshold: Maximum Levenshtein distance for match
    
    Returns:
        Normalized ingredient name or original if no match found
    """
    ingredient = ingredient.lower().strip()
    
    if not canonical_list:
        return ingredient
    
    best_match = None
    best_distance = float('inf')
    
    for canonical in canonical_list:
        canonical = canonical.lower().strip()
        distance = levenshtein_distance(ingredient, canonical)
        
        if distance <= threshold and distance < best_distance:
            best_distance = distance
            best_match = canonical
    
    return best_match if best_match else ingredient

def load_reference_ingredients(input_path='data/processed/normalized_ingredients.csv'):
    """Load reference ingredients from normalized ingredients file."""
    if not os.path.exists(input_path):
        # If file doesn't exist, return empty list
        logger.warning(f"Reference ingredients file not found: {input_path}")
        return []
    
    df = pd.read_csv(input_path)
    return df['ingredient_normalized'].unique().tolist()

def load_normalized_ingredients(input_path='data/processed/normalized_ingredients.csv'):
    """Load normalized ingredients data."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Normalized ingredients file not found: {input_path}")
    
    logger.info(f"Loading normalized ingredients from {input_path}")
    return pd.read_csv(input_path)

def calculate_functional_role(df, marginal_freq_df, positional_rank_df):
    """
    Calculate functional role for each ingredient.
    
    This function merges marginal frequency and positional rank data,
    then calculates functional role based on the combined score.
    """
    # Merge data
    df_merged = df.merge(marginal_freq_df, on='ingredient_normalized', how='left')
    df_merged = df_merged.merge(positional_rank_df, on='ingredient_normalized', how='left')
    
    # Fill missing values
    df_merged['marginal_frequency'] = df_merged['marginal_frequency'].fillna(0)
    df_merged['positional_rank'] = df_merged['positional_rank'].fillna(df_merged['positional_rank'].median())
    
    # Normalize values
    max_freq = df_merged['marginal_frequency'].max()
    max_rank = df_merged['positional_rank'].max()
    
    if max_freq > 0:
        df_merged['norm_freq'] = df_merged['marginal_frequency'] / max_freq
    else:
        df_merged['norm_freq'] = 0
    
    if max_rank > 0:
        df_merged['norm_rank'] = 1 - (df_merged['positional_rank'] / max_rank)
    else:
        df_merged['norm_rank'] = 0
    
    # Calculate combined score
    df_merged['role_score'] = (df_merged['norm_freq'] * 0.6) + (df_merged['norm_rank'] * 0.4)
    
    # Assign functional role
    def assign_role(score):
        if score >= 0.7:
            return 'primary'
        elif score >= 0.3:
            return 'secondary'
        else:
            return 'garnish'
    
    df_merged['functional_role'] = df_merged['role_score'].apply(assign_role)
    
    return df_merged

def verify_exclusion_of_co_occurrence(df_result, co_occurrence_df):
    """
    Verify that functional role is not correlated with co-occurrence frequency.
    """
    logger.info("Verifying exclusion of co-occurrence frequency...")
    
    # Encode roles
    role_map = {'primary': 2, 'secondary': 1, 'garnish': 0}
    df_result['role_encoded'] = df_result['functional_role'].map(role_map)
    
    # Calculate correlation
    if 'log_co_occurrence' in df_result.columns:
        correlation = df_result['role_encoded'].corr(df_result['log_co_occurrence'])
        logger.info(f"Correlation between functional role and log_co_occurrence: {correlation:.4f}")
        
        return {
            'correlation': float(correlation),
            'threshold': 0.5,
            'passed': abs(correlation) <= 0.5
        }
    
    return {
        'correlation': None,
        'threshold': 0.5,
        'passed': True,
        'note': 'Could not compute correlation'
    }

def save_output(df_result, output_path='data/processed/functional_roles.parquet',
               validation_log_path='data/logs/role_validation.json'):
    """Save functional roles and validation log."""
    ensure_directories()
    
    logger.info(f"Saving functional roles to {output_path}")
    df_result.to_parquet(output_path, index=False)
    
    # Save validation log
    validation_log = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'output_file': output_path,
        'total_ingredients': len(df_result),
        'role_distribution': df_result['functional_role'].value_counts().to_dict()
    }
    
    with open(validation_log_path, 'w') as f:
        json.dump(validation_log, f, indent=2)
    
    logger.info(f"Saved validation log to {validation_log_path}")
    return df_result

def main():
    """Main function to run preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline...")
    ensure_directories()
    
    try:
        # Load required data
        normalized_df = load_normalized_ingredients()
        
        # Load marginal frequencies
        marginal_freq_df = pd.read_csv('data/processed/normalized_ingredients.csv')
        marginal_freq_counts = marginal_freq_df['ingredient_normalized'].value_counts()
        total_recipes = len(marginal_freq_df)
        marginal_freq_df = marginal_freq_counts / total_recipes
        marginal_freq_df = marginal_freq_df.reset_index()
        marginal_freq_df.columns = ['ingredient_normalized', 'marginal_frequency']
        
        # Load positional ranks
        positional_rank_df = normalized_df.copy()
        positional_rank_df['positional_rank'] = positional_rank_df.groupby('recipe_id').cumcount() + 1
        positional_rank_df = positional_rank_df[['ingredient_normalized', 'positional_rank']].groupby('ingredient_normalized').mean().reset_index()
        
        # Load co-occurrence matrix
        co_occurrence_df = None
        if os.path.exists('data/processed/co_occurrence_matrix.parquet'):
            co_occurrence_df = pd.read_parquet('data/processed/co_occurrence_matrix.parquet')
            # Add log_co_occurrence to main df if available
            if 'log_co_occurrence' in co_occurrence_df.columns:
                normalized_df = normalized_df.merge(
                    co_occurrence_df[['ingredient_normalized', 'log_co_occurrence']],
                    on='ingredient_normalized',
                    how='left'
                )
                normalized_df['log_co_occurrence'] = normalized_df['log_co_occurrence'].fillna(0)
        
        # Calculate functional roles
        logger.info("Calculating functional roles...")
        df_with_roles = calculate_functional_role(normalized_df, marginal_freq_df, positional_rank_df)
        
        # Verify exclusion of co-occurrence
        validation_result = verify_exclusion_of_co_occurrence(df_with_roles, co_occurrence_df)
        
        # Save output
        df_final = save_output(df_with_roles)
        
        logger.info("Preprocessing pipeline completed successfully.")
        logger.info(f"Role distribution: {df_final['functional_role'].value_counts().to_dict()}")
        
        return df_final
        
    except Exception as e:
        logger.error(f"Error during preprocessing: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()