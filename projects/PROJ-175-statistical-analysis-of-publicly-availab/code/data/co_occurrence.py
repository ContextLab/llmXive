import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_epsilon_config(config_path: str = "data/processed/epsilon_config.json") -> float:
    """Load epsilon smoothing value from config file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return float(config.get('epsilon', 1e-6))
    except FileNotFoundError:
        logger.warning(f"Epsilon config not found at {config_path}, using default 1e-6")
        return 1e-6
    except Exception as e:
        logger.error(f"Error loading epsilon config: {e}")
        return 1e-6

def load_ingredient_pairs(input_path: str = "data/processed/normalized_ingredients.csv") -> pd.DataFrame:
    """Load the normalized ingredients dataframe."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. Run T014 first.")
    
    df = pd.read_csv(input_path)
    required_cols = ['ingredient_id', 'canonical_name', 'functional_role', 'frequency']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} ingredients from {input_path}")
    return df

def build_cooccurrence_matrix(
    recipes_path: str = "data/raw/recipe1m_processed.parquet",
    ingredient_col: str = "ingredients",
    recipe_col: str = "recipe_id"
) -> pd.DataFrame:
    """
    Build the global co-occurrence matrix C from recipe data.
    
    Counts pairs (i, j) in recipes.
    Applies log-transform with epsilon smoothing for zero counts.
    """
    if not os.path.exists(recipes_path):
        raise FileNotFoundError(f"Recipe data not found at {recipes_path}. Run T013a first.")
    
    logger.info(f"Loading recipe data from {recipes_path}...")
    recipes_df = pd.read_parquet(recipes_path)
    
    if ingredient_col not in recipes_df.columns:
        # Try to find a column that might contain ingredients
        possible_cols = [c for c in recipes_df.columns if 'ingredient' in c.lower()]
        if possible_cols:
            ingredient_col = possible_cols[0]
            logger.info(f"Using '{ingredient_col}' as ingredient column")
        else:
            raise ValueError(f"Could not find ingredient column in {recipes_df.columns}")
    
    # Flatten recipes to get ingredient pairs
    # Each recipe contains a list of ingredients; we count pairs within each recipe
    pair_counts = {}
    total_recipes = 0
    
    logger.info("Counting co-occurrences...")
    
    # Process in chunks to avoid memory issues
    chunk_size = 10000
    for start_idx in range(0, len(recipes_df), chunk_size):
        chunk = recipes_df.iloc[start_idx:start_idx + chunk_size]
        
        for _, row in chunk.iterrows():
            ingredients = row[ingredient_col]
            if not isinstance(ingredients, list):
                continue
            
            # Deduplicate ingredients in this recipe
            unique_ingredients = list(set(ingredients))
            
            # Count pairs (i, j) where i <= j (symmetric matrix)
            for i in range(len(unique_ingredients)):
                ing_a = unique_ingredients[i]
                pair_counts[(ing_a, ing_a)] = pair_counts.get((ing_a, ing_a), 0) + 1
                
                for j in range(i + 1, len(unique_ingredients)):
                    ing_b = unique_ingredients[j]
                    pair = tuple(sorted([ing_a, ing_b]))
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1
            
            total_recipes += 1
            if total_recipes % 50000 == 0:
                logger.info(f"Processed {total_recipes} recipes...")
    
    logger.info(f"Processed {total_recipes} recipes total.")
    
    # Build DataFrame from pair counts
    pairs_data = []
    for (ing_a, ing_b), count in pair_counts.items():
        pairs_data.append({
            'ingredient_a': ing_a,
            'ingredient_b': ing_b,
            'co_occurrence_count': count
        })
    
    pairs_df = pd.DataFrame(pairs_data)
    
    # Apply log-transform with epsilon smoothing
    epsilon = 1e-6
    pairs_df['log_co_occurrence'] = np.log1p(pairs_df['co_occurrence_count'] + epsilon)
    
    # Pivot to create symmetric matrix
    # First, ensure both directions exist for non-diagonal pairs
    non_diag = pairs_df[pairs_df['ingredient_a'] != pairs_df['ingredient_b']].copy()
    swapped = non_diag.rename(columns={
        'ingredient_a': 'ingredient_b',
        'ingredient_b': 'ingredient_a',
        'co_occurrence_count': 'co_occurrence_count_swapped',
        'log_co_occurrence': 'log_co_occurrence_swapped'
    })
    
    # Use the original counts (they should be symmetric by construction)
    # Just ensure we have both directions for the pivot
    full_pairs = pd.concat([
        pairs_df[['ingredient_a', 'ingredient_b', 'log_co_occurrence']],
        swapped[['ingredient_b', 'ingredient_a', 'log_co_occurrence']].rename(
            columns={'ingredient_b': 'ingredient_a', 'ingredient_a': 'ingredient_b'}
        )
    ]).drop_duplicates()
    
    matrix = full_pairs.pivot_table(
        index='ingredient_a',
        columns='ingredient_b',
        values='log_co_occurrence',
        fill_value=0
    )
    
    logger.info(f"Co-occurrence matrix shape: {matrix.shape}")
    return matrix

def save_output(matrix: pd.DataFrame, output_path: str = "data/processed/co_occurrence_matrix.parquet") -> None:
    """Save the co-occurrence matrix to parquet."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert to DataFrame with explicit index/columns for parquet
    matrix_df = matrix.reset_index()
    matrix_df = matrix_df.rename(columns={'index': 'ingredient_a'})
    
    matrix_df.to_parquet(output_path, index=False)
    logger.info(f"Saved co-occurrence matrix to {output_path}")
    
    # Also save metadata
    metadata = {
        'shape': list(matrix.shape),
        'num_ingredients': len(matrix.columns),
        'non_zero_pairs': int((matrix > 0).sum().sum()),
        'timestamp': datetime.now().isoformat()
    }
    
    metadata_path = output_path.replace('.parquet', '_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")

def main():
    """Main entry point for T015."""
    logger.info("Starting T015: Co-occurrence Matrix Construction")
    
    try:
        # Load input data
        logger.info("Loading normalized ingredients...")
        ingredients_df = load_ingredient_pairs()
        
        # Build co-occurrence matrix
        logger.info("Building co-occurrence matrix...")
        matrix = build_cooccurrence_matrix(
            recipes_path="data/raw/recipe1m_processed.parquet"
        )
        
        # Save output
        logger.info("Saving co-occurrence matrix...")
        save_output(matrix)
        
        logger.info("T015 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during co-occurrence matrix construction: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
