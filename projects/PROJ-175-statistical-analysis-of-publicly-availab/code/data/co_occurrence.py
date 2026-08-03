import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

def load_epsilon_config(config_path="specs/001-statistical-analysis-of-recipe-data/contracts/epsilon_config.json"):
    """Load the epsilon smoothing configuration."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default fallback if config is missing, though spec implies it should exist
        return {"epsilon": 1e-6}

def load_ingredient_pairs(input_path="data/processed/normalized_ingredients.csv"):
    """
    Load the normalized ingredients CSV.
    Expected columns: recipe_id, ingredient_id, functional_role, etc.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_csv(input_path)
    # Ensure recipe_id and ingredient_id are present
    required_cols = ['recipe_id', 'ingredient_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    return df

def build_cooccurrence_matrix(df):
    """
    Construct global co-occurrence matrix C.
    Counts pairs (i, j) in recipes.
    Applies log-transform with epsilon smoothing for zero counts.
    Returns a DataFrame where index and columns are ingredient_ids.
    """
    # Group by recipe_id to get sets of ingredients per recipe
    # We need to count how many times each pair appears together
    
    # Create a list of frozensets for each recipe's ingredients
    recipe_ingredient_sets = df.groupby('recipe_id')['ingredient_id'].apply(lambda x: frozenset(x.unique()))
    
    # Initialize a dictionary to count pairs
    pair_counts = {}
    
    # Iterate over recipes to count pairs
    # To handle memory efficiently, we can use a sparse approach or iterate carefully
    # Given the constraints, we iterate and update a dictionary of counts
    
    # We will use a symmetric matrix approach. 
    # Since we need a full matrix for downstream, we might need to use pandas crosstab if unique ingredients aren't too many.
    # However, standard crosstab counts co-occurrence of row/col. Here we want pair (i, j) in same recipe.
    
    # Approach: One-hot encode ingredients per recipe, then matrix multiply?
    # If ingredients are too many, this is memory heavy. 
    # Let's try the iterative pair counting first, optimized with numpy/pandas.
    
    # Get unique ingredients
    all_ingredients = df['ingredient_id'].unique()
    ingredient_to_idx = {ing: i for i, ing in enumerate(all_ingredients)}
    n_ingredients = len(all_ingredients)
    
    # Create a sparse matrix representation or a dense one if n is small enough
    # If n_ingredients > 5000, dense matrix (25M entries) might be heavy but manageable in 8GB if float32.
    # Let's assume n is manageable or we use a dictionary then convert.
    
    # Efficient counting:
    # For each recipe, get the list of ingredient indices.
    # Increment counts for all pairs (i, j) where i <= j.
    
    counts = np.zeros((n_ingredients, n_ingredients), dtype=np.float32)
    
    for ingredients in recipe_ingredient_sets:
        indices = [ingredient_to_idx[i] for i in ingredients]
        # Vectorized counting for this recipe
        # Create a temporary matrix for this recipe's co-occurrences
        # This loop might be slow in pure python for many recipes.
        # Alternative: Use pandas crosstab on exploded data? No, that counts occurrences, not pairs.
        
        # Optimized pair update:
        # If we have indices [a, b, c], we want to add 1 to (a,a), (a,b), (a,c), (b,b), (b,c), (c,c)
        # We can use np.add.at
        # Create a mask of pairs
        idx_arr = np.array(indices)
        # Upper triangle including diagonal
        for i in range(len(idx_arr)):
            for j in range(i, len(idx_arr)):
                counts[idx_arr[i], idx_arr[j]] += 1
                
    # Make symmetric
    counts = counts + counts.T - np.diag(np.diag(counts))
    
    # Convert to DataFrame
    co_occurrence_df = pd.DataFrame(counts, index=all_ingredients, columns=all_ingredients)
    
    # Apply log-transform with epsilon smoothing: log(C + epsilon)
    config = load_epsilon_config()
    epsilon = config.get("epsilon", 1e-6)
    
    # Avoid log(0) by adding epsilon before log
    # The task says "log-transform with epsilon smoothing for zero counts"
    # Usually means log(count + epsilon)
    log_co_occurrence = np.log(co_occurrence_df + epsilon)
    
    return log_co_occurrence

def save_output(df, output_path="data/processed/co_occurrence_matrix.parquet"):
    """Save the co-occurrence matrix to parquet."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=True)
    print(f"Co-occurrence matrix saved to {output_path}")
    return True

def main():
    """Main entry point for T015."""
    print("Starting Co-occurrence Matrix Construction (T015)...")
    
    input_path = "data/processed/normalized_ingredients.csv"
    output_path = "data/processed/co_occurrence_matrix.parquet"
    
    try:
        # Load data
        print(f"Loading normalized ingredients from {input_path}...")
        df = load_ingredient_pairs(input_path)
        
        # Build matrix
        print("Building co-occurrence matrix...")
        matrix_df = build_cooccurrence_matrix(df)
        
        # Save output
        print("Saving output...")
        save_output(matrix_df, output_path)
        
        print("T015 completed successfully.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
