import os
import sys
import json
import re
import gc
import time
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict
from typing import List, Dict, Tuple, Set
import itertools

# Import shared utilities if they exist in the project structure
try:
    from utils.memory_monitor import check_memory_limit
except ImportError:
    # Fallback if utils is not in path during direct execution
    pass

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

def log_event(message: str, level: str = "INFO"):
    """Log a message to stdout and optionally to a log file."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def ensure_directories():
    """Ensure required output directories exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_normalized_ingredients(input_path: str) -> pd.DataFrame:
    """
    Load the normalized ingredients dataset from T014.
    Expected columns: 'recipe_id', 'ingredient_id', 'normalized_name', 'position'
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    log_event(f"Loading normalized ingredients from {input_path}...")
    # Try parquet first, fallback to csv if necessary
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
    else:
        # Try to infer based on content
        try:
            df = pd.read_parquet(path)
        except Exception:
            df = pd.read_csv(path)
    
    log_event(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    
    # Validate required columns
    required_cols = ['recipe_id', 'ingredient_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}. Found: {list(df.columns)}")
    
    return df

def compute_pairwise_cooccurrence(df: pd.DataFrame, min_support: int = 2) -> pd.DataFrame:
    """
    Compute pairwise co-occurrence counts from normalized ingredient data.
    
    Logic:
    1. Group by recipe_id.
    2. For each recipe, generate all unique pairs of ingredients (combinations).
    3. Aggregate counts across all recipes.
    4. Filter by minimum support (optional).
    
    Args:
        df: DataFrame with 'recipe_id' and 'ingredient_id'.
        min_support: Minimum number of recipes an ingredient pair must appear in.
        
    Returns:
        DataFrame with columns: 'ingredient_id_1', 'ingredient_id_2', 'co_occurrence_count'.
    """
    log_event("Computing pairwise co-occurrence counts...")
    
    # Ensure deterministic ordering of ingredients within a recipe to avoid (A,B) and (B,A) duplicates
    # We sort ingredient_ids alphabetically/numerically within each recipe
    df_sorted = df.sort_values(['recipe_id', 'ingredient_id'])
    
    # Group by recipe and generate pairs
    pair_counts = defaultdict(int)
    
    # Process in chunks to manage memory if dataset is large
    # But for co-occurrence, we often need to iterate recipes.
    # If memory is tight, we can iterate groups one by one.
    
    log_event("Iterating recipes to generate pairs...")
    start_time = time.time()
    
    # Check memory before processing
    try:
        check_memory_limit(7168) # 7GB limit
    except NameError:
        pass # Skip if function not available
    
    recipe_groups = df_sorted.groupby('recipe_id')
    total_recipes = len(recipe_groups)
    
    processed_recipes = 0
    for recipe_id, group in recipe_groups:
        # Get unique ingredients for this recipe
        ingredients = group['ingredient_id'].unique()
        
        if len(ingredients) < 2:
            continue
        
        # Generate all unique pairs (combinations)
        # Sort to ensure (A, B) is same as (B, A) and we count once
        sorted_ingredients = sorted(ingredients)
        
        for pair in itertools.combinations(sorted_ingredients, 2):
            pair_key = (pair[0], pair[1])
            pair_counts[pair_key] += 1
        
        processed_recipes += 1
        if processed_recipes % 10000 == 0:
            elapsed = time.time() - start_time
            log_event(f"Processed {processed_recipes}/{total_recipes} recipes...")
            # Check memory periodically
            try:
                check_memory_limit(7168)
            except NameError:
                pass

    log_event(f"Finished iterating {processed_recipes} recipes in {time.time() - start_time:.2f}s")
    
    # Convert to DataFrame
    result_data = [
        {'ingredient_id_1': k[0], 'ingredient_id_2': k[1], 'co_occurrence_count': v}
        for k, v in pair_counts.items()
    ]
    
    result_df = pd.DataFrame(result_data)
    
    if result_df.empty:
        log_event("WARNING: No co-occurrence pairs found!", "WARNING")
        # Create empty dataframe with correct schema
        result_df = pd.DataFrame(columns=['ingredient_id_1', 'ingredient_id_2', 'co_occurrence_count'])
        result_df = result_df.astype({'ingredient_id_1': 'str', 'ingredient_id_2': 'str', 'co_occurrence_count': 'int64'})
    else:
        # Filter by min_support
        if min_support > 0:
            initial_count = len(result_df)
            result_df = result_df[result_df['co_occurrence_count'] >= min_support]
            log_event(f"Filtered pairs by min_support={min_support}: {initial_count} -> {len(result_df)}")
        
        # Sort for consistency
        result_df = result_df.sort_values(['ingredient_id_1', 'ingredient_id_2']).reset_index(drop=True)
    
    return result_df

def save_output(df: pd.DataFrame, output_path: str):
    """Save the co-occurrence dataframe to parquet."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    log_event(f"Saving co-occurrence counts to {output_path}...")
    df.to_parquet(output_path, index=False)
    log_event(f"Saved {len(df)} rows to {output_path}")

def main():
    """
    Main entry point for T013c: Compute Pairwise Co-occurrence.
    
    Usage:
        python code/data/preprocess.py --input data/processed/normalized_ingredients.parquet --output data/raw/co_occurrence_counts.parquet
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute pairwise co-occurrence counts.")
    parser.add_argument("--input", type=str, default=str(PROCESSED_DIR / "normalized_ingredients.parquet"),
                        help="Path to input normalized ingredients file.")
    parser.add_argument("--output", type=str, default=str(RAW_DIR / "co_occurrence_counts.parquet"),
                        help="Path to output co-occurrence counts file.")
    parser.add_argument("--min-support", type=int, default=2,
                        help="Minimum number of recipes for a pair to be included.")
    
    args = parser.parse_args()
    
    try:
        ensure_directories()
        
        # Load data
        df = load_normalized_ingredients(args.input)
        
        # Compute co-occurrence
        co_occurrence_df = compute_pairwise_cooccurrence(df, min_support=args.min_support)
        
        # Save output
        save_output(co_occurrence_df, args.output)
        
        log_event("T013c completed successfully.")
        return 0
        
    except Exception as e:
        log_event(f"ERROR: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())