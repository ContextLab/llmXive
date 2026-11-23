import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

def load_epsilon_config():
    """Load epsilon configuration for log smoothing."""
    config_path = Path("data/processed/epsilon_config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {"epsilon": 1e-6}

def load_ingredient_pairs():
    """
    Load the normalized ingredient pairs with functional roles.
    This expects the output of T014a and T014b to be merged.
    Since T018 (imputation) hasn't run yet, we look for the raw processed pairs
    or reconstruct from normalized ingredients and functional roles if needed.
    
    For this specific task T015, we assume the existence of a consolidated
    ingredient list that T014a produced, or we read from the raw recipe stream
    if the processed file is missing (as indicated by execution failures).
    
    However, based on the API surface and task dependencies:
    T015 depends on T014a (normalized_ingredients.csv) and T014b (functional_roles.csv).
    But to build a co-occurrence matrix, we need the RECIPE data (which ingredients appear together).
    
    Re-reading tasks.md:
    "T015 Co-occurrence Matrix: Construct global co-occurrence matrix C. ... Count pairs (i, j) in recipes."
    
    The raw recipe data is in data/raw/recipe1m_processed.parquet (from T013a).
    We must stream or load this, normalize the ingredients using the T014a mapping,
    and then count pairs.
    
    Let's check if T013a produced the file. If not, we fail loudly.
    """
    recipe_path = Path("data/raw/recipe1m_processed.parquet")
    if not recipe_path.exists():
        raise FileNotFoundError(
            f"Raw recipe data not found at {recipe_path}. "
            "Run T013a (Stream & Validate Recipe1M) first."
        )
    
    # Load the processed recipe data
    # Depending on the size, we might need to stream or load in chunks.
    # For now, assuming it fits or is a sample as per T013b power analysis.
    try:
        df = pd.read_parquet(recipe_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load recipe data: {e}")
    
    # Ensure we have the columns needed. 
    # T013a should have ensured 'rating' is present if proxy, but for co-occurrence we need 'ingredients'.
    if 'ingredients' not in df.columns:
        # Try common variations
        if 'ingredient_list' in df.columns:
            ingredients_col = 'ingredient_list'
        elif 'ingredient_names' in df.columns:
            ingredients_col = 'ingredient_names'
        else:
            raise ValueError(
                f"Recipe data must contain an 'ingredients' column. "
                f"Found columns: {df.columns.tolist()}"
            )
    else:
        ingredients_col = 'ingredients'
    
    # Load the normalized ingredient mapping from T014a
    normalized_path = Path("data/processed/normalized_ingredients.csv")
    if not normalized_path.exists():
        raise FileNotFoundError(
            f"Normalized ingredient mapping not found at {normalized_path}. "
            "Run T014a (Normalize Ingredients) first."
        )
    
    norm_df = pd.read_csv(normalized_path)
    # Expected columns: ingredient_id, canonical_name, frequency
    if 'canonical_name' not in norm_df.columns or 'ingredient_id' not in norm_df.columns:
        raise ValueError("normalized_ingredients.csv must have 'canonical_name' and 'ingredient_id' columns.")
    
    # Create a mapping from canonical_name to ingredient_id
    # Handle potential duplicates by taking the first or aggregating (though T014a should handle this)
    name_to_id = norm_df.set_index('canonical_name')['ingredient_id'].to_dict()
    
    # Map ingredients in the recipe dataframe
    def normalize_ingredient_list(ing_list):
        if isinstance(ing_list, str):
            # If it's a string representation of a list, try to parse
            try:
                ing_list = eval(ing_list)
            except:
                return []
        if not isinstance(ing_list, list):
            return []
        
        normalized_ids = []
        for ing in ing_list:
            # Normalize the ingredient name (lowercase, strip)
            canonical = ing.lower().strip() if isinstance(ing, str) else str(ing).lower().strip()
            if canonical in name_to_id:
                normalized_ids.append(name_to_id[canonical])
            else:
                # If not found, we might need to normalize it ourselves using Levenshtein if T014a missed it
                # But for now, we skip unknowns to avoid polluting the matrix with noise.
                # In a real scenario, T014a should have covered all.
                pass
        return normalized_ids
    
    # Apply normalization
    df['normalized_ingredient_ids'] = df[ingredients_col].apply(normalize_ingredient_list)
    
    return df

def build_cooccurrence_matrix(recipe_df):
    """
    Build the global co-occurrence matrix C from the recipe dataframe.
    C[i, j] = count of recipes containing both ingredient i and j.
    """
    # Extract all unique ingredient IDs
    all_ids = set()
    for ids in recipe_df['normalized_ingredient_ids']:
        all_ids.update(ids)
    
    id_list = sorted(list(all_ids))
    id_to_idx = {id_val: idx for idx, id_val in enumerate(id_list)}
    n = len(id_list)
    
    # Initialize matrix
    # Using a sparse matrix approach first to save memory, then converting to dense if needed
    # But for a co-occurrence matrix of ingredients, it might be dense if many ingredients co-occur.
    # Let's use a dictionary to count pairs first.
    pair_counts = {}
    
    for ids in recipe_df['normalized_ingredient_ids']:
        if len(ids) < 2:
            continue
        # Sort to avoid double counting (i, j) and (j, i)
        unique_ids = sorted(list(set(ids)))
        for i in range(len(unique_ids)):
            for j in range(i + 1, len(unique_ids)):
                pair = (unique_ids[i], unique_ids[j])
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
    
    # Create the matrix
    co_occurrence = np.zeros((n, n), dtype=np.int64)
    
    for (id1, id2), count in pair_counts.items():
        idx1 = id_to_idx[id1]
        idx2 = id_to_idx[id2]
        co_occurrence[idx1, idx2] = count
        co_occurrence[idx2, idx1] = count
    
    # Diagonal: count of recipes containing the ingredient (self-co-occurrence)
    # We can compute this from the recipe_df
    id_counts = {}
    for ids in recipe_df['normalized_ingredient_ids']:
        for id_val in ids:
            id_counts[id_val] = id_counts.get(id_val, 0) + 1
    
    for id_val, count in id_counts.items():
        idx = id_to_idx[id_val]
        co_occurrence[idx, idx] = count
    
    # Create a DataFrame for easier handling
    co_occurrence_df = pd.DataFrame(
        co_occurrence,
        index=id_list,
        columns=id_list
    )
    
    # Store the ID mapping for later use
    mapping_df = pd.DataFrame({
        'ingredient_id': id_list,
        'index': range(n)
    })
    
    return co_occurrence_df, mapping_df

def save_output(co_occurrence_df, mapping_df, output_path, epsilon_config):
    """
    Save the co-occurrence matrix to a parquet file with log-transform and epsilon smoothing.
    Output: data/processed/co_occurrence_matrix.parquet
    """
    # Apply log-transform with epsilon smoothing: log(C + epsilon)
    epsilon = epsilon_config.get('epsilon', 1e-6)
    log_co_occurrence = np.log(co_occurrence_df + epsilon)
    
    # Save the log-transformed matrix
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    log_co_occurrence.to_parquet(output_file, index=True)
    
    # Save the mapping as well
    mapping_path = output_file.parent / "co_occurrence_mapping.csv"
    mapping_df.to_csv(mapping_path, index=False)
    
    # Save the config used
    config_path = output_file.parent / "co_occurrence_config.json"
    with open(config_path, 'w') as f:
        json.dump(epsilon_config, f, indent=2)
    
    return output_file

def main():
    """
    Main function to execute T015: Co-occurrence Matrix construction.
    """
    print("Starting T015: Co-occurrence Matrix construction...")
    
    # Load configuration
    epsilon_config = load_epsilon_config()
    
    # Load data
    try:
        recipe_df = load_ingredient_pairs()
        print(f"Loaded {len(recipe_df)} recipes.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Build matrix
    print("Building co-occurrence matrix...")
    co_occurrence_df, mapping_df = build_cooccurrence_matrix(recipe_df)
    print(f"Matrix shape: {co_occurrence_df.shape}")
    
    # Save output
    output_path = "data/processed/co_occurrence_matrix.parquet"
    try:
        save_output(co_occurrence_df, mapping_df, output_path, epsilon_config)
        print(f"Successfully saved co-occurrence matrix to {output_path}")
    except Exception as e:
        print(f"Error saving output: {e}")
        sys.exit(1)
    
    print("T015 completed successfully.")

if __name__ == "__main__":
    main()
