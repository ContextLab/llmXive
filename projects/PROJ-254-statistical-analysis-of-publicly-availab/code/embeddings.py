import os
import gc
import logging
from pathlib import Path
from typing import List, Iterator, Optional, Dict, Any
import numpy as np
import pandas as pd
from gensim.models import Word2Vec

from utils import get_logger, setup_logging, set_deterministic_seed
from memory_utils import check_memory_checkpoint, trigger_garbage_collection, get_memory_percent
from models import YearlyGenreEmbedding

# Ensure deterministic behavior
set_deterministic_seed(42)
setup_logging()
logger = get_logger()

# Configuration
EMBEDDING_DIM = 100
MIN_COUNT = 5
WINDOW = 10
EPOCHS = 5
LOW_COVERAGE_THRESHOLD = 1000
MISSING_GENRE_FILL_VALUE = 0.0

def setup_embeddings_environment():
    """Initialize the environment for embedding generation."""
    logger.info("Setting up embeddings environment...")
    output_dir = Path("data/derived/yearly_embeddings")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def load_metadata_batches(batch_size: int = 50000) -> Iterator[pd.DataFrame]:
    """
    Load metadata in batches from the derived parquet file.
    Yields DataFrames containing track metadata (track_id, year, genre, vector_path).
    """
    metadata_path = Path("data/derived/metadata_mpd.parquet")
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}. Run ingest pipeline first.")
    
    logger.info(f"Loading metadata batches from {metadata_path}...")
    for chunk in pd.read_parquet(metadata_path, chunksize=batch_size):
        check_memory_checkpoint()
        yield chunk

def generate_track_sequences() -> Iterator[List[str]]:
    """
    Generate track sequences (playlists) from metadata.
    Yields lists of track_ids representing a single playlist sequence.
    """
    metadata_path = Path("data/derived/metadata_mpd.parquet")
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}. Run ingest pipeline first.")

    # Assuming the parquet has a playlist_id column to group tracks
    # If not, we might need to load the raw MPD data again or assume a different structure.
    # Based on typical MPD structure, we group by playlist_id.
    try:
        df = pd.read_parquet(metadata_path)
        # Ensure we have necessary columns
        required_cols = ['playlist_id', 'track_id']
        if not all(col in df.columns for col in required_cols):
            # Fallback or error handling if columns are missing
            logger.warning("Expected columns not found in metadata. Attempting to load raw MPD structure or using track_id as sequence.")
            # If playlist_id is missing, we can't generate sequences properly.
            # For this implementation, we assume the data model includes playlist_id.
            raise ValueError("Missing 'playlist_id' column in metadata for sequence generation.")

        # Group by playlist_id and yield track lists
        for _, group in df.groupby('playlist_id'):
            check_memory_checkpoint()
            yield group['track_id'].tolist()
    except Exception as e:
        logger.error(f"Error generating track sequences: {e}")
        raise

def train_global_word2vec(output_path: Optional[Path] = None) -> Word2Vec:
    """
    Train a global Word2Vec model on track sequences.
    Produces base track vectors.
    """
    logger.info("Training global Word2Vec model...")
    sequences = list(generate_track_sequences())
    
    if not sequences:
        raise ValueError("No track sequences found to train the model.")

    # Train model
    model = Word2Vec(
        sentences=sequences,
        vector_size=EMBEDDING_DIM,
        window=WINDOW,
        min_count=MIN_COUNT,
        workers=4,
        epochs=EPOCHS,
        sg=0,  # CBOW
        hs=0,  # Negative sampling
        negative=5
    )
    
    # Save model if path provided
    if output_path:
        model.save(str(output_path))
        logger.info(f"Word2Vec model saved to {output_path}")
    
    # Check memory usage
    check_memory_checkpoint()
    trigger_garbage_collection()
    
    return model

def aggregate_yearly_embeddings(model: Word2Vec, metadata_path: Optional[Path] = None) -> Dict[int, Dict[str, np.ndarray]]:
    """
    Aggregate base track vectors by genre and year.
    
    - Loads metadata to map track_id -> (year, genre).
    - Aggregates vectors for each (year, genre) pair (mean pooling).
    - Handles low-coverage years (<1,000 unique tracks) by flagging them in the result dict.
    - Handles missing genres by zero-filling vectors for genres not present in a given year.
    - Saves results to `data/derived/yearly_embeddings/{year}.npy`.
    
    Returns a dictionary: {year: {genre: vector_array}}
    """
    logger.info("Aggregating yearly embeddings...")
    
    if metadata_path is None:
        metadata_path = Path("data/derived/metadata_mpd.parquet")
    
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}. Run ingest pipeline first.")
    
    # Load full metadata (might be large, but we need to group by year/genre)
    # In a memory-constrained environment, we might need to stream this, 
    # but for grouping, loading once is often necessary unless we do two passes.
    # Given the 6GB limit, we rely on the memory monitoring functions.
    df = pd.read_parquet(metadata_path)
    
    # Ensure required columns exist
    required_cols = ['track_id', 'year', 'genre']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in metadata.")
    
    # Filter out tracks without a vector in the model (min_count filtering in Word2Vec)
    valid_track_ids = set(model.wv.index_to_key)
    df = df[df['track_id'].isin(valid_track_ids)]
    
    # Group by year and genre
    yearly_genre_data = {}
    low_coverage_years = set()
    missing_genre_warnings = []
    
    # Get all unique years
    unique_years = df['year'].dropna().astype(int).unique()
    
    for year in sorted(unique_years):
        check_memory_checkpoint()
        year_df = df[df['year'] == year]
        
        # Count unique tracks for this year
        unique_tracks_count = year_df['track_id'].nunique()
        
        # Flag low coverage years
        if unique_tracks_count < LOW_COVERAGE_THRESHOLD:
            low_coverage_years.add(year)
            logger.warning(f"Year {year} has low coverage: {unique_tracks_count} unique tracks (< {LOW_COVERAGE_THRESHOLD}). Flagged but not excluded.")
        
        # Group by genre for this year
        year_genre_vectors = {}
        genre_counts = {}
        
        for genre, group in year_df.groupby('genre'):
            # Skip NaN genres
            if pd.isna(genre):
                continue
            
            track_ids = group['track_id'].tolist()
            vectors = []
            
            for tid in track_ids:
                try:
                    vectors.append(model.wv[tid])
                except KeyError:
                    # Should not happen due to earlier filtering, but safety check
                    continue
            
            if vectors:
                # Mean pooling
                mean_vector = np.mean(vectors, axis=0)
                year_genre_vectors[genre] = mean_vector
                genre_counts[genre] = len(track_ids)
            else:
                # Zero-fill for genres with no valid tracks in this year (though groupby handles this)
                # This case is technically unreachable if groupby yielded a group, but for safety:
                year_genre_vectors[genre] = np.zeros(EMBEDDING_DIM)
                genre_counts[genre] = 0
        
        # Identify all genres that appeared in ANY year to ensure consistent shape?
        # The task says "missing genres (zero-fill)". This implies we need a fixed set of genres per year.
        # However, without a global genre list, we can only zero-fill genres that appeared in *other* years but not this one.
        # Let's collect all genres seen across all years first.
        
        yearly_genre_data[year] = {
            'vectors': year_genre_vectors,
            'counts': genre_counts,
            'unique_tracks': unique_tracks_count,
            'is_low_coverage': year in low_coverage_years
        }
    
    # Second pass: ensure consistent genre set across years for zero-filling
    all_genres = set()
    for year_data in yearly_genre_data.values():
        all_genres.update(year_data['vectors'].keys())
    
    final_yearly_data = {}
    for year, data in yearly_genre_data.items():
        final_vectors = {}
        for genre in all_genres:
            if genre in data['vectors']:
                final_vectors[genre] = data['vectors'][genre]
            else:
                # Zero-fill
                final_vectors[genre] = np.zeros(EMBEDDING_DIM)
                missing_genre_warnings.append(f"Year {year}, Genre '{genre}': Zero-filled (no tracks).")
        
        final_yearly_data[year] = final_vectors
        
        # Save to disk
        output_dir = Path("data/derived/yearly_embeddings")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{year}.npy"
        
        # Create a structured array or just a dict of vectors? 
        # Numpy .npy can save a dict if pickled, but usually we want a matrix.
        # To be safe and standard, we'll save a dict of {genre: vector}.
        # Alternatively, we can save a 2D array if we order genres.
        # Let's save the dict to preserve genre labels.
        np.save(str(output_file), final_vectors)
        logger.info(f"Saved embeddings for year {year} to {output_file}")
    
    if missing_genre_warnings:
        logger.warning(f"Total missing genre instances logged: {len(missing_genre_warnings)}")
    
    logger.info("Yearly embedding aggregation complete.")
    return final_yearly_data

def main():
    """Main entry point for the embeddings pipeline."""
    try:
        # 1. Setup
        output_dir = setup_embeddings_environment()
        
        # 2. Train Global Model (if not already done)
        # In a real pipeline, we might check if the model exists.
        # For this task, we assume we are running the full pipeline or the model is provided.
        # Since T013 is the training step, we assume the model is available or we train it here.
        # To be safe and self-contained for this task execution:
        model_path = Path("data/derived/global_word2vec.model")
        if not model_path.exists():
            logger.info("Global model not found. Training now...")
            model = train_global_word2vec(model_path)
        else:
            logger.info("Loading existing global Word2Vec model...")
            model = Word2Vec.load(str(model_path))
        
        # 3. Aggregate Yearly Embeddings
        aggregate_yearly_embeddings(model)
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()