"""
Embeddings module for training Word2Vec and aggregating yearly genre vectors.
"""
import os
import gc
import logging
from pathlib import Path
from typing import List, Iterator, Optional, Dict, Any
import json
import numpy as np
import pandas as pd

from utils import setup_logging, get_logger, set_deterministic_seed
from memory_utils import check_memory_thresholds, trigger_garbage_collection, get_memory_usage_gb

logger = setup_logging()

DATA_DERIVED_DIR = Path(__file__).resolve().parent.parent / "data" / "derived"
YEARLY_EMBEDDINGS_DIR = DATA_DERIVED_DIR.parent / "yearly_embeddings"

def setup_embeddings_environment():
    """
    Setup environment for embeddings.

    Raises:
        RuntimeError: If gensim is not installed.
    """
    try:
        from gensim.models import Word2Vec
    except ImportError:
        raise RuntimeError("gensim is required for embeddings.")
    
    YEARLY_EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Embeddings environment ready.")

def load_metadata_batches() -> Iterator[pd.DataFrame]:
    """
    Load metadata batches from parquet files.

    Yields:
        Iterator[pd.DataFrame]: Chunks of the metadata DataFrame.

    Raises:
        FileNotFoundError: If the metadata file is not found.
    """
    path = DATA_DERIVED_DIR / "metadata_mpd.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {path}")
    
    # Read in chunks to simulate streaming/batching
    for chunk in pd.read_parquet(path, chunksize=10000):
        yield chunk

def generate_track_sequences(df: pd.DataFrame) -> Iterator[List[str]]:
    """
    Generate sequences of genres per playlist for Word2Vec training.

    Args:
        df (pd.DataFrame): DataFrame containing playlist and genre data.

    Yields:
        Iterator[List[str]]: Sequences of genres.
    """
    # Group by playlist_id and sort by year or index
    # For this demo, we assume a 'playlist_id' and 'genre' column
    if 'playlist_id' not in df.columns or 'genre' not in df.columns:
        logger.warning("Missing required columns for sequence generation.")
        return
    
    grouped = df.groupby('playlist_id')
    for _, group in grouped:
        genres = group['genre'].dropna().tolist()
        if len(genres) > 1:
            yield genres

def train_global_word2vec(sequence_iterator: Iterator[List[str]], dim: int = 100, window: int = 10, epochs: int = 5):
    """
    Train a global Word2Vec model on the sequence iterator.

    Args:
        sequence_iterator (Iterator[List[str]]): Iterator of genre sequences.
        dim (int): Dimensionality of the word vectors.
        window (int): Maximum distance between current and predicted word.
        epochs (int): Number of epochs to train.

    Returns:
        Word2Vec: Trained Word2Vec model.

    Raises:
        RuntimeError: If training fails.
    """
    from gensim.models import Word2Vec
    
    logger.info("Starting Word2Vec training...")
    logger.info(f"Parameters: dimensions={dim}, window={window}, epochs={epochs}")
    
    # Convert iterator to a list to allow multiple passes (required by gensim)
    # In a real streaming scenario, we might need to cache or re-stream
    try:
        sequences = list(sequence_iterator)
    except Exception as e:
        logger.error(f"Failed to materialize sequence iterator: {e}")
        raise
    
    model = Word2Vec(
        vector_size=dim,
        window=window,
        min_count=1,
        workers=4,
        epochs=epochs
    )
    
    # Build vocabulary
    model.build_vocab(sequences)
    
    # Train
    model.train(sequences, total_examples=model.corpus_count, epochs=model.epochs)
    
    logger.info("Word2Vec training complete.")
    return model

def aggregate_yearly_embeddings(model, df: pd.DataFrame) -> Dict[int, np.ndarray]:
    """
    Aggregate base track vectors by genre and year.

    Args:
        model: Trained Word2Vec model.
        df (pd.DataFrame): DataFrame with 'year' and 'genre' columns.

    Returns:
        Dict[int, np.ndarray]: Dictionary mapping years to aggregated vectors.

    Raises:
        ValueError: If required columns are missing.
    """
    if 'year' not in df.columns or 'genre' not in df.columns:
        raise ValueError("DataFrame must contain 'year' and 'genre' columns.")
    
    # Get model vectors
    vectors = model.wv
    
    year_genre_vectors = {}
    low_coverage_years = []
    
    # Group by year
    for year, group in df.groupby('year'):
        year = int(year)
        year_vectors = []
        
        for genre in group['genre'].dropna().unique():
            if genre in vectors:
                year_vectors.append(vectors[genre])
        
        if len(year_vectors) == 0:
            logger.warning(f"No vectors found for year {year}")
            continue
        
        # Check low coverage
        if len(year_vectors) < 1000: # Threshold from spec
            low_coverage_years.append(year)
            logger.warning(f"Year {year} has low coverage ({len(year_vectors)} tracks).")
        
        # Average vector for the year
        avg_vector = np.mean(year_vectors, axis=0)
        year_genre_vectors[year] = avg_vector
    
    # Save low coverage years
    if low_coverage_years:
        with open(DATA_DERIVED_DIR / "low_coverage_years.json", 'w') as f:
            json.dump(low_coverage_years, f)
        logger.info(f"Saved low coverage years to {DATA_DERIVED_DIR / 'low_coverage_years.json'}")
    
    # Save temp embeddings
    temp_path = DATA_DERIVED_DIR / "temp_embeddings.npz"
    np.savez(temp_path, **{str(k): v for k, v in year_genre_vectors.items()})
    logger.info(f"Saved temporary embeddings to {temp_path}")
    
    return year_genre_vectors

def save_yearly_embeddings(year_genre_vectors: Dict[int, np.ndarray]):
    """
    Save aggregated vectors to individual yearly files.

    Args:
        year_genre_vectors (Dict[int, np.ndarray]): Dictionary of year to vector.
    """
    for year, vector in year_genre_vectors.items():
        path = YEARLY_EMBEDDINGS_DIR / f"{year}.npy"
        np.save(path, vector)
        logger.info(f"Saved embedding for year {year} to {path}")

def main():
    """
    Main entry point for embeddings.
    """
    set_deterministic_seed(42)
    setup_embeddings_environment()
    
    try:
        # Load data
        df = pd.read_parquet(DATA_DERIVED_DIR / "metadata_mpd.parquet")
        
        # Generate sequences
        sequences = generate_track_sequences(df)
        
        # Train model
        model = train_global_word2vec(sequences)
        
        # Aggregate
        year_genre_vectors = aggregate_yearly_embeddings(model, df)
        
        # Save
        save_yearly_embeddings(year_genre_vectors)
        
        logger.info("Embeddings pipeline complete.")
        
    except Exception as e:
        logger.error(f"Embeddings pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
