"""
T016: Semantic Similarity Computation

Computes cosine similarity between Recipe1M embeddings for ingredient pairs.
Input: data/processed/ingredient_embeddings.parquet, data/processed/unique_ingredients.parquet
Output: data/processed/similarity_scores.parquet
"""
import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm

# Ensure paths are relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

def load_ingredient_pairs():
    """
    Loads unique ingredients and generates all unique pairs.
    Uses the unique_ingredients.parquet created in T014.
    """
    unique_ingredients_path = PROCESSED_DIR / "unique_ingredients.parquet"
    if not unique_ingredients_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {unique_ingredients_path}. "
            "Run T014 (normalization) first."
        )
    
    df = pd.read_parquet(unique_ingredients_path)
    # Expecting 'ingredient_id' column based on T014 output
    if 'ingredient_id' not in df.columns:
        # Fallback if column name differs, though schema dictates ingredient_id
        cols = [c for c in df.columns if 'ingredient' in c.lower() and 'id' in c.lower()]
        if cols:
            ingredient_col = cols[0]
        else:
            raise ValueError("Could not find ingredient_id column in unique_ingredients.parquet")
    else:
        ingredient_col = 'ingredient_id'
    
    ingredients = df[ingredient_col].tolist()
    
    # Generate unique pairs (i, j) where i < j to avoid duplicates and self-sim
    pairs = []
    n = len(ingredients)
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((ingredients[i], ingredients[j]))
    
    return pd.DataFrame(pairs, columns=['ingredient_id_1', 'ingredient_id_2'])

def load_embeddings():
    """
    Loads ingredient embeddings from T013d output.
    Returns a dictionary mapping ingredient_id -> embedding vector.
    """
    embeddings_path = PROCESSED_DIR / "ingredient_embeddings.parquet"
    if not embeddings_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {embeddings_path}. "
            "Run T013d (fetch embeddings) first."
        )
    
    df = pd.read_parquet(embeddings_path)
    
    # Identify columns: typically 'ingredient_id' and one or more embedding columns
    # We assume embedding columns are numeric and not 'ingredient_id'
    id_col = 'ingredient_id'
    if id_col not in df.columns:
        # Try to find id column
        id_candidates = [c for c in df.columns if 'id' in c.lower()]
        if id_candidates:
            id_col = id_candidates[0]
        else:
            raise ValueError("Could not find ingredient_id column in embeddings file")
    
    embedding_cols = [c for c in df.columns if c != id_col]
    if not embedding_cols:
        raise ValueError("No embedding columns found in embeddings file")
    
    # Build dictionary
    embeddings_dict = {}
    for _, row in df.iterrows():
        emb_id = row[id_col]
        emb_vec = row[embedding_cols].values.astype(np.float32)
        embeddings_dict[emb_id] = emb_vec
    
    return embeddings_dict

def compute_cosine_similarity(emb1, emb2):
    """
    Computes cosine similarity between two 1D numpy arrays.
    Handles zero vectors by returning 0.0.
    """
    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    dot_product = np.dot(emb1, emb2)
    return dot_product / (norm1 * norm2)

def process_similarity(pairs_df, embeddings_dict):
    """
    Iterates over pairs, looks up embeddings, computes cosine similarity.
    """
    results = []
    missing_count = 0
    
    # Use tqdm for progress bar
    for _, row in tqdm(pairs_df.iterrows(), total=len(pairs_df), desc="Computing Similarity"):
        id1 = row['ingredient_id_1']
        id2 = row['ingredient_id_2']
        
        if id1 not in embeddings_dict or id2 not in embeddings_dict:
            missing_count += 1
            # Skip pairs with missing embeddings to avoid errors
            # In a full pipeline, this might trigger a re-fetch or imputation
            continue
        
        emb1 = embeddings_dict[id1]
        emb2 = embeddings_dict[id2]
        
        sim_score = compute_cosine_similarity(emb1, emb2)
        results.append({
            'ingredient_id_1': id1,
            'ingredient_id_2': id2,
            'similarity_score': float(sim_score)
        })
    
    if missing_count > 0:
        print(f"Warning: Skipped {missing_count} pairs due to missing embeddings.")
    
    return pd.DataFrame(results)

def save_output(df):
    """
    Saves the similarity scores to parquet.
    """
    output_path = PROCESSED_DIR / "similarity_scores.parquet"
    
    # Ensure directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    print(f"Saved similarity scores to {output_path}")
    print(f"Total pairs processed: {len(df)}")
    
    # Log basic stats
    stats = {
        "total_pairs": len(df),
        "min_similarity": float(df['similarity_score'].min()),
        "max_similarity": float(df['similarity_score'].max()),
        "mean_similarity": float(df['similarity_score'].mean()),
        "output_file": str(output_path)
    }
    
    stats_path = PROCESSED_DIR / "similarity_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Saved stats to {stats_path}")

def main():
    print("Starting T016: Semantic Similarity Computation")
    
    try:
        # 1. Load Pairs
        print("Loading unique ingredients and generating pairs...")
        pairs_df = load_ingredient_pairs()
        print(f"Generated {len(pairs_df)} unique pairs.")
        
        # 2. Load Embeddings
        print("Loading ingredient embeddings...")
        embeddings_dict = load_embeddings()
        print(f"Loaded embeddings for {len(embeddings_dict)} ingredients.")
        
        # 3. Compute Similarity
        print("Computing cosine similarities...")
        start_time = time.time()
        similarity_df = process_similarity(pairs_df, embeddings_dict)
        elapsed = time.time() - start_time
        print(f"Computation took {elapsed:.2f} seconds.")
        
        # 4. Save Output
        print("Saving results...")
        save_output(similarity_df)
        
        print("T016 completed successfully.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during T016: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
