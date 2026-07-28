import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd

def load_ingredient_pairs(pairs_path):
    """
    Load ingredient pairs from a parquet file.
    Expected columns: ingredient_id_1, ingredient_id_2
    """
    if not os.path.exists(pairs_path):
        raise FileNotFoundError(f"Ingredient pairs file not found: {pairs_path}")
    return pd.read_parquet(pairs_path)

def load_embeddings(embeddings_path):
    """
    Load ingredient embeddings from a parquet file.
    Expected columns: ingredient_id, embedding (as list/array)
    """
    if not os.path.exists(embeddings_path):
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")
    df = pd.read_parquet(embeddings_path)
    # Convert embedding lists to numpy arrays
    df['embedding'] = df['embedding'].apply(lambda x: np.array(x) if isinstance(x, list) else x)
    return df.set_index('ingredient_id')['embedding'].to_dict()

def compute_cosine_similarity(vec1, vec2):
    """
    Compute cosine similarity between two vectors.
    Returns a value between -1 and 1.
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

def process_similarity(pairs_df, embeddings_dict, output_path, log_path):
    """
    Process all pairs, compute cosine similarity, and save results.
    """
    results = []
    start_time = time.time()
    total = len(pairs_df)
    
    for idx, row in pairs_df.iterrows():
        id1 = row['ingredient_id_1']
        id2 = row['ingredient_id_2']
        
        if id1 not in embeddings_dict or id2 not in embeddings_dict:
            # Skip pairs with missing embeddings
            continue
        
        vec1 = embeddings_dict[id1]
        vec2 = embeddings_dict[id2]
        
        sim_score = compute_cosine_similarity(vec1, vec2)
        results.append({
            'ingredient_id_1': id1,
            'ingredient_id_2': id2,
            'similarity_score': sim_score
        })
        
        if (idx + 1) % 1000 == 0:
            elapsed = time.time() - start_time
            rate = (idx + 1) / elapsed if elapsed > 0 else 0
            print(f"Processed {idx+1}/{total} pairs ({elapsed:.2f}s, {rate:.1f} pairs/s)")

    output_df = pd.DataFrame(results)
    output_df.to_parquet(output_path, index=False)
    
    # Log processing stats
    log_data = {
        'total_pairs_processed': len(results),
        'processing_time_seconds': time.time() - start_time,
        'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    return output_df

def main():
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    embeddings_path = project_root / 'data' / 'processed' / 'ingredient_embeddings.parquet'
    pairs_path = project_root / 'data' / 'processed' / 'ingredient_pairs.parquet'
    output_path = project_root / 'data' / 'processed' / 'similarity_scores.parquet'
    log_path = project_root / 'data' / 'similarity_computation_log.json'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading embeddings from {embeddings_path}...")
    embeddings = load_embeddings(embeddings_path)
    print(f"Loaded {len(embeddings)} ingredient embeddings.")
    
    print(f"Loading ingredient pairs from {pairs_path}...")
    pairs_df = load_ingredient_pairs(pairs_path)
    print(f"Loaded {len(pairs_df)} ingredient pairs.")
    
    print("Computing cosine similarities...")
    result_df = process_similarity(pairs_df, embeddings, output_path, log_path)
    
    print(f"Similarity computation complete. Results saved to {output_path}")
    print(f"Processed {len(result_df)} pairs successfully.")

if __name__ == "__main__":
    main()
