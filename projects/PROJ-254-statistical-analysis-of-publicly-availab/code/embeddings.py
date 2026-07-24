"""
Embeddings module for training Word2Vec models and aggregating yearly genre embeddings.

This module handles the generation of track sequences, training of the global Word2Vec model,
aggregation of embeddings by year and genre, and saving of the resulting vectors.

It is designed to work with streaming data to handle large datasets efficiently.
"""
import os
import gc
import logging
from pathlib import Path
from typing import List, Iterator, Optional, Dict, Any
import json
import yaml
import numpy as np
import pandas as pd
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence

# Import from utils
from utils import setup_logging, get_logger, set_deterministic_seed
from memory_utils import check_memory_checkpoint, trigger_garbage_collection

# Setup logging
logger = get_logger(__name__)

def setup_embeddings_environment(config_path: str = "config/embeddings.yaml") -> Dict[str, Any]:
    """
    Setup the embeddings environment by loading configuration and initializing logging.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Dictionary containing the loaded configuration.
    """
    setup_logging()
    logger.info("Setting up embeddings environment...")

    if not os.path.exists(config_path):
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        config = {
            'word2vec': {
                'algorithm': 'skip-gram',
                'dimensions': 100,
                'window': 10,
                'epochs': 5,
                'min_count': 5,
                'workers': 2,
                'vector_size': 100,
                'sg': 1,
                'hs': 0,
                'negative': 5,
                'sample': 0.001,
                'alpha': 0.025,
                'min_alpha': 0.0001,
                'epochs_passes': 5
            },
            'paths': {
                'metadata_file': 'data/derived/metadata_mpd.parquet',
                'output_dir': 'yearly_embeddings',
                'temp_embeddings': 'data/derived/temp_embeddings.npz',
                'flagged_years_file': 'data/derived/flagged_low_coverage_years.json'
            },
            'logging': {
                'level': 'INFO',
                'file': 'pipeline_log.txt'
            }
        }
    else:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

    # Ensure output directory exists
    output_dir = Path(config['paths']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set deterministic seed
    set_deterministic_seed(42)

    logger.info(f"Embeddings environment setup complete. Config: {config['word2vec']}")
    return config

def load_metadata_batches(metadata_path: str, batch_size: int = 1000) -> Iterator[pd.DataFrame]:
    """
    Load metadata in batches from a Parquet file to manage memory.

    Args:
        metadata_path: Path to the metadata Parquet file.
        batch_size: Number of rows to load per batch.

    Yields:
        DataFrame containing a batch of metadata.
    """
    logger.info(f"Loading metadata from {metadata_path} in batches of {batch_size}...")
    
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    # Read in chunks
    for chunk in pd.read_parquet(metadata_path, engine='pyarrow', chunksize=batch_size):
        check_memory_checkpoint(threshold_gb=6.0)
        yield chunk
        
        # Force garbage collection if memory is high
        if check_memory_checkpoint(threshold_gb=6.0, verbose=False):
            trigger_garbage_collection()

def generate_track_sequences(metadata_path: str, batch_size: int = 1000) -> Iterator[List[List[str]]]:
    """
    Generate track sequences (lists of track IDs) from metadata, ready for Word2Vec.

    This function yields sequences of track IDs grouped by playlist, in playlist order.
    It processes the metadata in batches to handle large datasets.

    Args:
        metadata_path: Path to the metadata Parquet file.
        batch_size: Number of rows to load per batch.

    Yields:
        Iterator of lists of track IDs (sequences).
    """
    logger.info("Generating track sequences from metadata...")
    
    current_playlist = None
    current_sequence = []
    sequences_buffer = []
    buffer_threshold = 1000  # Yield after collecting this many sequences

    for batch in load_metadata_batches(metadata_path, batch_size):
        # Sort by playlist_id and track_index to ensure correct order
        batch = batch.sort_values(['playlist_id', 'track_index'])
        
        for _, row in batch.iterrows():
            playlist_id = row['playlist_id']
            track_id = str(row['track_id'])
            
            if current_playlist is None:
                current_playlist = playlist_id
                current_sequence = [track_id]
            elif playlist_id == current_playlist:
                current_sequence.append(track_id)
            else:
                # New playlist, yield the old one
                if len(current_sequence) > 1:
                    sequences_buffer.append(current_sequence)
                    if len(sequences_buffer) >= buffer_threshold:
                        yield sequences_buffer
                        sequences_buffer = []
                current_playlist = playlist_id
                current_sequence = [track_id]
        
        # Yield any remaining sequences in the buffer
        if sequences_buffer:
            yield sequences_buffer
            sequences_buffer = []

    # Yield the last sequence if it exists
    if current_sequence and len(current_sequence) > 1:
        sequences_buffer.append(current_sequence)
        if sequences_buffer:
            yield sequences_buffer

    logger.info("Track sequence generation complete.")

def train_global_word2vec(config: Dict[str, Any], sequences_iterator: Iterator[Any]) -> Word2Vec:
    """
    Train a global Word2Vec model on track sequences.

    This function trains a Word2Vec model using the skip-gram algorithm with parameters
    loaded from the configuration file. It is optimized for memory efficiency on CI runners.

    Args:
        config: Configuration dictionary containing Word2Vec parameters.
        sequences_iterator: Iterator yielding lists of track IDs (sequences).

    Returns:
        Trained Word2Vec model.

    Raises:
        RuntimeError: If training fails or data is insufficient.
    """
    logger.info("Starting Word2Vec training...")
    
    # Extract parameters from config
    w2v_config = config['word2vec']
    dimensions = w2v_config.get('dimensions', 100)
    window = w2v_config.get('window', 10)
    epochs = w2v_config.get('epochs', 5)
    min_count = w2v_config.get('min_count', 5)
    workers = w2v_config.get('workers', 2)  # Optimized for 2-core runners
    vector_size = w2v_config.get('vector_size', dimensions)
    sg = w2v_config.get('sg', 1)
    hs = w2v_config.get('hs', 0)
    negative = w2v_config.get('negative', 5)
    sample = w2v_config.get('sample', 0.001)
    alpha = w2v_config.get('alpha', 0.025)
    min_alpha = w2v_config.get('min_alpha', 0.0001)
    
    logger.info(f"Parameters: dimensions={dimensions}, window={window}, epochs={epochs}, "
               f"workers={workers}, min_count={min_count}")

    # Convert iterator to a re-iterable list for multiple passes
    # Word2Vec requires multiple passes over the data, so we cannot use a generator directly
    logger.info("Loading sequences into memory for multiple passes (optimized for 2 workers)...")
    all_sequences = []
    total_seqs = 0
    total_tokens = 0
    
    for batch in sequences_iterator:
        all_sequences.extend(batch)
        total_seqs += len(batch)
        total_tokens += sum(len(seq) for seq in batch)
        
        # Log progress
        if total_seqs % 10000 == 0:
            logger.info(f"Loaded {total_seqs} sequences ({total_tokens} tokens so far)...")
            check_memory_checkpoint(threshold_gb=6.0)
    
    logger.info(f"Total sequences loaded: {total_seqs}, total tokens: {total_tokens}")
    
    if total_seqs == 0:
        raise RuntimeError("No sequences found for training. Check input data.")

    # Train the model
    logger.info("Training Word2Vec model...")
    try:
        model = Word2Vec(
            sentences=all_sequences,
            vector_size=vector_size,
            window=window,
            min_count=min_count,
            workers=workers,  # Optimized for 2-core runner
            sg=sg,
            hs=hs,
            negative=negative,
            sample=sample,
            alpha=alpha,
            min_alpha=min_alpha,
            epochs=epochs,
            compute_loss=True,
            seed=42
        )
        
        # Explicitly call train to ensure all passes are done
        model.train(
            all_sequences,
            total_examples=len(all_sequences),
            epochs=epochs
        )
        
        logger.info("Word2Vec training complete.")
        return model
        
    except Exception as e:
        logger.error(f"Error during training: {str(e)}")
        raise RuntimeError(f"Failed to train Word2Vec model: {str(e)}")

def aggregate_yearly_embeddings(
    model: Word2Vec,
    metadata_path: str,
    output_path: str,
    config: Dict[str, Any]
) -> List[int]:
    """
    Aggregate track embeddings by genre and year.

    This function computes the mean embedding for each genre in each year
    by averaging the embeddings of all tracks belonging to that genre-year pair.

    Args:
        model: Trained Word2Vec model.
        metadata_path: Path to the metadata Parquet file.
        output_path: Path to save the temporary aggregated embeddings.
        config: Configuration dictionary.

    Returns:
        List of years flagged for low coverage (< 100 unique tracks).
    """
    logger.info("Aggregating yearly embeddings by genre...")
    
    # Load metadata
    logger.info(f"Loading metadata from {metadata_path}...")
    df = pd.read_parquet(metadata_path, engine='pyarrow')
    
    # Filter tracks with valid years and genre tags
    df = df[df['release_year'].notna()]
    df = df[df['genre_tag'].notna()]
    df = df[df['genre_tag'] != '']
    
    logger.info(f"Processing {len(df)} tracks with valid years and genres...")
    
    # Group by year and genre
    yearly_genre_embeddings = {}
    low_coverage_years = []
    
    # Get unique years
    unique_years = sorted(df['release_year'].unique())
    logger.info(f"Found {len(unique_years)} unique years: {unique_years[:10]}...")
    
    for year in unique_years:
        year_df = df[df['release_year'] == year]
        unique_tracks = year_df['track_id'].nunique()
        
        if unique_tracks < 100:
            low_coverage_years.append(int(year))
            logger.warning(f"Year {year} has low coverage: {unique_tracks} tracks (< 100). Flagged.")
        
        # Group by genre within the year
        for genre, genre_df in year_df.groupby('genre_tag'):
            # Get track IDs for this genre-year
            track_ids = genre_df['track_id'].unique()
            
            # Get embeddings for these tracks
            embeddings = []
            for track_id in track_ids:
                try:
                    track_str = str(track_id)
                    if track_str in model.wv:
                        embeddings.append(model.wv[track_str])
                except Exception as e:
                    # Track not in vocabulary
                    pass
            
            if embeddings:
                # Mean embedding for this genre-year
                mean_embedding = np.mean(embeddings, axis=0)
                key = (int(year), genre)
                yearly_genre_embeddings[key] = mean_embedding
    
    # Save aggregated embeddings
    logger.info(f"Saving aggregated embeddings to {output_path}...")
    np.savez(output_path, embeddings=yearly_genre_embeddings)
    
    logger.info(f"Aggregation complete. Flagged {len(low_coverage_years)} low-coverage years.")
    return low_coverage_years

def save_yearly_embeddings(
    config: Dict[str, Any],
    flagged_years: Optional[List[int]] = None
) -> None:
    """
    Save yearly genre embeddings to individual NumPy files.

    This function loads the aggregated embeddings and saves each year's
    genre embeddings to a separate .npy file in the output directory.

    Args:
        config: Configuration dictionary.
        flagged_years: Optional list of flagged low-coverage years.
    """
    logger.info("Saving yearly embeddings...")
    
    temp_path = config['paths']['temp_embeddings']
    output_dir = Path(config['paths']['output_dir'])
    flagged_years_file = config['paths']['flagged_years_file']
    
    if not os.path.exists(temp_path):
        raise FileNotFoundError(f"Temp embeddings file not found: {temp_path}")
    
    # Load aggregated embeddings
    data = np.load(temp_path, allow_pickle=True)
    embeddings_dict = data['embeddings'].item()
    
    # Group by year
    yearly_embeddings = {}
    for (year, genre), embedding in embeddings_dict.items():
        if year not in yearly_embeddings:
            yearly_embeddings[year] = {}
        yearly_embeddings[year][genre] = embedding
    
    # Save each year's embeddings
    for year, genre_embeddings in yearly_embeddings.items():
        output_path = output_dir / f"{year}.npy"
        
        # Convert to numpy array
        # Structure: array of (genre_name, embedding_vector) tuples
        # Or a dictionary saved as object array
        embedding_array = np.array(
            [(genre, emb) for genre, emb in genre_embeddings.items()],
            dtype=object
        )
        
        np.save(output_path, embedding_array)
        logger.debug(f"Saved embeddings for year {year} to {output_path}")
    
    # Save flagged years if provided
    if flagged_years is not None:
        with open(flagged_years_file, 'w') as f:
            json.dump(flagged_years, f)
        logger.info(f"Saved flagged years to {flagged_years_file}")
    
    logger.info("Yearly embeddings saved successfully.")

def main() -> None:
    """
    Main entry point for the embeddings pipeline.

    This function orchestrates the full embeddings workflow:
    1. Setup environment and load configuration
    2. Generate track sequences from metadata
    3. Train Word2Vec model
    4. Aggregate embeddings by year and genre
    5. Save yearly embeddings
    """
    logger.info("Starting embeddings pipeline...")
    
    try:
        # Setup environment
        config = setup_embeddings_environment()
        
        # Generate track sequences
        sequences_iterator = generate_track_sequences(
            config['paths']['metadata_file']
        )
        
        # Train Word2Vec model
        model = train_global_word2vec(config, sequences_iterator)
        
        # Aggregate embeddings
        flagged_years = aggregate_yearly_embeddings(
            model,
            config['paths']['metadata_file'],
            config['paths']['temp_embeddings'],
            config
        )
        
        # Save yearly embeddings
        save_yearly_embeddings(config, flagged_years)
        
        logger.info("Embeddings pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()