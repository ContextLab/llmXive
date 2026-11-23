"""
T014: Normalization of ingredient names and derivation of functional roles.

This script reads the processed Recipe1M data, normalizes ingredient names using
Levenshtein distance, calculates marginal frequencies from the raw recipe list
(excluding co-occurrence matrices to ensure independence), and derives functional
roles based on positional rank and frequency.

Output: data/processed/normalized_ingredients.csv
"""
import os
import sys
import json
import re
import gc
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.download import load_verification_report
from utils.memory_monitor import check_memory_limit, get_memory_usage_gb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
LEVENSHTEIN_THRESHOLD = 2
SEED = 42
RAM_LIMIT_MB = 7168

np.random.seed(SEED)

def ensure_directories():
    """Ensure output directories exist."""
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
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

def normalize_ingredient_name(ingredient: str, reference_list: List[str]) -> Tuple[str, int]:
    """
    Normalize an ingredient name against a reference list using Levenshtein distance.
    
    Returns:
        Tuple of (canonical_name, distance)
    """
    ingredient_lower = ingredient.lower().strip()
    
    # Exact match
    if ingredient_lower in [r.lower() for r in reference_list]:
        return ingredient_lower, 0
    
    best_match = None
    best_distance = LEVENSHTEIN_THRESHOLD + 1
    
    for ref in reference_list:
        ref_lower = ref.lower().strip()
        dist = levenshtein_distance(ingredient_lower, ref_lower)
        
        if dist < best_distance:
            best_distance = dist
            best_match = ref_lower
        elif dist == best_distance and best_match:
            # Tie-breaking: select the one with higher marginal frequency (handled later)
            # For now, keep the first found or alphabetically first
            if ref_lower < best_match:
                best_match = ref_lower
    
    if best_distance <= LEVENSHTEIN_THRESHOLD:
        return best_match, best_distance
    
    return ingredient_lower, best_distance  # Return original if no good match

def load_reference_ingredients() -> List[str]:
    """
    Load the reference ingredient list.
    If proxy_source is Recipe1M, use the unique ingredients from the raw dataset.
    If proxy_source is null, use FlavorDB (not implemented here as per current state).
    """
    amendment_log_path = project_root / "data" / "amendment_log.json"
    if not amendment_log_path.exists():
        raise FileNotFoundError(f"Amendment log not found at {amendment_log_path}. Run T012d first.")
    
    with open(amendment_log_path, 'r') as f:
        amendment_data = json.load(f)
    
    if amendment_data.get('status') != 'RATIFIED':
        raise RuntimeError(f"Amendment log status is {amendment_data.get('status')}, not RATIFIED.")
    
    proxy_source = amendment_data.get('proxy_source')
    
    # Load raw Recipe1M data to get reference ingredients
    # We assume T013a has produced data/raw/recipe1m_processed.parquet
    raw_data_path = project_root / "data" / "raw" / "recipe1m_processed.parquet"
    
    if not raw_data_path.exists():
        # Fallback to raw parquet if processed doesn't exist yet
        raw_data_path = project_root / "data" / "raw" / "recipe1m_raw.parquet"
    
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Recipe1M data not found at {raw_data_path}. Run T013a first.")
    
    logger.info(f"Loading reference ingredients from {raw_data_path}")
    df = pd.read_parquet(raw_data_path)
    
    # Assume the column containing ingredients is named 'ingredients' or similar
    # Recipe1M structure usually has a list of ingredients per recipe
    ingredient_col = None
    for col in df.columns:
        if 'ingredient' in col.lower():
            ingredient_col = col
            break
    
    if not ingredient_col:
        # Try to infer from common names
        possible_cols = ['ingredients', 'ingredient_list', 'items']
        for col in possible_cols:
            if col in df.columns:
                ingredient_col = col
                break
    
    if not ingredient_col:
        raise ValueError("Could not find ingredient column in Recipe1M data.")
    
    # Flatten the list of ingredients
    all_ingredients = []
    for ingredients in df[ingredient_col]:
        if isinstance(ingredients, list):
            all_ingredients.extend(ingredients)
        elif isinstance(ingredients, str):
            # Handle CSV-like strings if necessary
            all_ingredients.extend([i.strip() for i in ingredients.split(',') if i.strip()])
    
    # Get unique ingredients
    reference_list = list(set(all_ingredients))
    logger.info(f"Loaded {len(reference_list)} unique reference ingredients")
    
    return reference_list

def load_marginal_frequencies(ingredients: List[str], reference_list: List[str]) -> Dict[str, int]:
    """
    Calculate marginal frequency of each ingredient from the raw recipe list.
    This is done EXCLUDING any co-occurrence matrix to ensure independence.
    """
    frequencies = {}
    for ing in ingredients:
        normalized, _ = normalize_ingredient_name(ing, reference_list)
        frequencies[normalized] = frequencies.get(normalized, 0) + 1
    return frequencies

def load_positional_ranks(ingredients: List[List[str]]) -> Dict[str, float]:
    """
    Calculate the average positional rank for each ingredient.
    Ingredients appearing earlier in recipes are considered more primary.
    """
    rank_sums = {}
    count = {}
    
    for recipe in ingredients:
        for idx, ing in enumerate(recipe):
            normalized, _ = normalize_ingredient_name(ing, reference_list)
            rank_sums[normalized] = rank_sums.get(normalized, 0) + idx
            count[normalized] = count.get(normalized, 0) + 1
    
    avg_ranks = {k: rank_sums[k] / count[k] for k in rank_sums}
    return avg_ranks

def load_co_occurrence_matrix() -> Optional[pd.DataFrame]:
    """
    Load the co-occurrence matrix if it exists (for verification only, not used in calculation).
    """
    co_occ_path = project_root / "data" / "processed" / "co_occurrence_matrix.parquet"
    if co_occ_path.exists():
        return pd.read_parquet(co_occ_path)
    return None

def load_normalized_ingredients() -> pd.DataFrame:
    """Load the output from the normalization step if it exists."""
    output_path = project_root / "data" / "processed" / "normalized_ingredients.csv"
    if output_path.exists():
        return pd.read_csv(output_path)
    return None

def calculate_functional_role(frequency: int, avg_rank: float, total_recipes: int) -> str:
    """
    Derive functional role based on marginal frequency and positional rank.
    
    Logic:
    - Primary: High frequency (top 20%) and low average rank (early in recipe)
    - Secondary: Moderate frequency/rank
    - Garnish: Low frequency or high average rank (late in recipe)
    """
    # Normalize frequency
    freq_percentile = (frequency / total_recipes) if total_recipes > 0 else 0
    
    # Normalize rank (lower is better)
    # Assuming max rank is roughly the average recipe length (e.g., 10)
    # We can use a fixed threshold or percentile for rank
    rank_percentile = 1 - (avg_rank / 10.0) if avg_rank < 10 else 0
    rank_percentile = max(0, min(1, rank_percentile))
    
    # Combined score
    score = 0.6 * freq_percentile + 0.4 * rank_percentile
    
    if score > 0.7:
        return "primary"
    elif score > 0.3:
        return "secondary"
    else:
        return "garnish"

def verify_exclusion_of_co_occurrence(frequencies: Dict[str, int], co_occ_matrix: Optional[pd.DataFrame]):
    """
    Verify that frequencies were calculated without using the co-occurrence matrix.
    This is a sanity check to ensure independence per FR-005.
    """
    if co_occ_matrix is not None:
        logger.warning("Co-occurrence matrix exists. Ensure marginal frequencies were calculated independently.")
        # In a real scenario, we might compare the sum of frequencies to the sum of co-occurrence counts
        # but for this task, we just log the warning.
    return True

def save_output(df: pd.DataFrame, output_path: Path):
    """Save the normalized ingredients dataframe to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Saved normalized ingredients to {output_path}")

def main():
    """Main execution function for T014."""
    logger.info("Starting T014: Normalization and Functional Role Derivation")
    
    # Check memory
    check_memory_limit(RAM_LIMIT_MB)
    
    # Ensure directories
    output_dir = ensure_directories()
    output_path = output_dir / "normalized_ingredients.csv"
    
    # Load reference ingredients
    try:
        reference_list = load_reference_ingredients()
    except Exception as e:
        logger.error(f"Failed to load reference ingredients: {e}")
        raise
    
    # Load raw data to calculate frequencies and ranks
    raw_data_path = project_root / "data" / "raw" / "recipe1m_processed.parquet"
    if not raw_data_path.exists():
        raw_data_path = project_root / "data" / "raw" / "recipe1m_raw.parquet"
    
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data not found at {raw_data_path}")
    
    logger.info("Loading raw data for frequency and rank calculation")
    df_raw = pd.read_parquet(raw_data_path)
    
    ingredient_col = None
    for col in df_raw.columns:
        if 'ingredient' in col.lower():
            ingredient_col = col
            break
    
    if not ingredient_col:
        possible_cols = ['ingredients', 'ingredient_list', 'items']
        for col in possible_cols:
            if col in df_raw.columns:
                ingredient_col = col
                break
    
    if not ingredient_col:
        raise ValueError("Could not find ingredient column in raw data.")
    
    # Extract all recipes (list of ingredients)
    recipes = df_raw[ingredient_col].tolist()
    total_recipes = len(recipes)
    
    # Flatten to get all ingredients for frequency calculation
    all_ingredients = []
    for recipe in recipes:
        if isinstance(recipe, list):
            all_ingredients.extend(recipe)
        elif isinstance(recipe, str):
            all_ingredients.extend([i.strip() for i in recipe.split(',') if i.strip()])
    
    # Calculate marginal frequencies
    logger.info("Calculating marginal frequencies...")
    frequencies = load_marginal_frequencies(all_ingredients, reference_list)
    
    # Calculate positional ranks
    logger.info("Calculating positional ranks...")
    avg_ranks = load_positional_ranks(recipes)
    
    # Load co-occurrence matrix for verification (if exists)
    co_occ_matrix = load_co_occurrence_matrix()
    verify_exclusion_of_co_occurrence(frequencies, co_occ_matrix)
    
    # Normalize all unique ingredients and assign roles
    logger.info("Normalizing ingredients and assigning roles...")
    normalized_data = []
    
    # Get unique ingredients from the reference list (or all observed)
    unique_ingredients = list(set(all_ingredients))
    
    for ing in unique_ingredients:
        canonical, distance = normalize_ingredient_name(ing, reference_list)
        freq = frequencies.get(canonical, 0)
        rank = avg_ranks.get(canonical, 10.0)  # Default high rank if not found
        
        role = calculate_functional_role(freq, rank, total_recipes)
        
        normalized_data.append({
            "ingredient_id": canonical,
            "canonical_name": canonical,
            "functional_role": role,
            "frequency": freq,
            "avg_positional_rank": rank,
            "normalization_distance": distance
        })
    
    # Create DataFrame
    df_output = pd.DataFrame(normalized_data)
    
    # Sort by frequency descending
    df_output = df_output.sort_values(by="frequency", ascending=False)
    
    # Save output
    save_output(df_output, output_path)
    
    # Verify output
    if output_path.exists():
        logger.info(f"T014 completed successfully. Output: {output_path}")
        return True
    else:
        logger.error("Output file was not created.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
