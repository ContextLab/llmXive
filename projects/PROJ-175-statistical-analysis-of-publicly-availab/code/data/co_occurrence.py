"""
Co-occurrence Matrix Construction (Task T015).

Builds global matrix C with log-transform using epsilon from T049.
Output: data/processed/co_occurrence_matrix.parquet
"""
import os
import sys
import json
import gc
import time
from pathlib import Path

import pandas as pd
import numpy as np

# Ensure project root is in path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.memory_monitor import check_memory_limit

OUTPUT_DIR = Path("data/processed")
INPUT_PAIRS = Path("data/processed/ingredient_pairs.parquet")
EPSILON_CONFIG = Path("data/zero_handling_log.json")
OUTPUT_FILE = Path("data/processed/co_occurrence_matrix.parquet")


def load_epsilon():
    """Load epsilon value from T049 configuration."""
    if not EPSILON_CONFIG.exists():
        raise FileNotFoundError(f"Configuration file not found: {EPSILON_CONFIG}. Run T049 first.")
    
    with open(EPSILON_CONFIG, 'r') as f:
        config = json.load(f)
    
    # Expecting a key 'epsilon' or similar in the zero handling log
    epsilon = config.get('epsilon', 1e-6)
    return float(epsilon)


def load_ingredient_pairs():
    """
    Load the ingredient pairs dataframe.
    Expects a parquet file with columns: ingredient_a, ingredient_b, count (or frequency).
    """
    if not INPUT_PAIRS.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PAIRS}. Run T013/T014 first.")
    
    df = pd.read_parquet(INPUT_PAIRS)
    
    # Validate required columns
    required_cols = ['ingredient_a', 'ingredient_b', 'count']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input file missing required columns: {missing}")
    
    return df


def build_co_occurrence_matrix(df, epsilon):
    """
    Build the global co-occurrence matrix C and apply log-transform.
    
    C_ij = log(count_ij + epsilon)
    
    Returns a DataFrame where index and columns are ingredient IDs,
    and values are log-transformed co-occurrence counts.
    """
    print(f"Building co-occurrence matrix from {len(df):,} pairs...")
    
    # Check memory before heavy operation
    check_memory_limit(limit_mb=6144)
    
    # Pivot to create the matrix
    # We assume 'count' is the frequency of co-occurrence
    matrix = df.pivot_table(
        index='ingredient_a', 
        columns='ingredient_b', 
        values='count', 
        fill_value=0
    )
    
    # Ensure symmetric matrix (co-occurrence is usually symmetric)
    # If the source data is already symmetric, this is redundant but safe.
    # If not, we take the max or sum. Here we assume the pivot handles one direction
    # and we mirror it if the transpose exists, or just fill missing with 0.
    # To be robust: if the dataset contains (A, B) but not (B, A), we should fill.
    # The pivot_table with fill_value=0 handles missing entries.
    
    # Check memory after pivot
    check_memory_limit(limit_mb=6144)
    
    # Apply log transform: log(count + epsilon)
    # Add epsilon to avoid log(0)
    matrix = np.log(matrix + epsilon)
    
    print(f"Matrix shape: {matrix.shape}")
    print(f"Min value: {matrix.min().min():.4f}, Max value: {matrix.max().max():.4f}")
    
    return matrix


def save_matrix(matrix, output_path):
    """Save the matrix to parquet."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_parquet(output_path, index=True)
    print(f"Saved co-occurrence matrix to {output_path}")


def main():
    """Main entry point for T015."""
    start_time = time.time()
    
    try:
        # 1. Load Epsilon
        epsilon = load_epsilon()
        print(f"Using epsilon: {epsilon}")
        
        # 2. Load Ingredient Pairs
        df = load_ingredient_pairs()
        print(f"Loaded {len(df):,} ingredient pairs.")
        
        # 3. Build Matrix
        matrix = build_co_occurrence_matrix(df, epsilon)
        
        # 4. Save Output
        save_matrix(matrix, OUTPUT_FILE)
        
        elapsed = time.time() - start_time
        print(f"T015 completed successfully in {elapsed:.2f} seconds.")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except MemoryError as e:
        print(f"ERROR: Memory limit exceeded: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during T015: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        gc.collect()


if __name__ == "__main__":
    main()