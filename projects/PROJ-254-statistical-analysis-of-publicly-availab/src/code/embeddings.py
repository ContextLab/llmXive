import os
import gc
import logging
from pathlib import Path
from typing import List, Iterator, Optional, Dict, Any
import numpy as np

try:
    import gensim
    from gensim.models import Word2Vec
    GENSIM_AVAILABLE = True
except ImportError:
    GENSIM_AVAILABLE = False
    logging.warning("gensim not installed. Embedding functions will fail.")

from utils import get_logger, setup_logging, set_deterministic_seed
from memory_utils import monitor_and_maybe_gc, enforce_memory_limit, get_memory_usage_gb

def load_metadata_batches(batch_size: int = 100000) -> Iterator[List[Dict[str, Any]]]:
    """
    Load metadata from parquet files in batches to manage memory.

    Args:
        batch_size: Number of rows to load per batch.

    Yields:
        List of track metadata dictionaries.
    """
    metadata_path = Path("data/derived/metadata_mpd.parquet")
    if not metadata_path.exists():
        logger = get_logger()
        logger.error(f"Metadata file not found: {metadata_path}")
        return

    import pandas as pd
    logger = get_logger()
    logger.info(f"Loading metadata from {metadata_path} in batches of {batch_size}")

    for chunk in pd.read_parquet(metadata_path, chunksize=batch_size):
        batch = chunk.to_dict('records')
        yield batch
        monitor_and_maybe_gc()

def generate_track_sequences(batches: List[List[Dict[str, Any]]]) -> Iterator[List[str]]:
    """
    Generate track ID sequences from playlist data.

    Args:
        batches: List of batch data containing playlist information.

    Yields:
        List of track IDs representing a playlist sequence.
    """
    for batch in batches:
        for record in batch:
            if 'track_ids' in record and record['track_ids']:
                yield record['track_ids']
            monitor_and_maybe_gc()

def train_global_word2vec(
    output_path: str = "data/derived/word2vec_model.bin",
    dimensions: int = 100,
    window: int = 10,
    epochs: int = 5,
    min_count: int = 5,
    workers: int = 4
) -> Optional[Any]:
    """
    Train a global Word2Vec model on track sequences.

    Args:
        output_path: Path to save the trained model.
        dimensions: Dimensionality of embeddings.
        window: Context window size.
        epochs: Number of training epochs.
        min_count: Minimum word count.
        workers: Number of worker threads.

    Returns:
        Trained Word2Vec model or None if training failed.
    """
    if not GENSIM_AVAILABLE:
        logger = get_logger()
        logger.error("gensim is not installed. Cannot train Word2Vec model.")
        return None

    logger = get_logger()
    logger.info("Starting Word2Vec training...")
    logger.info(f"Parameters: dimensions={dimensions}, window={window}, epochs={epochs}")

    try:
        # Create generator for sequences
        def sequence_generator():
            for batch in load_metadata_batches():
                for sequence in generate_track_sequences([batch]):
                    yield sequence
                    monitor_and_maybe_gc()

        # Train model
        model = Word2Vec(
            sentences=sequence_generator(),
            vector_size=dimensions,
            window=window,
            min_count=min_count,
            workers=workers,
            epochs=epochs,
            sg=0,  # CBOW
            hs=0,  # Negative sampling
            negative=5
        )

        # Save model
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        model.save(output_path)
        logger.info(f"Model saved to {output_path}")
        logger.info(f"Vocabulary size: {len(model.wv)}")

        return model

    except MemoryError as e:
        logger.error(f"Memory error during training: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error during training: {str(e)}")
        return None

def aggregate_yearly_embeddings(
    model_path: str = "data/derived/word2vec_model.bin",
    metadata_path: str = "data/derived/metadata_mpd.parquet",
    output_dir: str = "yearly_embeddings"
) -> Dict[int, Dict[str, np.ndarray]]:
    """
    Aggregate track embeddings by genre and year.

    Args:
        model_path: Path to trained Word2Vec model.
        metadata_path: Path to metadata parquet file.
        output_dir: Directory to save yearly embeddings.

    Returns:
        Dictionary mapping year to genre embeddings.
    """
    if not GENSIM_AVAILABLE:
        logger = get_logger()
        logger.error("gensim is not installed.")
        return {}

    logger = get_logger()
    logger.info("Aggregating yearly embeddings...")

    try:
        import pandas as pd
        from gensim.models import Word2Vec

        # Load model
        model = Word2Vec.load(model_path)
        logger.info(f"Loaded model with {len(model.wv)} vectors")

        # Load metadata
        df = pd.read_parquet(metadata_path)
        logger.info(f"Loaded {len(df)} tracks")

        # Group by year and genre
        yearly_genre_embeddings = {}

        for year in sorted(df['year'].dropna().unique()):
            year_df = df[df['year'] == year]
            yearly_genre_embeddings[year] = {}

            for genre in year_df['genre'].dropna().unique():
                genre_df = year_df[year_df['genre'] == genre]
                track_ids = genre_df['track_id'].tolist()

                # Get embeddings for tracks in this genre/year
                embeddings = []
                for tid in track_ids:
                    if tid in model.wv:
                        embeddings.append(model.wv[tid])

                if len(embeddings) > 0:
                    avg_embedding = np.mean(embeddings, axis=0)
                    yearly_genre_embeddings[year][genre] = avg_embedding
                else:
                    # Zero-fill for missing genres
                    yearly_genre_embeddings[year][genre] = np.zeros(model.vector_size)

                monitor_and_maybe_gc()

            # Flag low coverage years
            unique_tracks = len(year_df['track_id'].unique())
            if unique_tracks < 1000:
                logger.warning(f"Year {year} has low coverage: {unique_tracks} tracks")

            # Save yearly embeddings
            output_path = Path(output_dir) / f"{year}.npy"
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            np.save(output_path, yearly_genre_embeddings[year])
            logger.info(f"Saved embeddings for year {year} to {output_path}")

        return yearly_genre_embeddings

    except Exception as e:
        logger.error(f"Error aggregating embeddings: {str(e)}")
        return {}

def main() -> int:
    """Main entry point for embeddings pipeline."""
    set_deterministic_seed(42)
    setup_logging("pipeline_log.txt")
    logger = get_logger()

    try:
        # Train model
        model = train_global_word2vec()
        if model is None:
            logger.error("Failed to train model")
            return 1

        # Aggregate embeddings
        embeddings = aggregate_yearly_embeddings()
        if not embeddings:
            logger.error("Failed to aggregate embeddings")
            return 1

        logger.info("Embeddings pipeline completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
