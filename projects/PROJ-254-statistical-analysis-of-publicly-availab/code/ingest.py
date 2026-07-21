"""
Ingestion module for streaming MPD dataset and processing track metadata.

This module implements the streaming ingestion of the Spotify Million Playlist Dataset
using the Hugging Face datasets library. It handles memory management, track extraction,
and coverage validation as per the project specifications.
"""

import os
import sys
import gc
import logging
import time
import shutil
import json
import tempfile
from pathlib import Path
from typing import Iterator, List, Dict, Any, Optional, Set

# Import from project utils
from utils import setup_logging, get_logger, set_deterministic_seed
from memory_utils import (
    setup_memory_monitoring,
    get_memory_usage_gb,
    check_memory_thresholds,
    trigger_garbage_collection,
    enforce_memory_limit
)
from models import Track, TrackMetadata

# Setup logging
logger = setup_logging()

# Constants
MEMORY_LIMIT_GB = 6.0
MIN_VALID_YEAR = 1950
MAX_VALID_YEAR = 2024
MIN_COVERAGE_THRESHOLD = 0.80
DATASET_NAME = "spotify_million_playlist"
STREAMING_CHUNK_SIZE = 1000  # Number of playlists per batch

def setup_ingest_environment():
    """
    Initialize the ingestion environment.
    
    Returns:
        Logger instance for the ingestion module.
    """
    set_deterministic_seed(42)
    setup_memory_monitoring(MEMORY_LIMIT_GB)
    logger.info("Ingestion environment setup complete.")
    return logger

def stream_mpd_dataset(streaming: bool = True) -> Iterator[Dict]:
    """
    Stream the MPD dataset from Hugging Face in chunks.
    
    Yields:
        Dictionary containing playlist data with tracks.
        
    Raises:
        RuntimeError: If the dataset fetch fails.
    """
    try:
        from datasets import load_dataset
        
        logger.info(f"Loading dataset: {DATASET_NAME} in streaming mode...")
        dataset = load_dataset(DATASET_NAME, streaming=True)
        
        # Iterate through the 'train' split
        for item in dataset['train']:
            yield item
            
    except Exception as e:
        logger.error(f"Failed to load or stream dataset: {e}")
        raise RuntimeError(f"Dataset fetch failed: {e}")

def parse_playlists_to_tracks(playlist_batch: List[Dict[str, Any]]) -> List[Track]:
    """
    Parse a batch of playlists into Track objects.
    
    Args:
        playlist_batch: List of playlist dictionaries.
        
    Returns:
        List of Track objects extracted from the batch.
    """
    tracks = []
    for playlist in playlist_batch:
        playlist_id = playlist.get('playlist_id')
        tracks_in_playlist = playlist.get('tracks', [])
        
        for track_info in tracks_in_playlist:
            track_id = track_info.get('track_uri')
            track_name = track_info.get('track_name')
            artist_name = track_info.get('artist_name')
            album_name = track_info.get('album_name')
            release_year = track_info.get('release_year')
            genre_tags = track_info.get('genre_tags', [])
            
            # Only include tracks with valid release years
            if release_year is not None:
                try:
                    year_int = int(release_year)
                    if MIN_VALID_YEAR <= year_int <= MAX_VALID_YEAR:
                        track = Track(
                            track_id=track_id,
                            track_name=track_name,
                            artist_name=artist_name,
                            album_name=album_name,
                            release_year=year_int,
                            genre_tags=genre_tags if genre_tags else []
                        )
                        tracks.append(track)
                except (ValueError, TypeError):
                    continue
                    
    return tracks

def validate_year_range(year: int) -> bool:
    """
    Validate if a year is within the acceptable range.
    
    Args:
        year: The year to validate.
        
    Returns:
        True if the year is valid, False otherwise.
    """
    return MIN_VALID_YEAR <= year <= MAX_VALID_YEAR

def verify_track_count_file(output_path: Path) -> bool:
    """
    Verify that the track count file exists and is readable.
    
    Args:
        output_path: Path to the track count file.
        
    Returns:
        True if the file exists and is valid, False otherwise.
    """
    if not output_path.exists():
        logger.error(f"Track count file not found: {output_path}")
        return False
        
    try:
        with open(output_path, 'r') as f:
            count_str = f.read().strip()
            count = int(count_str)
            if count <= 0:
                logger.error(f"Invalid track count: {count}")
                return False
        return True
    except Exception as e:
        logger.error(f"Error reading track count file: {e}")
        return False

def validate_coverage(
    total_tracks: int, 
    covered_tracks: int, 
    min_threshold: float = MIN_COVERAGE_THRESHOLD
) -> Dict[str, Any]:
    """
    Validate the coverage of tracks with genre tags.
    
    Args:
        total_tracks: Total number of unique tracks.
        covered_tracks: Number of tracks with genre tags.
        min_threshold: Minimum acceptable coverage threshold.
        
    Returns:
        Dictionary with validation results.
    """
    coverage = covered_tracks / total_tracks if total_tracks > 0 else 0.0
    is_valid = coverage >= min_threshold
    
    result = {
        "total_tracks": total_tracks,
        "covered_tracks": covered_tracks,
        "coverage": coverage,
        "is_valid": is_valid,
        "threshold": min_threshold
    }
    
    return result

def ingest_mpd():
    """
    Main ingestion function for the MPD dataset.
    
    This function streams the Spotify Million Playlist Dataset, extracts track
    information, validates years, and writes the total count of unique tracks
    with valid release years to a file. It also performs coverage validation
    and logs critical information.
    
    Process:
        1. Stream the dataset in batches.
        2. Parse playlists to extract tracks.
        3. Track unique tracks with valid years.
        4. Monitor memory usage and trigger GC if needed.
        5. Atomically write the track count to disk.
        6. Validate coverage and log results.
        
    Memory Management:
        - Uses streaming to avoid loading full dataset into memory.
        - Processes data in batches of STREAMING_CHUNK_SIZE.
        - Monitors memory usage and triggers garbage collection at 90% threshold.
        - Enforces a hard limit of MEMORY_LIMIT_GB (6GB).
        
    Error Handling:
        - Raises RuntimeError if dataset fetch fails.
        - Raises RuntimeError if atomic write fails.
        - Exits with code 1 if coverage is below threshold.
        
    Output:
        - Writes total unique track count to data/derived/track_count.txt.
        - Writes coverage report to data/derived/coverage_report.json if coverage < 80%.
        
    Raises:
        RuntimeError: If dataset fetch or file write fails.
        SystemExit: If coverage validation fails.
    """
    logger.info("Starting MPD ingestion process...")
    setup_ingest_environment()
    
    # Ensure output directory exists
    output_dir = Path("data/derived")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    track_count_path = output_dir / "track_count.txt"
    coverage_report_path = output_dir / "coverage_report.json"
    
    # Use a set to track unique track IDs
    unique_tracks: Set[str] = set()
    tracks_with_genres: Set[str] = set()
    processed_playlists = 0
    current_batch = []
    
    logger.info(f"Streaming dataset: {DATASET_NAME}")
    
    try:
        dataset_stream = stream_mpd_dataset()
        
        for playlist_data in dataset_stream:
            current_batch.append(playlist_data)
            processed_playlists += 1
            
            # Process in batches
            if len(current_batch) >= STREAMING_CHUNK_SIZE:
                tracks = parse_playlists_to_tracks(current_batch)
                
                for track in tracks:
                    unique_tracks.add(track.track_id)
                    if track.genre_tags:
                        tracks_with_genres.add(track.track_id)
                
                # Memory management
                mem_gb = get_memory_usage_gb()
                if mem_gb > 5.4:  # 90% of 6GB
                    logger.warning(f"Memory usage high: {mem_gb:.2f}GB. Triggering GC.")
                    trigger_garbage_collection()
                
                # Check memory limit
                if not enforce_memory_limit(MEMORY_LIMIT_GB):
                    logger.error("Memory limit exceeded. Aborting.")
                    raise RuntimeError("Memory limit exceeded")
                
                current_batch = []
                
                if processed_playlists % 10000 == 0:
                    logger.info(f"Processed {processed_playlists} playlists, "
                              f"{len(unique_tracks)} unique tracks so far.")
        
        # Process remaining batch
        if current_batch:
            tracks = parse_playlists_to_tracks(current_batch)
            for track in tracks:
                unique_tracks.add(track.track_id)
                if track.genre_tags:
                    tracks_with_genres.add(track.track_id)
                
    except RuntimeError as e:
        logger.error(f"Ingestion failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        raise RuntimeError(f"Ingestion failed: {e}")
    
    total_tracks = len(unique_tracks)
    covered_tracks = len(tracks_with_genres)
    
    logger.info(f"Ingestion complete: {total_tracks} unique tracks processed.")
    
    # Validate coverage
    coverage_result = validate_coverage(total_tracks, covered_tracks)
    
    if not coverage_result['is_valid']:
        logger.critical(f"CRITICAL: Coverage < 80% ({coverage_result['coverage']*100:.2f}%). ABORTING.")
        
        # Write coverage report
        try:
            with open(coverage_report_path, 'w') as f:
                json.dump(coverage_result, f, indent=2)
            logger.info(f"Coverage report written to {coverage_report_path}")
        except Exception as e:
            logger.error(f"Failed to write coverage report: {e}")
            raise RuntimeError(f"Failed to write coverage report: {e}")
        
        # Exit with error code
        sys.exit(1)
    
    # Atomically write track count
    try:
        # Write to temporary file first
        temp_path = track_count_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            f.write(str(total_tracks))
        
        # Atomically rename
        os.replace(temp_path, track_count_path)
        logger.info(f"Track count written to {track_count_path}: {total_tracks}")
        
    except Exception as e:
        logger.error(f"Failed to write track count file: {e}")
        raise RuntimeError(f"Failed to write track count file: {e}")
    
    logger.info("Ingestion process completed successfully.")
    return total_tracks

def main():
    """
    Main entry point for the ingestion script.
    """
    try:
        track_count = ingest_mpd()
        logger.info(f"Final track count: {track_count}")
    except RuntimeError as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ingest_mpd()