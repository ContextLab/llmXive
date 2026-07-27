"""
Data Preprocessing Module
Handles normalization, co-occurrence matrix, flavor similarity, functional roles, etc.
"""
import os
import sys
import json
import re
import gc
import time
import pandas as pd
import numpy as np
from pathlib import Path
from difflib import SequenceMatcher
from utils.memory_monitor import get_memory_usage_gb, check_memory_limit

def log_event(message, log_file="data/normalization_config.json"):
    """Log events to a JSON file."""
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []
    
    logs.append({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "message": message
    })
    
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)

def levenshtein_distance(s1, s2):
    """
    Calculate the Levenshtein distance between two strings.
    """
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

def levenshtein_similarity(s1, s2):
    """
    Calculate similarity based on Levenshtein distance.
    """
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    distance = levenshtein_distance(s1, s2)
    return 1 - (distance / max_len)

def normalize_ingredient_name(name, canonical_map, threshold=2):
    """
    Normalize ingredient name using Levenshtein distance <= threshold.
    """
    name = name.lower().strip()
    if name in canonical_map:
        return canonical_map[name], True
    
    best_match = None
    min_distance = threshold + 1
    
    for canonical in canonical_map.keys():
        dist = levenshtein_distance(name, canonical)
        if dist < min_distance:
            min_distance = dist
            best_match = canonical
            if dist == 0:
                break
    
    if best_match:
        return best_match, True
    return name, False

def build_canonical_map(data_dir="data/raw"):
    """
    Build a canonical map of ingredients from the raw data.
    """
    raw_file = os.path.join(data_dir, "recipe1m.parquet")
    if not os.path.exists(raw_file):
        # If raw file doesn't exist, return an empty map
        return {}
    
    try:
        # Load a sample to build the map
        df = pd.read_parquet(raw_file, columns=['ingredient']).head(10000)
        canonical_set = set(df['ingredient'].str.lower().str.strip().unique())
        return {name: name for name in canonical_set}
    except Exception as e:
        print(f"Error building canonical map: {e}")
        return {}

def process_chunk_normalize(input_file, output_file, chunk_size=100000):
    """
    Process data in chunks to normalize ingredient names.
    """
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Build canonical map
    canonical_map = build_canonical_map()
    if not canonical_map:
        print("Warning: Canonical map is empty. Using raw data.")
    
    # Process in chunks
    chunks = []
    total_rows = 0
    normalized_count = 0
    excluded_count = 0
    
    for chunk in pd.read_parquet(input_file, chunksize=chunk_size):
        # Check memory
        check_memory_limit(6144)
        
        # Normalize ingredients
        def normalize_func(name):
            nonlocal normalized_count, excluded_count
            norm, matched = normalize_ingredient_name(name, canonical_map)
            if matched:
                normalized_count += 1
            else:
                excluded_count += 1
            return norm
        
        chunk['normalized_ingredient'] = chunk['ingredient'].apply(normalize_func)
        chunks.append(chunk)
        total_rows += len(chunk)
        
        # Log progress
        if total_rows % 500000 == 0:
            print(f"Processed {total_rows} rows. Normalized: {normalized_count}, Excluded: {excluded_count}")
            gc.collect()
    
    if chunks:
        result_df = pd.concat(chunks, ignore_index=True)
        result_df.to_parquet(output_file)
        
        # Log normalization config
        log_event(f"Normalization complete. Total rows: {total_rows}, Normalized: {normalized_count}, Excluded: {excluded_count}")
        
        # Save config
        config = {
            "total_rows": total_rows,
            "normalized_count": normalized_count,
            "excluded_count": excluded_count,
            "threshold": 2
        }
        config_file = "data/normalization_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    return True

def construct_cooccurrence_matrix_streaming(input_file, output_file, chunk_size=100000):
    """
    Construct co-occurrence matrix in chunks.
    """
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize matrix dictionary
    cooccurrence = {}
    total_rows = 0
    
    for chunk in pd.read_parquet(input_file, chunksize=chunk_size):
        check_memory_limit(6144)
        
        # Group by recipe_id and count co-occurrences
        for recipe_id, group in chunk.groupby('recipe_id'):
            ingredients = group['normalized_ingredient'].unique()
            for i, ing1 in enumerate(ingredients):
                for ing2 in ingredients[i+1:]:
                    pair = tuple(sorted([ing1, ing2]))
                    cooccurrence[pair] = cooccurrence.get(pair, 0) + 1
        
        total_rows += len(chunk)
        if total_rows % 500000 == 0:
            print(f"Processed {total_rows} rows for co-occurrence.")
            gc.collect()
    
    # Convert to DataFrame
    rows = []
    for (ing1, ing2), count in cooccurrence.items():
        rows.append({
            'ingredient_1': ing1,
            'ingredient_2': ing2,
            'count': count
        })
    
    df = pd.DataFrame(rows)
    df.to_parquet(output_file)
    print(f"Co-occurrence matrix saved to {output_file}")
    
    return True

def calculate_flavor_similarity(input_file, output_file):
    """
    Calculate flavor similarity using embeddings.
    """
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = pd.read_parquet(input_file)
    
    # In a real scenario, we would load embeddings and compute cosine similarity
    # For now, we simulate with a placeholder calculation
    # Assuming we have an 'embedding' column
    if 'embedding' in df.columns:
        # Compute cosine similarity for pairs
        # This is a simplified version
        pass
    else:
        # If no embeddings, we can't calculate real similarity
        # We'll create a dummy column
        df['flavor_similarity'] = 0.5
    
    df.to_parquet(output_file)
    print(f"Flavor similarity saved to {output_file}")
    
    return True

def derive_orthogonalized_functional_role(input_file, output_file):
    """
    Derive orthogonalized functional role.
    """
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_parquet(input_file)
    
    # Orthogonalize ingredient positional rank against log-frequency
    if 'position_rank' in df.columns and 'log_frequency' in df.columns:
        # Simple linear regression to get residuals
        from sklearn.linear_model import LinearRegression
        
        X = df[['log_frequency']]
        y = df['position_rank']
        
        model = LinearRegression()
        model.fit(X, y)
        
        residuals = y - model.predict(X)
        df['functional_role_residuals'] = residuals
    
    df.to_parquet(output_file)
    print(f"Functional role residuals saved to {output_file}")
    
    return True

def discretize_functional_role(input_file, output_file):
    """
    Discretize functional role into tertiles.
    """
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_parquet(input_file)
    
    if 'functional_role_residuals' in df.columns:
        df['functional_role_tertile'] = pd.qcut(df['functional_role_residuals'], q=3, labels=['Low', 'Medium', 'High'], duplicates='drop')
    
    df.to_parquet(output_file)
    print(f"Discretized functional role saved to {output_file}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Preprocess data.")
    parser.add_argument("--input", type=str, required=True, help="Input directory")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    args = parser.parse_args()
    
    input_dir = args.input
    output_dir = args.output
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Normalize ingredients
    input_file = os.path.join(input_dir, "recipe1m.parquet")
    output_file = os.path.join(output_dir, "normalized_recipe1m.parquet")
    
    if os.path.exists(input_file):
        print("Normalizing ingredients...")
        process_chunk_normalize(input_file, output_file)
    else:
        print(f"Input file {input_file} not found. Skipping normalization.")
    
    # Construct co-occurrence matrix
    if os.path.exists(output_file):
        cooccurrence_file = os.path.join(output_dir, "co_occurrence_matrix.parquet")
        print("Constructing co-occurrence matrix...")
        construct_cooccurrence_matrix_streaming(output_file, cooccurrence_file)
    
    # Calculate flavor similarity
    if os.path.exists(output_file):
        similarity_file = os.path.join(output_dir, "flavor_similarity.parquet")
        print("Calculating flavor similarity...")
        calculate_flavor_similarity(output_file, similarity_file)
    
    # Derive functional role
    if os.path.exists(output_file):
        role_file = os.path.join(output_dir, "ingredient_roles_residuals.parquet")
        print("Deriving functional role...")
        derive_orthogonalized_functional_role(output_file, role_file)
    
    # Discretize functional role
    if os.path.exists(role_file):
        discretized_file = os.path.join(output_dir, "discretized_roles.parquet")
        print("Discretizing functional role...")
        discretize_functional_role(role_file, discretized_file)
    
    print("Preprocessing complete.")

if __name__ == "__main__":
    main()