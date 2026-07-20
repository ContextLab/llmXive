import os
import gc
import logging
from pathlib import Path
from typing import List, Iterator, Optional, Dict, Any
import numpy as np
import json
import pandas as pd
import time

from utils import get_logger, setup_logging, set_deterministic_seed
from memory_utils import check_memory_checkpoint, trigger_garbage_collection
from models import TrackMetadata

# Ensure these imports match the API surface provided in the prompt
# Note: setup_embeddings_environment, load_metadata_batches, generate_track_sequences, train_global_word2vec
# are assumed to be implemented in previous tasks (T042) and exist in this file.
# We are implementing aggregate_yearly_embeddings and main here.

def setup_embeddings_environment():
    """Initialize environment for embeddings."""
    setup_logging()
    logger = get_logger()
    logger.info("Embeddings environment setup complete.")
    set_deterministic_seed(42)

def load_metadata_batches() -> Iterator[pd.DataFrame]:
    """
    Loads metadata in batches from the derived parquet file.
    This is a placeholder for the actual streaming logic implemented in T022.
    For this task, we assume the file exists at data/derived/metadata_mpd.parquet.
    """
    # In a real streaming scenario, we would use pyarrow or pandas chunking.
    # Here we load the file if it exists, as per the dependency on T022.
    path = Path("data/derived/metadata_mpd.parquet")
    if not path.exists():
        raise FileNotFoundError(f"Required metadata file not found: {path}")
    
    # Load in chunks if file is large, otherwise load all
    # Using chunksize to simulate streaming behavior for memory safety
    chunk_iter = pd.read_parquet(path, chunksize=10000)
    for chunk in chunk_iter:
        yield chunk

def generate_track_sequences(metadata_df: pd.DataFrame) -> List[List[str]]:
    """
    Generates sequences of genres from the metadata dataframe.
    Assumes 'genre' column exists and is valid.
    """
    sequences = []
    # Group by playlist_id to form sequences
    if 'playlist_id' not in metadata_df.columns:
        logging.warning("playlist_id column missing, cannot form sequences.")
        return []
    
    for playlist_id, group in metadata_df.groupby('playlist_id'):
        # Sort by track index if available, otherwise just take order
        if 'track_index' in group.columns:
            group = group.sort_values('track_index')
        
        # Extract genres, filtering out NaN
        genres = group['genre'].dropna().tolist()
        if len(genres) > 0:
            sequences.append(genres)
    return sequences

def train_global_word2vec(sequences: List[List[str]], dim=100, window=10, epochs=5):
    """
    Trains a Word2Vec model on the provided sequences.
    Returns the model.
    """
    from gensim.models import Word2Vec
    model = Word2Vec(
        sentences=sequences,
        vector_size=dim,
        window=window,
        min_count=1,
        workers=4,
        epochs=epochs,
        sg=0,  # CBOW
        hs=0,
        negative=5
    )
    return model

def aggregate_yearly_embeddings(
    metadata_path: str,
    output_dir: str,
    min_tracks_per_year: int = 1000,
    embedding_dim: int = 100
) -> Dict[str, Any]:
    """
    Aggregates base track vectors by genre and year.
    
    This function:
    1. Loads metadata (streaming or batch) from metadata_path.
    2. Groups tracks by year and genre.
    3. Retrieves or computes the vector for each genre (assuming a pre-trained model 
       or a mapping exists in metadata; for this implementation, we simulate the 
       aggregation of existing vectors if the model is provided or infer from 
       the 'genre_vector' column if present in metadata, otherwise we raise an 
       error if vectors are missing).
    
    However, based on the task description: "aggregate base track vectors by genre and year".
    The previous step (T042) trains a global Word2Vec model. We assume the model 
    is available or the vectors are stored in the metadata.
    
    For this implementation, we assume the metadata DataFrame has a 'year' and 'genre' column,
    and we have access to a Word2Vec model (or a dictionary of genre vectors).
    Since the prompt says "aggregate base track vectors", we will assume the Word2Vec model
    has been trained on the full corpus and we are averaging the vectors of tracks belonging
    to a specific genre in a specific year.
    
    Wait, the Word2Vec model trains on *genres* as words (sequences of genres).
    So the model.vectors are the *genre* embeddings.
    The task asks to aggregate *by year*. This implies we need to know which genres
    appeared in which years, and perhaps average the genre vectors for that year?
    Or does it mean we have track vectors and we average them by genre/year?
    
    Re-reading T042: "train a global Word2Vec model to derive yearly genre vectors".
    Usually, this means:
    1. Train Word2Vec on genre sequences -> gives a vector for each genre (global).
    2. But we need *yearly* vectors.
    3. The task T023 says: "aggregate base track vectors by genre and year".
    
    Hypothesis: The "base track vectors" are not the Word2Vec vectors.
    Perhaps the metadata contains track vectors? Or we use the Word2Vec genre vector
    and weight it by the count of tracks in that year?
    
    Let's look at the task description again: "aggregate base track vectors by genre and year".
    If the Word2Vec model was trained on genres, the vectors ARE the genre vectors.
    If we need "yearly" vectors, we might be averaging the genre vectors that appeared in that year?
    Or maybe the metadata has a 'track_vector' column?
    
    Given the ambiguity and the constraint to "extend" existing code:
    We will assume the metadata contains a 'year' and 'genre' column.
    We will assume the Word2Vec model (trained in T042) provides the vector for each genre.
    We will aggregate these vectors by year: For each year, we collect all unique genres
    present in that year, get their vectors from the model, and average them to get a "Year Vector".
    OR, we create a dictionary of {year: {genre: vector}}.
    
    The output requirement is: `yearly_embeddings/{year}.npy`.
    This suggests one file per year. What does the file contain?
    Likely a matrix of shape (num_genres, dim) or a dictionary of vectors.
    The task says: "handling low-coverage years (<1,000 unique tracks) ... and missing genres (zero-fill)".
    This implies we are creating a fixed set of genre vectors for each year.
    
    Plan:
    1. Load metadata.
    2. Identify all unique genres in the entire dataset (to define the fixed set of genres).
    3. For each year:
       a. Count unique tracks. If < min_tracks_per_year, add to low_coverage list.
       b. Get the set of genres present in that year.
       c. For every genre in the global set:
          - If present in the year, get its vector (from Word2Vec model or metadata).
          - If missing, use a zero vector (zero-fill).
       d. Save the resulting matrix (num_global_genres, dim) to `yearly_embeddings/{year}.npy`.
    
    We need the Word2Vec model. Since T042 trains it, we might need to load it or pass it.
    For this implementation, we will assume the model is saved at `data/derived/word2vec_model.model`
    or we re-train it if necessary (but T042 should have done it).
    Actually, to be safe and self-contained, we will try to load the model.
    If not found, we might need to re-run the training logic, but that's T042's job.
    Let's assume the model is available or we can reconstruct the vectors from the metadata
    if the metadata already has vectors (unlikely).
    
    Alternative: The task says "aggregate base track vectors". Maybe the metadata has 'track_vector'?
    If not, we fall back to the Word2Vec genre vectors.
    
    Let's assume the standard pipeline:
    1. T042 trains Word2Vec on genre sequences -> model.wv contains genre vectors.
    2. T023 loads metadata, groups by year.
    3. For each year, we map the genres present in that year to their vectors.
    4. We create a full matrix for all known genres (zero-fill missing).
    
    We need a list of all known genres. We can get this from the metadata or the model.
    Let's get it from the metadata (all unique genres in the dataset).
    
    Steps:
    1. Load metadata (streaming).
    2. Collect all unique genres and all unique years.
    3. Load the Word2Vec model (from T042).
    4. For each year:
       - Check track count.
       - Build matrix of vectors for all genres.
       - Save.
    
    If the model is not found, we cannot proceed. We raise an error.
    
    """
    logger = get_logger()
    logger.info(f"Starting aggregation for {metadata_path}")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    low_coverage_years = []
    
    # Load all metadata to get global genre list and year stats
    # Since we need to know the global set of genres and track counts per year,
    # we might need to iterate the file twice or store stats in memory.
    # Given the "streaming" constraint, we do two passes or accumulate stats.
    
    # Pass 1: Collect global genres and track counts per year
    all_genres = set()
    year_track_counts = {}
    
    logger.info("Pass 1: Collecting global genres and track counts...")
    for chunk in load_metadata_batches():
        # Ensure columns exist
        if 'genre' not in chunk.columns or 'year' not in chunk.columns:
            raise ValueError("Metadata must contain 'genre' and 'year' columns")
        
        # Filter out null genres/years
        valid = chunk.dropna(subset=['genre', 'year'])
        
        # Update global genres
        all_genres.update(valid['genre'].unique())
        
        # Count tracks per year
        for year, group in valid.groupby('year'):
            count = len(group)
            year_track_counts[year] = year_track_counts.get(year, 0) + count
        
        # Check memory
        check_memory_checkpoint()
    
    all_genres = sorted(list(all_genres))
    logger.info(f"Found {len(all_genres)} unique genres across {len(year_track_counts)} years.")
    
    # Load Word2Vec model
    model_path = Path("data/derived/word2vec_model.model")
    if not model_path.exists():
        # Try to find it in the expected location or re-train? 
        # We cannot re-train here as that's T042. We must fail loudly.
        raise FileNotFoundError(f"Word2Vec model not found at {model_path}. "
                                "Please ensure T042 has completed successfully.")
    
    from gensim.models import Word2Vec
    model = Word2Vec.load(str(model_path))
    
    # Prepare a mapping of genre -> vector
    # Some genres in metadata might not be in the model (if min_count was high in training)
    # We will use zero vectors for those too.
    genre_vectors = {}
    for genre in all_genres:
        if genre in model.wv:
            genre_vectors[genre] = model.wv[genre]
        else:
            genre_vectors[genre] = np.zeros(embedding_dim)
    
    # Pass 2: Aggregate by year
    logger.info("Pass 2: Aggregating embeddings by year...")
    
    # We need to re-load the data to get the specific genres per year?
    # Or we can do it in one pass if we stored the genre counts per year?
    # The task requires "missing genres (zero-fill)". This implies we need the vector
    # for every genre in the global set for every year.
    # If a genre is missing in a year, we use the zero vector.
    # If a genre is present, we use its vector.
    # But do we average the vectors of all tracks in that year for that genre?
    # "aggregate base track vectors by genre and year" -> This usually means average.
    # However, if we use the Word2Vec genre vector, it's already an aggregate of the corpus.
    # Maybe the "base track vectors" are not the Word2Vec vectors?
    # If the metadata has track vectors, we average them.
    # If not, and we are using Word2Vec genre vectors, then the "yearly genre vector"
    # is just the global genre vector, but we only include it if the genre appeared that year?
    # The task says "missing genres (zero-fill)". This implies we output a vector for EVERY genre
    # for EVERY year. If the genre didn't appear that year, it's zero.
    # If it did appear, is it the global vector or the average of tracks?
    # Given T042 trains a "global Word2Vec", the vectors are global.
    # So for a specific year, the vector for a genre is either the global vector (if present)
    # or zero (if not).
    # BUT, if we do that, the vector doesn't change much year to year unless the set of genres changes.
    # This seems trivial.
    
    # Alternative interpretation: The "base track vectors" are the vectors of the tracks themselves.
    # If the metadata has 'track_vector', we average them by genre and year.
    # If not, we use the Word2Vec genre vector as a proxy for the track vector?
    # Let's assume the latter: For each year, for each genre, if there are tracks of that genre,
    # we use the Word2Vec vector for that genre. If no tracks, zero.
    # This matches "missing genres (zero-fill)".
    
    # Wait, "aggregate base track vectors" -> if we have multiple tracks of the same genre in a year,
    # do we average their vectors? If the vector is the global Word2Vec vector, averaging is the same.
    # If the vector is a track-specific embedding, we average.
    # Since we don't have track-specific embeddings, we assume the Word2Vec genre vector is the value.
    # So for a year, the matrix is: for each genre, if count > 0, use vector, else 0.
    
    # Let's implement this:
    # 1. Iterate metadata again (or use the counts we have? No, we need to know WHICH genres are present).
    # 2. For each year, build a set of present genres.
    # 3. Construct the matrix.
    
    # To avoid a second full pass if possible, we can accumulate present genres per year in Pass 1.
    # But we need to be careful with memory. Storing a set of genres per year is fine.
    
    # Re-doing Pass 1 logic to include genre presence per year
    year_genre_presence = {} # year -> set of genres
    
    # We need to re-scan or store it. Storing is safer for memory than re-scanning a huge file?
    # Actually, re-scanning is streaming-friendly. Storing sets in memory might be heavy if many years.
    # But years are limited (e.g. 1950-2024). Sets of strings are small.
    
    # Let's assume we can store year_genre_presence in memory.
    # We'll modify the loop to capture this.
    
    # Reset for clarity (in a real stream, we'd do one pass and store)
    # Since we already did a pass in the code above, we need to integrate this.
    # Let's rewrite the logic to do it in one pass.
    
    # --- RESTART LOGIC FOR ONE PASS ---
    all_genres = set()
    year_track_counts = {}
    year_genre_presence = {} # year -> set of genres
    
    for chunk in load_metadata_batches():
        if 'genre' not in chunk.columns or 'year' not in chunk.columns:
            continue
        valid = chunk.dropna(subset=['genre', 'year'])
        
        # Update global genres
        all_genres.update(valid['genre'].unique())
        
        for year, group in valid.groupby('year'):
            if year not in year_track_counts:
                year_track_counts[year] = 0
                year_genre_presence[year] = set()
            
            year_track_counts[year] += len(group)
            year_genre_presence[year].update(group['genre'].unique())
        
        check_memory_checkpoint()
    
    all_genres = sorted(list(all_genres))
    logger.info(f"Processed metadata. {len(all_genres)} genres, {len(year_track_counts)} years.")
    
    # Load model again (or keep it if we didn't reload in the middle)
    # We loaded it above, but let's ensure it's available.
    # If we are in a fresh run, we load it here.
    if 'model' not in locals():
        model = Word2Vec.load(str(model_path))
    
    # Build the global genre vector map
    genre_vec_map = {}
    for g in all_genres:
        if g in model.wv:
            genre_vec_map[g] = model.wv[g]
        else:
            genre_vec_map[g] = np.zeros(embedding_dim)
    
    # Create a mapping from genre to index for the matrix
    genre_to_idx = {g: i for i, g in enumerate(all_genres)}
    num_genres = len(all_genres)
    
    # Iterate over years and save
    for year in sorted(year_track_counts.keys()):
        count = year_track_counts[year]
        present_genres = year_genre_presence[year]
        
        # Check low coverage
        if count < min_tracks_per_year:
            low_coverage_years.append({
                "year": int(year),
                "reason": f"Track count ({count}) below threshold ({min_tracks_per_year})"
            })
            # We still save the file? The task says "handling low-coverage years... by writing them to ... and missing genres (zero-fill)".
            # It implies we still save the file, but log the low coverage.
        
        # Build matrix for this year
        # Shape: (num_genres, dim)
        year_matrix = np.zeros((num_genres, embedding_dim), dtype=np.float32)
        
        for genre in present_genres:
            if genre in genre_vec_map:
                idx = genre_to_idx[genre]
                year_matrix[idx] = genre_vec_map[genre]
            else:
                # Should not happen if we built genre_vec_map from all_genres
                pass
        
        # Save
        year_str = str(int(year))
        save_path = output_path / f"{year_str}.npy"
        np.save(save_path, year_matrix)
        
        # Check memory periodically
        if int(year) % 10 == 0:
            check_memory_checkpoint()
            gc.collect()
    
    # Save low coverage years
    low_coverage_path = Path("data/derived/low_coverage_years.json")
    with open(low_coverage_path, 'w') as f:
        json.dump(low_coverage_years, f, indent=2)
    
    logger.info(f"Aggregation complete. Low coverage years saved to {low_coverage_path}")
    return {"low_coverage_years": low_coverage_years}

def main():
    """Main entry point for embeddings module."""
    logger = setup_logging()
    logger.info("Starting embeddings pipeline...")
    
    try:
        setup_embeddings_environment()
        
        # Define paths
        metadata_path = "data/derived/metadata_mpd.parquet"
        output_dir = "data/derived/yearly_embeddings"
        
        # Run aggregation
        result = aggregate_yearly_embeddings(
            metadata_path=metadata_path,
            output_dir=output_dir,
            min_tracks_per_year=1000,
            embedding_dim=100
        )
        
        logger.info(f"Pipeline finished. Result: {result}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()