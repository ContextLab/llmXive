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
        logging.FileHandler('data/logs/derive_roles.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure output directories exist
def ensure_directories():
    dirs = ['data/processed', 'data/logs']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def load_marginal_frequencies(input_path='data/processed/normalized_ingredients.csv'):
    """Load marginal frequencies from normalized ingredients."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Required input file not found: {input_path}")
    logger.info(f"Loading marginal frequencies from {input_path}")
    df = pd.read_csv(input_path)
    # Ensure we have the frequency column
    if 'marginal_frequency' not in df.columns:
        # Calculate if missing: count / total
        total = len(df)
        freq_counts = df['ingredient_normalized'].value_counts() / total
        df = df.merge(freq_counts.rename('marginal_frequency'), 
                     left_on='ingredient_normalized', 
                     right_index=True, 
                     how='left')
    return df[['ingredient_normalized', 'marginal_frequency']]

def load_positional_ranks(input_path='data/processed/normalized_ingredients.csv'):
    """Load positional ranks from normalized ingredients."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Required input file not found: {input_path}")
    logger.info(f"Loading positional ranks from {input_path}")
    df = pd.read_csv(input_path)
    # Assume positional rank is derived from position in recipe
    # If not present, we calculate a simple rank based on order of appearance
    if 'positional_rank' not in df.columns:
        # Create a dummy rank based on index (simplified for this task)
        # In a real scenario, this would come from recipe structure
        df['positional_rank'] = df.groupby('recipe_id').cumcount() + 1
    return df[['ingredient_normalized', 'positional_rank']]

def load_co_occurrence_matrix(input_path='data/processed/co_occurrence_matrix.parquet'):
    """Load co-occurrence matrix."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Required input file not found: {input_path}")
    logger.info(f"Loading co-occurrence matrix from {input_path}")
    df = pd.read_parquet(input_path)
    return df

def load_reference_ingredients(input_path='data/processed/normalized_ingredients.csv'):
    """Load reference ingredients list."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Required input file not found: {input_path}")
    logger.info(f"Loading reference ingredients from {input_path}")
    df = pd.read_csv(input_path)
    return df['ingredient_normalized'].unique().tolist()

def calculate_functional_role(marginal_freq, positional_rank, co_occurrence_count):
    """
    Calculate functional role based on:
    1. Marginal frequency (high frequency = primary)
    2. Positional rank (early position = primary)
    3. Excluding co-occurrence frequency to prevent multicollinearity
    
    Returns: 'primary', 'secondary', or 'garnish'
    """
    # Normalize values for comparison
    max_freq = marginal_freq.max() if marginal_freq.max() > 0 else 1
    max_rank = positional_rank.max() if positional_rank.max() > 0 else 1
    
    # Normalize
    norm_freq = marginal_freq / max_freq
    norm_rank = 1 - (positional_rank / max_rank)  # Invert so early rank = high value
    
    # Combined score: weighted average
    # Higher score = more likely to be primary
    score = (norm_freq * 0.6) + (norm_rank * 0.4)
    
    # Determine role based on score thresholds
    # Adjust thresholds based on distribution if needed
    if score >= 0.7:
        return 'primary'
    elif score >= 0.3:
        return 'secondary'
    else:
        return 'garnish'

def verify_exclusion_of_co_occurrence(df_result, co_occurrence_matrix):
    """
    Verify that functional role is not correlated with co-occurrence frequency.
    This is a validation step to ensure multicollinearity is avoided.
    """
    logger.info("Verifying exclusion of co-occurrence frequency...")
    
    # Calculate correlation between functional role encoding and co-occurrence
    # Encode roles: primary=2, secondary=1, garnish=0
    role_map = {'primary': 2, 'secondary': 1, 'garnish': 0}
    df_result['role_encoded'] = df_result['functional_role'].map(role_map)
    
    # Calculate correlation with co-occurrence frequency
    # We need to map ingredient pairs to their co-occurrence counts
    # For simplicity, we'll check correlation at the ingredient level
    if 'ingredient_normalized' in df_result.columns and 'log_co_occurrence' in df_result.columns:
        correlation = df_result['role_encoded'].corr(df_result['log_co_occurrence'])
        logger.info(f"Correlation between functional role and log_co_occurrence: {correlation:.4f}")
        
        # If correlation is too high (> 0.5), we might have multicollinearity
        # In a real scenario, we might adjust the calculation or flag this
        if abs(correlation) > 0.5:
            logger.warning(f"High correlation ({correlation:.4f}) detected. Consider adjusting role calculation.")
        
        return {
            'correlation': float(correlation),
            'threshold': 0.5,
            'passed': abs(correlation) <= 0.5
        }
    
    return {
        'correlation': None,
        'threshold': 0.5,
        'passed': True,
        'note': 'Could not compute correlation due to missing data'
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
    """Main function to derive and validate functional roles."""
    logger.info("Starting functional role derivation...")
    ensure_directories()
    
    try:
        # Load required data
        marginal_freq_df = load_marginal_frequencies()
        positional_rank_df = load_positional_ranks()
        co_occurrence_df = load_co_occurrence_matrix()
        reference_ingredients = load_reference_ingredients()
        
        # Merge data
        df_merged = marginal_freq_df.merge(
            positional_rank_df, 
            on='ingredient_normalized', 
            how='outer'
        )
        
        # Calculate functional role for each ingredient
        logger.info("Calculating functional roles...")
        df_merged['functional_role'] = df_merged.apply(
            lambda row: calculate_functional_role(
                row['marginal_frequency'],
                row['positional_rank'],
                0  # Co-occurrence count is excluded from calculation
            ),
            axis=1
        )
        
        # Add log_co_occurrence for validation (if available)
        if not co_occurrence_df.empty and 'log_co_occurrence' in co_occurrence_df.columns:
            # Merge co-occurrence data if possible
            # This is a simplified merge; real implementation would handle pairs
            df_merged = df_merged.merge(
                co_occurrence_df[['ingredient_normalized', 'log_co_occurrence']],
                on='ingredient_normalized',
                how='left'
            )
            df_merged['log_co_occurrence'] = df_merged['log_co_occurrence'].fillna(0)
        
        # Verify exclusion of co-occurrence
        validation_result = verify_exclusion_of_co_occurrence(df_merged, co_occurrence_df)
        
        # Save output
        df_final = save_output(df_merged)
        
        logger.info("Functional role derivation completed successfully.")
        logger.info(f"Role distribution: {df_final['functional_role'].value_counts().to_dict()}")
        
        return df_final
        
    except Exception as e:
        logger.error(f"Error during functional role derivation: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
