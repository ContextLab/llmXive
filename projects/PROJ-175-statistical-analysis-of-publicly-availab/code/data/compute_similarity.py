import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd

def load_ingredient_pairs(input_path: str) -> pd.DataFrame:
    """
    Load ingredient pairs from a Parquet file.
    Expected schema: ['ingredient_id_1', 'ingredient_id_2'] (or similar pair columns).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_parquet(input_path)
    required_cols = ['ingredient_id_1', 'ingredient_id_2']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    return df

def load_embeddings(embeddings_path: str) -> dict:
    """
    Load ingredient embeddings from a Parquet file into a dictionary.
    Expected schema: ['ingredient_id', 'embedding'] where 'embedding' is a list/array.
    """
    if not os.path.exists(embeddings_path):
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")
    df = pd.read_parquet(embeddings_path)
    required_cols = ['ingredient_id', 'embedding']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {embeddings_path}: {missing}")

    # Convert to dict: {id: np_array}
    emb_dict = {}
    for _, row in df.iterrows():
        try:
            emb_dict[row['ingredient_id']] = np.array(row['embedding'], dtype=np.float32)
        except Exception as e:
            # Log or skip malformed embeddings if necessary
            continue
    return emb_dict

def compute_cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """
    Compute cosine similarity between two 1D numpy arrays.
    Returns a float in [-1, 1].
    """
    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(emb1, emb2) / (norm1 * norm2))

def process_similarity(pairs_df: pd.DataFrame, embeddings: dict) -> pd.DataFrame:
    """
    Process ingredient pairs and compute cosine similarity for each pair.
    Returns a DataFrame with columns: ingredient_id_1, ingredient_id_2, similarity_score.
    """
    results = []
    missing_count = 0
    for _, row in pairs_df.iterrows():
        id1 = row['ingredient_id_1']
        id2 = row['ingredient_id_2']

        emb1 = embeddings.get(id1)
        emb2 = embeddings.get(id2)

        if emb1 is None or emb2 is None:
            missing_count += 1
            # Skip pairs with missing embeddings; could also log or fill later
            continue

        sim = compute_cosine_similarity(emb1, emb2)
        results.append({
            'ingredient_id_1': id1,
            'ingredient_id_2': id2,
            'similarity_score': sim
        })

    if missing_count > 0:
        print(f"Warning: Skipped {missing_count} pairs due to missing embeddings.")

    return pd.DataFrame(results)

def save_output(output_df: pd.DataFrame, output_path: str):
    """
    Save the similarity scores DataFrame to a Parquet file.
    """
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_parquet(output_path, index=False)
    print(f"Saved similarity scores to {output_path}")

def main():
    """
    Main entry point for computing semantic similarity.
    Usage: python code/data/compute_similarity.py
    Expects:
      - data/processed/ingredient_embeddings.parquet (from T014c)
      - A pairs file (e.g., data/processed/ingredient_pairs.parquet or similar)
    Outputs:
      - data/processed/similarity_scores.parquet
    """
    # Define paths based on project structure and task description
    embeddings_path = "data/processed/ingredient_embeddings.parquet"
    # We assume a pairs file exists; if not, we might need to generate or load from another source.
    # For T016, we assume ingredient_pairs.parquet exists or is derived from normalized ingredients.
    # If not present, we can try to generate pairs from the embeddings file itself (unique IDs).
    pairs_path = "data/processed/ingredient_pairs.parquet"

    # If pairs file doesn't exist, generate all unique pairs from embeddings
    if not os.path.exists(pairs_path):
        print("Pairs file not found. Generating all unique pairs from embeddings...")
        if not os.path.exists(embeddings_path):
            raise FileNotFoundError(f"Neither pairs nor embeddings file found.")
        emb_df = pd.read_parquet(embeddings_path)
        if 'ingredient_id' not in emb_df.columns:
            raise ValueError("Embeddings file must contain 'ingredient_id' column.")
        ids = emb_df['ingredient_id'].unique()
        # Generate all unique pairs (i, j) where i < j to avoid duplicates and self
        pairs = []
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pairs.append({'ingredient_id_1': ids[i], 'ingredient_id_2': ids[j]})
        pairs_df = pd.DataFrame(pairs)
        # Save generated pairs for potential reuse
        pairs_df.to_parquet(pairs_path, index=False)
        print(f"Generated {len(pairs)} pairs and saved to {pairs_path}")
    else:
        pairs_df = load_ingredient_pairs(pairs_path)

    print(f"Loaded {len(pairs_df)} ingredient pairs.")
    print("Loading embeddings...")
    embeddings = load_embeddings(embeddings_path)
    print(f"Loaded embeddings for {len(embeddings)} ingredients.")

    print("Computing cosine similarities...")
    start_time = time.time()
    similarity_df = process_similarity(pairs_df, embeddings)
    elapsed = time.time() - start_time
    print(f"Computed {len(similarity_df)} similarities in {elapsed:.2f} seconds.")

    output_path = "data/processed/similarity_scores.parquet"
    save_output(similarity_df, output_path)

    # Verify output
    if os.path.exists(output_path):
        print("Task T016 completed successfully.")
    else:
        raise RuntimeError("Output file was not created.")

if __name__ == "__main__":
    main()
