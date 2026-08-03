"""
T016: Semantic Similarity - Compute cosine similarity between ingredient embeddings.

This module implements the semantic similarity computation step of the pipeline.
It loads ingredient embeddings (either from FlavorDB chemical vectors or Recipe1M
visual/text embeddings based on T012a status) and computes pairwise cosine similarity.

Output: data/processed/similarity_scores.parquet
"""
import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure consistent random seed
from code import seed
np.random.seed(seed)

def load_ingredient_pairs(input_path: str) -> pd.DataFrame:
    """
    Load the normalized ingredient pairs from T014 output.
    
    Args:
        input_path: Path to the normalized_ingredients.csv file
        
    Returns:
        DataFrame with ingredient pairs and metadata
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Ingredient pairs file not found: {input_path}")
    
    logger.info(f"Loading ingredient pairs from {input_path}")
    df = pd.read_csv(path)
    
    # Validate required columns
    required_cols = ['ingredient_id', 'normalized_name', 'functional_role']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in ingredient pairs: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} ingredients with {df['ingredient_id'].nunique()} unique IDs")
    return df

def load_embeddings(data_dir: str, use_flavordb: bool) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
    """
    Load ingredient embeddings.
    
    If FlavorDB is available (use_flavordb=True), load chemical vectors.
    Otherwise, load Recipe1M embeddings (visual/text).
    
    Args:
        data_dir: Directory containing embedding files
        use_flavordb: Whether to use FlavorDB embeddings
        
    Returns:
        Tuple of (ingredient list DataFrame, embeddings dictionary)
    """
    data_path = Path(data_dir)
    
    if use_flavordb:
        embedding_file = data_path / "flavordb_embeddings.parquet"
        source_name = "FlavorDB"
    else:
        embedding_file = data_path / "recipe1m_embeddings.parquet"
        source_name = "Recipe1M"
    
    if not embedding_file.exists():
        raise FileNotFoundError(
            f"{source_name} embeddings not found at {embedding_file}. "
            f"Run the appropriate embedding generation step first."
        )
    
    logger.info(f"Loading {source_name} embeddings from {embedding_file}")
    embeddings_df = pd.read_parquet(embedding_file)
    
    # Validate required columns
    if use_flavordb:
        required_cols = ['ingredient_id', 'vector']
    else:
        required_cols = ['ingredient_id', 'embedding_vector']
        
    missing_cols = [col for col in required_cols if col not in embeddings_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in embeddings: {missing_cols}")
    
    # Convert to dictionary for efficient lookup
    embeddings_dict = {}
    for _, row in embeddings_df.iterrows():
        if use_flavordb:
            vec = row['vector']
        else:
            vec = row['embedding_vector']
        
        # Ensure vector is numpy array
        if isinstance(vec, list):
            vec = np.array(vec)
        elif isinstance(vec, np.ndarray):
            pass
        else:
            # Handle string representation if necessary
            vec = np.fromstring(vec.strip('[]'), sep=',')
        
        embeddings_dict[row['ingredient_id']] = vec
    
    logger.info(f"Loaded {len(embeddings_dict)} ingredient embeddings from {source_name}")
    return embeddings_df, embeddings_dict

def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity value between -1 and 1
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return np.dot(vec1, vec2) / (norm1 * norm2)

def process_similarity(
    ingredient_pairs: pd.DataFrame,
    embeddings: Dict[str, np.ndarray],
    output_path: str
) -> pd.DataFrame:
    """
    Compute pairwise cosine similarity for all ingredient pairs.
    
    Args:
        ingredient_pairs: DataFrame with ingredient pairs
        embeddings: Dictionary mapping ingredient_id to embedding vector
        output_path: Path to save the results
        
    Returns:
        DataFrame with similarity scores
    """
    logger.info("Computing pairwise cosine similarities...")
    
    results = []
    unique_ingredients = ingredient_pairs['ingredient_id'].unique()
    
    # Filter ingredients that have embeddings
    available_ingredients = [ing for ing in unique_ingredients if ing in embeddings]
    missing_ingredients = set(unique_ingredients) - set(available_ingredients)
    
    if missing_ingredients:
        logger.warning(f"Skipping {len(missing_ingredients)} ingredients without embeddings: {missing_ingredients}")
    
    start_time = time.time()
    total_pairs = 0
    
    for i, ing1_id in enumerate(available_ingredients):
        if ing1_id not in embeddings:
            continue
        
        vec1 = embeddings[ing1_id]
        
        for ing2_id in available_ingredients[i:]:
            if ing2_id not in embeddings:
                continue
            
            vec2 = embeddings[ing2_id]
            similarity = compute_cosine_similarity(vec1, vec2)
            
            results.append({
                'ingredient_id_1': ing1_id,
                'ingredient_id_2': ing2_id,
                'cosine_similarity': similarity,
                'vector_norm_1': np.linalg.norm(vec1),
                'vector_norm_2': np.linalg.norm(vec2)
            })
            
            total_pairs += 1
            
            # Log progress every 1000 pairs
            if total_pairs % 1000 == 0:
                elapsed = time.time() - start_time
                logger.info(f"Processed {total_pairs} pairs ({elapsed:.2f}s)")
    
    logger.info(f"Computed {total_pairs} similarity pairs in {time.time() - start_time:.2f}s")
    
    similarity_df = pd.DataFrame(results)
    
    if similarity_df.empty:
        raise ValueError("No similarity scores computed. Check that ingredients have valid embeddings.")
    
    # Save to parquet
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving similarity scores to {output_path}")
    similarity_df.to_parquet(output_path, index=False)
    
    # Log summary statistics
    logger.info(f"Similarity statistics: mean={similarity_df['cosine_similarity'].mean():.4f}, "
               f"std={similarity_df['cosine_similarity'].std():.4f}, "
               f"min={similarity_df['cosine_similarity'].min():.4f}, "
               f"max={similarity_df['cosine_similarity'].max():.4f}")
    
    return similarity_df

def save_output(similarity_df: pd.DataFrame, output_path: str) -> None:
    """
    Save the similarity scores to the output file.
    
    Args:
        similarity_df: DataFrame with similarity scores
        output_path: Path to save the results
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    similarity_df.to_parquet(output_path, index=False)
    logger.info(f"Saved similarity scores to {output_path}")

def main():
    """
    Main entry point for T016.
    
    Usage:
        python code/data/compute_similarity.py
        
    Expected inputs:
        - data/processed/normalized_ingredients.csv (from T014)
        - data/raw/flavordb_embeddings.parquet OR data/raw/recipe1m_embeddings.parquet
        
    Output:
        - data/processed/similarity_scores.parquet
    """
    logger.info("Starting T016: Semantic Similarity Computation")
    
    # Configuration
    base_dir = Path(__file__).parent.parent.parent
    data_dir = base_dir / "data"
    processed_dir = data_dir / "processed"
    raw_dir = data_dir / "raw"
    
    # Load download status to determine which embeddings to use
    download_status_path = data_dir / "download_status.json"
    if not download_status_path.exists():
        raise FileNotFoundError(
            f"Download status file not found: {download_status_path}. "
            f"Run T012a first."
        )
    
    with open(download_status_path, 'r') as f:
        download_status = json.load(f)
    
    use_flavordb = download_status.get('flavordb', {}).get('status') == 'SUCCESS'
    logger.info(f"Using {'FlavorDB' if use_flavordb else 'Recipe1M'} embeddings")
    
    # Load ingredient pairs
    ingredient_pairs_path = processed_dir / "normalized_ingredients.csv"
    ingredient_pairs = load_ingredient_pairs(str(ingredient_pairs_path))
    
    # Load embeddings
    embeddings_df, embeddings_dict = load_embeddings(str(raw_dir), use_flavordb)
    
    # Compute similarity
    output_path = str(processed_dir / "similarity_scores.parquet")
    similarity_df = process_similarity(ingredient_pairs, embeddings_dict, output_path)
    
    # Save output
    save_output(similarity_df, output_path)
    
    logger.info("T016 completed successfully")
    return similarity_df

if __name__ == "__main__":
    main()