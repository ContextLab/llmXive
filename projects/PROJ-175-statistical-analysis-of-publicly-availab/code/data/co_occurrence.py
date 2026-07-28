import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_epsilon_config(config_path: str) -> float:
    """Load epsilon value from T049 config."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return float(config.get('epsilon', 1e-10))
    except FileNotFoundError:
        logger.warning(f"Epsilon config not found at {config_path}. Using default 1e-10.")
        return 1e-10

def load_ingredient_pairs(input_path: str) -> pd.DataFrame:
    """
    Load the ingredient pair counts from T013 output.
    Expected schema: ingredient_id_1, ingredient_id_2, count (or similar).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Normalize column names if necessary (handle potential variations)
    cols = df.columns.str.lower()
    if 'count' not in cols and 'frequency' not in cols:
        # Assume the last column is the count if not named explicitly
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            count_col = numeric_cols[-1]
            df.rename(columns={count_col: 'count'}, inplace=True)
        else:
            raise ValueError("Could not identify count column in input parquet.")
    elif 'frequency' in cols and 'count' not in cols:
        df.rename(columns={'frequency': 'count'}, inplace=True)
        
    return df

def build_cooccurrence_matrix(df: pd.DataFrame, epsilon: float) -> tuple:
    """
    Build the global co-occurrence matrix C.
    C[i, j] = log(count[i, j] + epsilon)
    
    Returns:
      matrix_df: DataFrame with index and columns as ingredient IDs, values as log counts.
      stats: Dict of matrix statistics.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty. Cannot build matrix.")

    # Pivot to create matrix
    # Ensure we have the right columns
    if 'ingredient_id_1' not in df.columns or 'ingredient_id_2' not in df.columns or 'count' not in df.columns:
        # Try to infer or raise
        raise ValueError(f"Expected columns ['ingredient_id_1', 'ingredient_id_2', 'count']. Found: {df.columns.tolist()}")

    # Pivot
    matrix = df.pivot_table(
        index='ingredient_id_1',
        columns='ingredient_id_2',
        values='count',
        aggfunc='sum',
        fill_value=0
    )

    # Apply log transform with epsilon
    # Avoid log(0) by adding epsilon
    matrix_log = np.log(matrix + epsilon)

    # Calculate stats
    total_cells = matrix_log.size
    non_zero_cells = (matrix_log > 0).sum().sum()
    sparsity = 1.0 - (non_zero_cells / total_cells) if total_cells > 0 else 1.0
    mean_val = matrix_log.mean().mean()
    max_val = matrix_log.max().max()
    min_val = matrix_log.min().min()

    stats = {
        "dimensions": list(matrix_log.shape),
        "total_cells": int(total_cells),
        "non_zero_cells": int(non_zero_cells),
        "sparsity": float(sparsity),
        "mean_log_count": float(mean_val),
        "max_log_count": float(max_val),
        "min_log_count": float(min_val),
        "epsilon_used": float(epsilon)
    }

    # Convert to DataFrame for saving
    matrix_df = matrix_log.reset_index()
    matrix_df.columns = ['ingredient_id_1'] + [f'ingredient_id_{i}' for i in range(1, len(matrix_df.columns) + 1)]
    
    # Actually, standard parquet save for matrix usually keeps index as column or separate.
    # Let's keep it as a wide table where index is ingredient_id_1 and columns are ingredient_id_2
    matrix_df = matrix_log.reset_index()
    
    return matrix_df, stats

def save_output(matrix_df: pd.DataFrame, stats: dict, output_matrix_path: str, output_stats_path: str):
    """Save the matrix and stats to disk."""
    # Ensure output directories exist
    Path(output_matrix_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_stats_path).parent.mkdir(parents=True, exist_ok=True)

    # Save matrix
    matrix_df.to_parquet(output_matrix_path, index=False)
    logger.info(f"Saved co-occurrence matrix to {output_matrix_path}")

    # Save stats
    with open(output_stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Saved matrix stats to {output_stats_path}")

def main():
    """Main entry point for T015."""
    # Paths based on task description
    input_path = "data/raw/recipe1m_counts.parquet"
    epsilon_config_path = "data/zero_handling_log.json" # T049 output
    output_matrix_path = "data/processed/co_occurrence_matrix.parquet"
    output_stats_path = "data/matrix_stats.json"

    logger.info(f"Starting T015: Co-occurrence Matrix Construction")
    logger.info(f"Input: {input_path}")
    
    # 1. Load Epsilon
    epsilon = load_epsilon_config(epsilon_config_path)
    logger.info(f"Using epsilon: {epsilon}")

    # 2. Load Counts
    try:
        df = load_ingredient_pairs(input_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)

    # 3. Build Matrix
    try:
        matrix_df, stats = build_cooccurrence_matrix(df, epsilon)
    except ValueError as e:
        logger.error(f"Failed to build matrix: {e}")
        sys.exit(1)

    # 4. Save Output
    save_output(matrix_df, stats, output_matrix_path, output_stats_path)

    logger.info("T015 completed successfully.")
    print(json.dumps(stats))

if __name__ == "__main__":
    main()
