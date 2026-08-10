import os
import sys
import json
import time
import gc
from pathlib import Path
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

# Ensure reproducibility
SEED = 42
np.random.seed(SEED)

def ensure_directories(output_path: Path) -> None:
    """Ensure the output directory exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

def load_ingredient_list(input_path: Path) -> pd.DataFrame:
    """
    Load the normalized ingredients CSV.
    Expected columns: ingredient_id, canonical_name, frequency
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    required_cols = ['ingredient_id', 'canonical_name']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    return df

def fetch_embeddings_for_ingredients(
    ingredient_names: List[str], 
    model: SentenceTransformer,
    batch_size: int = 32
) -> np.ndarray:
    """
    Fetch embeddings for a list of ingredient names using the SentenceTransformer model.
    Returns a numpy array of shape (N, embedding_dim).
    """
    if not ingredient_names:
        return np.array([])
    
    embeddings = model.encode(
        ingredient_names,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True
    )
    return embeddings

def aggregate_embeddings(
    ingredient_df: pd.DataFrame,
    embeddings: np.ndarray
) -> pd.DataFrame:
    """
    Attach embeddings to the ingredient dataframe.
    Returns a dataframe with ingredient_id, canonical_name, and embedding_vector (list).
    """
    if len(embeddings) != len(ingredient_df):
        raise ValueError("Embedding count mismatch with ingredient count.")
    
    # Convert numpy array to list of lists for JSON/Parquet serialization compatibility
    embedding_list = embeddings.tolist()
    
    result_df = ingredient_df.copy()
    result_df['embedding_vector'] = embedding_list
    return result_df

def save_embeddings(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the embeddings to a Parquet file.
    """
    ensure_directories(output_path)
    # Convert list of lists to string or keep as object if parquet supports it.
    # Parquet supports lists, but to be safe with all engines, we store as list.
    df.to_parquet(output_path, index=False)
    print(f"Saved embeddings to {output_path}")

def compute_cosine_similarity_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute pairwise cosine similarity between all ingredient embeddings.
    Returns a dataframe with columns: ingredient_id_1, ingredient_id_2, similarity_score.
    """
    if 'embedding_vector' not in df.columns:
        raise ValueError("Embedding vectors not found in dataframe.")
    
    embeddings = np.array(df['embedding_vector'].tolist())
    ids = df['ingredient_id'].values
    
    # Normalize embeddings for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    # Avoid division by zero
    norms[norms == 0] = 1e-9
    normalized = embeddings / norms
    
    # Compute dot product
    similarity_matrix = np.dot(normalized, normalized.T)
    
    # Convert to long format
    results = []
    n = len(ids)
    for i in range(n):
        for j in range(i + 1, n):
            results.append({
                'ingredient_id_1': ids[i],
                'ingredient_id_2': ids[j],
                'similarity_score': float(similarity_matrix[i, j])
            })
    
    return pd.DataFrame(results)

def process_similarity(similarity_df: pd.DataFrame, output_path: Path) -> None:
    """
    Process and save the similarity scores.
    """
    ensure_directories(output_path)
    similarity_df.to_parquet(output_path, index=False)
    print(f"Saved similarity scores to {output_path}")

def save_output(df: pd.DataFrame, output_path: Path) -> None:
    """
    Generic save output function for the embedding dataframe if needed.
    """
    ensure_directories(output_path)
    df.to_parquet(output_path, index=False)

def main():
    """
    Main entry point for T016b: Embedding Similarity.
    Reads amendment_log.json. If methodology is 'Correlational Analysis',
    computes embeddings and similarity scores. Otherwise, skips.
    """
    # Paths
    project_root = Path(__file__).resolve().parent.parent.parent
    amendment_log_path = project_root / "data" / "amendment_log.json"
    input_ingredients_path = project_root / "data" / "processed" / "normalized_ingredients.csv"
    output_embeddings_path = project_root / "data" / "processed" / "ingredient_embeddings.parquet"
    output_similarity_path = project_root / "data" / "processed" / "similarity_scores_embedding.parquet"

    # Check Amendment Log
    if not amendment_log_path.exists():
        raise FileNotFoundError(f"Amendment log not found at {amendment_log_path}. Run T012 first.")
    
    with open(amendment_log_path, 'r') as f:
        amendment_data = json.load(f)
    
    methodology = amendment_data.get("methodology")
    
    if methodology != "Correlational Analysis":
        print(f"Methodology is '{methodology}'. Skipping T016b (Embedding Similarity) as per spec.")
        # Create an empty file or a placeholder to indicate skipped status if required by pipeline
        # But spec says "SKIP this task", so we just exit cleanly.
        return

    print(f"Methodology is 'Correlational Analysis'. Proceeding with T016b.")

    # Load Ingredients
    print("Loading normalized ingredients...")
    ingredient_df = load_ingredient_list(input_ingredients_path)
    
    # Load Model
    print("Loading SentenceTransformer model (all-MiniLM-L6-v2)...")
    # This model is small enough to run on CPU/GPU automatically detected by the library
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        print(f"Error loading model: {e}")
        # If the model download fails, we must fail loudly, not fallback to synthetic
        raise RuntimeError("Failed to load SentenceTransformer model. Ensure internet access or pre-cached model.")

    # Fetch Embeddings
    print(f"Fetching embeddings for {len(ingredient_df)} ingredients...")
    ingredient_names = ingredient_df['canonical_name'].tolist()
    
    # Process in batches if needed, but the function handles batches internally
    embeddings = fetch_embeddings_for_ingredients(ingredient_names, model)
    
    # Aggregate
    print("Aggregating embeddings...")
    embedded_df = aggregate_embeddings(ingredient_df, embeddings)
    
    # Save Embeddings
    print("Saving embeddings...")
    save_embeddings(embedded_df, output_embeddings_path)
    
    # Compute Similarity
    print("Computing pairwise cosine similarity...")
    similarity_df = compute_cosine_similarity_matrix(embedded_df)
    
    # Save Similarity
    print("Saving similarity scores...")
    process_similarity(similarity_df, output_similarity_path)
    
    print("T016b completed successfully.")

if __name__ == "__main__":
    main()
