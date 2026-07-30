import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure the project root is in the path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def load_epsilon_config():
    """
    Loads the epsilon value from the configuration file generated in T049.
    Falls back to 1e-6 if not found, but logs a warning.
    """
    config_path = Path("data/epsilon_config.json")
    default_epsilon = 1e-6
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('epsilon', default_epsilon)
        except (json.JSONDecodeError, KeyError):
            print(f"Warning: Could not parse epsilon from {config_path}, using default.")
            return default_epsilon
    else:
        print(f"Warning: {config_path} not found, using default epsilon.")
        return default_epsilon

def load_ingredient_pairs(input_path):
    """
    Loads the pairwise co-occurrence counts from the parquet file generated in T013c.
    Expected columns: ingredient_id_1, ingredient_id_2, count
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_parquet(path)
    required_cols = {'ingredient_id_1', 'ingredient_id_2', 'count'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Input file missing required columns: {missing}")
    
    return df

def build_cooccurrence_matrix(df, epsilon):
    """
    Builds the global co-occurrence matrix C from the pairwise counts.
    Applies a log-transform: log(count + epsilon).
    
    Returns:
        pd.DataFrame: The log-transformed co-occurrence matrix.
        dict: Statistics about the matrix (dimensions, sparsity, etc.)
    """
    # Pivot the dataframe to create the matrix
    # We assume the data is symmetric or we treat (A,B) and (B,A) as the same edge.
    # For the matrix, we want a square matrix where index/cols are unique ingredients.
    
    # Ensure unique ingredients list
    ingredients = sorted(set(df['ingredient_id_1']).union(set(df['ingredient_id_2'])))
    n = len(ingredients)
    
    # Create a mapping from ingredient to index
    idx_map = {ing: i for i, ing in enumerate(ingredients)}
    
    # Initialize matrix with zeros
    matrix = np.zeros((n, n), dtype=np.float32)
    
    # Fill the matrix
    # We iterate through the dataframe rows. If the data is not symmetric, 
    # we might need to aggregate or just fill both (i,j) and (j,i).
    # Assuming the input T013c output contains unique pairs (i,j) with i <= j or similar.
    # To be safe, we fill both symmetric positions if we want a symmetric matrix,
    # or just fill the specific entries provided.
    # Standard co-occurrence matrices in this context are usually symmetric.
    
    for _, row in df.iterrows():
        i = idx_map[row['ingredient_id_1']]
        j = idx_map[row['ingredient_id_2']]
        val = row['count']
        
        # Apply log transform
        log_val = np.log(val + epsilon)
        
        matrix[i, j] = log_val
        matrix[j, i] = log_val # Ensure symmetry if input is directed or partial

    # Convert to DataFrame for easier handling and saving
    matrix_df = pd.DataFrame(matrix, index=ingredients, columns=ingredients)
    
    # Calculate statistics
    total_cells = n * n
    non_zero = np.count_nonzero(matrix)
    sparsity = 1.0 - (non_zero / total_cells)
    
    stats = {
        "dimensions": [n, n],
        "total_cells": int(total_cells),
        "non_zero_entries": int(non_zero),
        "sparsity": float(sparsity),
        "min_value": float(np.min(matrix)),
        "max_value": float(np.max(matrix)),
        "mean_value": float(np.mean(matrix[matrix > 0])) if non_zero > 0 else 0.0,
        "epsilon_used": float(epsilon),
        "ingredient_count": n
    }
    
    return matrix_df, stats

def save_output(matrix_df, stats, output_matrix_path, output_stats_path):
    """
    Saves the matrix to parquet and the stats to JSON.
    """
    # Ensure output directories exist
    Path(output_matrix_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_stats_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save matrix
    matrix_df.to_parquet(output_matrix_path, index=True)
    
    # Save stats
    with open(output_stats_path, 'w') as f:
        json.dump(stats, f, indent=2)

def main():
    """
    Main entry point for T015: Co-occurrence Matrix generation.
    """
    print("Starting T015: Co-occurrence Matrix Generation")
    
    # Paths
    input_path = "data/raw/co_occurrence_counts.parquet"
    output_matrix_path = "data/processed/co_occurrence_matrix.parquet"
    output_stats_path = "data/matrix_stats.json"
    
    # Load Config
    epsilon = load_epsilon_config()
    print(f"Using epsilon: {epsilon}")
    
    # Load Data
    try:
        df = load_ingredient_pairs(input_path)
        print(f"Loaded {len(df)} pairwise co-occurrence records.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Build Matrix
    print("Building co-occurrence matrix...")
    matrix_df, stats = build_cooccurrence_matrix(df, epsilon)
    
    # Save Output
    save_output(matrix_df, stats, output_matrix_path, output_stats_path)
    
    print(f"Matrix saved to {output_matrix_path}")
    print(f"Stats saved to {output_stats_path}")
    print(f"Matrix Stats: {stats['dimensions']} with sparsity {stats['sparsity']:.4f}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())