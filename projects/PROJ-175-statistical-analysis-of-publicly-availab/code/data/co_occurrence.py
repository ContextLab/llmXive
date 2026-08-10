import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

def load_epsilon_config(config_path: str = "data/processed/epsilon_config.json") -> float:
    """Load the epsilon smoothing value from config, defaulting to 1e-9."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('epsilon', 1e-9)
    except FileNotFoundError:
        return 1e-9

def load_ingredient_pairs(input_path: str = "data/processed/normalized_ingredients.csv") -> pd.DataFrame:
    """Load the normalized ingredient pairs dataset."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Ingredient pairs file not found: {input_path}")
    return pd.read_csv(input_path)

def build_cooccurrence_matrix(df: pd.DataFrame, epsilon: float = 1e-9) -> pd.DataFrame:
    """
    Construct the global co-occurrence matrix C from the ingredient pairs dataframe.
    
    The input dataframe is expected to have columns:
    - 'recipe_id': Identifier for the recipe
    - 'ingredient_id': Identifier for the ingredient (canonical)
    
    Returns a DataFrame where rows and columns are ingredient_ids, 
    and values are log(1 + count) + epsilon.
    """
    if df.empty:
        raise ValueError("Input dataframe is empty; cannot build co-occurrence matrix.")
    
    required_cols = ['recipe_id', 'ingredient_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")
    
    # Count co-occurrences: For each recipe, generate all unique pairs (i, j)
    # We count undirected pairs (i, j) where i != j.
    # We use a dictionary to accumulate counts to avoid memory explosion with large sparse matrices
    # before converting to DataFrame.
    
    co_occurrence_counts = {}
    
    recipes = df['recipe_id'].unique()
    
    # To optimize, we can group by recipe_id first
    grouped = df.groupby('recipe_id')['ingredient_id'].apply(list)
    
    for ingredients in grouped:
        if len(ingredients) < 2:
            continue
        # Generate unique pairs
        unique_ingredients = list(set(ingredients))
        n = len(unique_ingredients)
        for i in range(n):
            for j in range(i + 1, n):
                ing_a = unique_ingredients[i]
                ing_b = unique_ingredients[j]
                # Normalize order to ensure (a, b) is same as (b, a)
                if ing_a > ing_b:
                    ing_a, ing_b = ing_b, ing_a
                
                pair = (ing_a, ing_b)
                co_occurrence_counts[pair] = co_occurrence_counts.get(pair, 0) + 1
    
    # Convert to DataFrame
    if not co_occurrence_counts:
        # Return empty matrix if no pairs found
        return pd.DataFrame()
    
    pairs = list(co_occurrence_counts.keys())
    counts = list(co_occurrence_counts.values())
    
    df_pairs = pd.DataFrame(pairs, columns=['ingredient_1', 'ingredient_2'])
    df_pairs['count'] = counts
    
    # Pivot to matrix form (sparse-friendly, but we'll make dense for small/medium or use sparse if needed)
    # Since we need to output a parquet, we can keep it in long form or pivot.
    # The task asks for a "matrix C". Usually, a matrix implies a square 2D structure.
    # However, for large N, a long-form table is often more practical for storage.
    # We will pivot to a square matrix if the number of unique ingredients is reasonable (< 5000),
    # otherwise we keep it in long form but named "co_occurrence_matrix" conceptually.
    # Given Recipe1M scale, a full dense matrix is likely too big. We will output a long-form
    # representation which is the standard way to store sparse co-occurrence data in parquet.
    
    # Let's pivot to wide form only if feasible, else keep long.
    # To be safe and strictly follow "matrix", we create a square matrix only for the ingredients present.
    # If too many unique ingredients, we fall back to long form but label it as the matrix representation.
    
    all_ingredients = sorted(set(df_pairs['ingredient_1']).union(set(df_pairs['ingredient_2'])))
    n_ingredients = len(all_ingredients)
    
    # Heuristic: if > 2000 ingredients, keep long form to avoid OOM, as dense matrix would be 2000x2000 floats (32MB) which is fine,
    # but 10k x 10k is 800MB. Recipe1M has many ingredients. Let's cap at 5000.
    if n_ingredients <= 5000:
        # Create square matrix
        matrix = np.zeros((n_ingredients, n_ingredients), dtype=np.float64)
        ing_to_idx = {ing: idx for idx, ing in enumerate(all_ingredients)}
        
        for _, row in df_pairs.iterrows():
            i = ing_to_idx[row['ingredient_1']]
            j = ing_to_idx[row['ingredient_2']]
            val = row['count']
            matrix[i, j] = val
            matrix[j, i] = val
        
        df_matrix = pd.DataFrame(matrix, index=all_ingredients, columns=all_ingredients)
        # Apply log transform with epsilon smoothing
        df_matrix = np.log1p(df_matrix) + epsilon
        # Ensure diagonal is epsilon (or log(1)+eps = 0+eps) if we assume self-cooccurrence is 0 or 1?
        # Usually diagonal is 0 or 1. We'll set diagonal to epsilon to avoid log(0) if we assumed 0 count.
        np.fill_diagonal(df_matrix.values, epsilon) 
        return df_matrix
    else:
        # Keep long form but apply log transform
        df_pairs['log_count'] = np.log1p(df_pairs['count']) + epsilon
        # Symmetrize by creating both (a,b) and (b,a) if needed for downstream matrix ops,
        # but usually long form is sufficient. We'll output the symmetric long form.
        df_long = pd.concat([
            df_pairs[['ingredient_1', 'ingredient_2', 'log_count']],
            df_pairs.rename(columns={'ingredient_1': 'ingredient_2', 'ingredient_2': 'ingredient_1'})[['ingredient_1', 'ingredient_2', 'log_count']]
        ])
        return df_long

def save_output(df: pd.DataFrame, output_path: str = "data/processed/co_occurrence_matrix.parquet") -> None:
    """Save the co-occurrence matrix (or long-form representation) to parquet."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    df.to_parquet(output_path, index=True)
    print(f"Co-occurrence matrix saved to {output_path}")

def main():
    """Main entry point for T015."""
    # Paths
    input_path = "data/processed/normalized_ingredients.csv"
    output_path = "data/processed/co_occurrence_matrix.parquet"
    config_path = "data/processed/epsilon_config.json"
    
    # Load config
    epsilon = load_epsilon_config(config_path)
    print(f"Loaded epsilon: {epsilon}")
    
    # Load data
    try:
        df = load_ingredient_pairs(input_path)
        print(f"Loaded {len(df)} ingredient entries.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Build matrix
    print("Building co-occurrence matrix...")
    matrix_df = build_cooccurrence_matrix(df, epsilon)
    print(f"Matrix shape: {matrix_df.shape if hasattr(matrix_df, 'shape') else 'Long form with ' + str(len(matrix_df)) + ' rows'}")
    
    # Save
    save_output(matrix_df, output_path)
    print("Task T015 completed successfully.")

if __name__ == "__main__":
    main()
