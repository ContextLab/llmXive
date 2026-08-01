"""
Preprocessing pipeline for recipe data normalization and co-occurrence computation.
Implements T014: Normalization using Levenshtein distance against Recipe1M ingredient list.
"""

import os
import sys
import json
import re
import gc
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set

import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/preprocessing.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directories ensured: {RAW_DIR}, {PROCESSED_DIR}")

def log_event(event_type: str, details: Dict):
    """Log an event to the preprocessing log."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "details": details
    }
    logger.info(json.dumps(log_entry))

def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute the Levenshtein distance between two strings."""
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

def normalize_ingredient_name(name: str, reference_list: List[str], max_distance: int = 2) -> Tuple[str, bool]:
    """
    Normalize an ingredient name against a reference list using Levenshtein distance.
    
    Args:
        name: The ingredient name to normalize
        reference_list: List of reference ingredient names from Recipe1M
        max_distance: Maximum allowed Levenshtein distance (default 2)
    
    Returns:
        Tuple of (normalized_name, was_normalized)
    """
    name_clean = name.lower().strip()
    name_clean = re.sub(r'[^a-z0-9\s]', '', name_clean)
    
    if name_clean in reference_list:
        return name_clean, False
    
    best_match = None
    best_distance = float('inf')
    
    for ref in reference_list:
        ref_clean = ref.lower().strip()
        ref_clean = re.sub(r'[^a-z0-9\s]', '', ref_clean)
        
        dist = levenshtein_distance(name_clean, ref_clean)
        
        if dist < best_distance:
            best_distance = dist
            best_match = ref
        
        if best_distance <= max_distance:
            break
    
    if best_distance <= max_distance:
        return best_match, True
    else:
        return name, False

def load_normalized_ingredients(input_path: str) -> pd.DataFrame:
    """Load normalized ingredients from parquet file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading normalized ingredients from {input_path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def compute_pairwise_cooccurrence(ingredients_df: pd.DataFrame, output_path: str):
    """
    Compute pairwise co-occurrence matrix from normalized ingredients.
    
    Args:
        ingredients_df: DataFrame with recipe-ingredient pairs
        output_path: Path to save the co-occurrence matrix
    """
    logger.info("Computing pairwise co-occurrence matrix...")
    
    # Group by recipe_id and count ingredient pairs
    recipe_ingredients = ingredients_df.groupby('recipe_id')['ingredient_name'].apply(list)
    
    co_occurrence_counts = {}
    total_pairs = 0
    
    for ingredients in recipe_ingredients:
        unique_ingredients = list(set(ingredients))
        for i in range(len(unique_ingredients)):
            for j in range(i + 1, len(unique_ingredients)):
                pair = tuple(sorted([unique_ingredients[i], unique_ingredients[j]]))
                co_occurrence_counts[pair] = co_occurrence_counts.get(pair, 0) + 1
                total_pairs += 1
    
    # Convert to DataFrame
    co_occurrence_data = [
        {
            'ingredient_1': pair[0],
            'ingredient_2': pair[1],
            'co_occurrence_count': count
        }
        for pair, count in co_occurrence_counts.items()
    ]
    
    co_occurrence_df = pd.DataFrame(co_occurrence_data)
    logger.info(f"Computed {len(co_occurrence_df)} unique ingredient pairs")
    
    # Save to parquet
    co_occurrence_df.to_parquet(output_path, index=False)
    logger.info(f"Saved co-occurrence matrix to {output_path}")
    
    # Log statistics
    stats = {
        'total_pairs': total_pairs,
        'unique_pairs': len(co_occurrence_df),
        'timestamp': datetime.utcnow().isoformat()
    }
    log_event('co_occurrence_computed', stats)

def load_reference_ingredients() -> List[str]:
    """Load reference ingredient list from Recipe1M dataset."""
    # Try to load from pilot data or full data
    pilot_path = RAW_DIR / "pilot_data.parquet"
    full_path = RAW_DIR / "recipe1m_full.parquet"
    
    reference_list = []
    
    if pilot_path.exists():
        logger.info("Loading reference ingredients from pilot data...")
        df = pd.read_parquet(pilot_path)
        if 'ingredient' in df.columns:
            reference_list = df['ingredient'].unique().tolist()
        elif 'ingredients' in df.columns:
            # Handle list of ingredients
            all_ingredients = []
            for ingredients in df['ingredients']:
                if isinstance(ingredients, list):
                    all_ingredients.extend(ingredients)
            reference_list = list(set(all_ingredients))
    elif full_path.exists():
        logger.info("Loading reference ingredients from full data...")
        df = pd.read_parquet(full_path)
        if 'ingredient' in df.columns:
            reference_list = df['ingredient'].unique().tolist()
        elif 'ingredients' in df.columns:
            all_ingredients = []
            for ingredients in df['ingredients']:
                if isinstance(ingredients, list):
                    all_ingredients.extend(ingredients)
            reference_list = list(set(all_ingredients))
    else:
        raise FileNotFoundError("No Recipe1M data found. Run download.py first.")
    
    logger.info(f"Loaded {len(reference_list)} reference ingredients")
    return reference_list

def save_output(df: pd.DataFrame, output_path: str):
    """Save DataFrame to parquet file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved output to {output_path}")

def main():
    """Main preprocessing pipeline for T014 normalization."""
    logger.info("Starting T014 preprocessing pipeline...")
    start_time = time.time()
    
    ensure_directories()
    
    # Load reference ingredients
    try:
        reference_list = load_reference_ingredients()
    except FileNotFoundError as e:
        logger.error(f"Failed to load reference ingredients: {e}")
        sys.exit(1)
    
    # Load raw ingredient data (from T013a_full or T013b)
    input_path = RAW_DIR / "recipe1m_full.parquet"
    if not input_path.exists():
        input_path = RAW_DIR / "pilot_data.parquet"
    
    if not input_path.exists():
        logger.error("No input data found. Run download.py first.")
        sys.exit(1)
    
    logger.info(f"Loading input data from {input_path}")
    raw_df = pd.read_parquet(input_path)
    
    # Determine column name for ingredients
    ingredient_col = None
    for col in ['ingredient', 'ingredients', 'ingredient_name', 'ingredient_list']:
        if col in raw_df.columns:
            ingredient_col = col
            break
    
    if ingredient_col is None:
        logger.error("Could not find ingredient column in input data")
        sys.exit(1)
    
    logger.info(f"Using column '{ingredient_col}' for ingredients")
    
    # Extract and normalize ingredients
    normalized_ingredients = []
    excluded_count = 0
    normalized_count = 0
    
    # Process in chunks to manage memory
    chunk_size = 10000
    for start_idx in range(0, len(raw_df), chunk_size):
        end_idx = min(start_idx + chunk_size, len(raw_df))
        chunk = raw_df.iloc[start_idx:end_idx]
        
        for _, row in chunk.iterrows():
            recipe_id = row['recipe_id'] if 'recipe_id' in row else start_idx
            
            ingredients = row[ingredient_col]
            if isinstance(ingredients, str):
                ingredients = [ingredients]
            elif not isinstance(ingredients, list):
                ingredients = []
            
            for ingredient in ingredients:
                if not isinstance(ingredient, str):
                    continue
                
                normalized_name, was_normalized = normalize_ingredient_name(
                    ingredient, reference_list, max_distance=2
                )
                
                if was_normalized:
                    normalized_count += 1
                else:
                    # Check if it's a valid ingredient (not excluded)
                    if normalized_name.lower().strip() not in ['', 'nan', 'none']:
                        normalized_count += 1
                    else:
                        excluded_count += 1
                
                normalized_ingredients.append({
                    'recipe_id': recipe_id,
                    'original_name': ingredient,
                    'normalized_name': normalized_name,
                    'was_normalized': was_normalized
                })
        
        # Free memory
        if (end_idx // chunk_size) % 5 == 0:
            gc.collect()
    
    # Create DataFrame
    normalized_df = pd.DataFrame(normalized_ingredients)
    
    # Save normalized ingredients
    output_path = PROCESSED_DIR / "normalized_ingredients.parquet"
    save_output(normalized_df, str(output_path))
    
    # Create unique ingredients list
    unique_ingredients = normalized_df['normalized_name'].unique()
    unique_df = pd.DataFrame({'ingredient_name': unique_ingredients})
    unique_output_path = PROCESSED_DIR / "unique_ingredients.parquet"
    save_output(unique_df, str(unique_output_path))
    
    # Compute co-occurrence matrix
    co_occurrence_path = PROCESSED_DIR / "co_occurrence_matrix.parquet"
    compute_pairwise_cooccurrence(normalized_df, str(co_occurrence_path))
    
    # Generate normalization report
    report = {
        "normalized_count": normalized_count,
        "excluded_count": excluded_count,
        "total_ingredients_processed": len(normalized_ingredients),
        "unique_ingredients": len(unique_ingredients),
        "reference_list_size": len(reference_list),
        "max_levenshtein_distance": 2,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "SUCCESS" if normalized_count > 0 else "NO_DATA",
        "deviation_note": "Uses Recipe1M ingredient list instead of FlavorDB per Plan Critical Reframe"
    }
    
    report_path = DATA_DIR / "normalization_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    log_event('normalization_complete', report)
    
    elapsed_time = time.time() - start_time
    logger.info(f"T014 preprocessing completed in {elapsed_time:.2f} seconds")
    logger.info(f"Normalized {normalized_count} ingredients, excluded {excluded_count}")
    logger.info(f"Output files: {output_path}, {unique_output_path}, {co_occurrence_path}")

if __name__ == "__main__":
    main()
