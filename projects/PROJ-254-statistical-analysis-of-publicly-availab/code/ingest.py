"""
Ingestion module for the Spotify Million Playlist Dataset (MPD).

This module handles the streaming ingestion of the MPD dataset,
validation of data coverage, and integration with MusicBrainz metadata.
It operates in an out-of-core fashion to handle large datasets within
memory constraints.
"""

import os
import sys
import gc
import logging
import time
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Iterator, Any
import json
import hashlib
from datetime import datetime

# Local imports
from utils import setup_logging, get_logger, set_deterministic_seed
from memory_utils import (
    setup_memory_monitoring,
    get_memory_usage_gb,
    check_memory_thresholds,
    trigger_garbage_collection,
    check_memory_checkpoint
)
from models import Track, TrackMetadata, Playlist

# Configure logging
logger = get_logger(__name__)

# Constants
MPD_DATASET_NAME = "spotify_million_playlist"
DATA_DERIVED_DIR = Path("data/derived")
TRACK_COUNT_FILE = DATA_DERIVED_DIR / "track_count.txt"
MIN_YEAR = 1950
MAX_YEAR = 2024
MEMORY_LIMIT_GB = 6.0
MEMORY_CHECKPOINT_MB = 500

def setup_requests_session():
    """
    Setup a requests session with appropriate headers and timeouts.

    Returns:
        requests.Session: Configured session object.
    """
    import requests
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'llmXive/1.0 (research-project)'
    })
    session.timeout = 30
    return session

def stream_mpd_dataset() -> Iterator[Dict[str, Any]]:
    """
    Stream the MPD dataset from HuggingFace Datasets.

    This function uses the HuggingFace `datasets` library to stream
    the Spotify Million Playlist Dataset in chunks, avoiding loading
    the entire dataset into memory.

    Yields:
        Dict[str, Any]: A dictionary representing a single playlist record.
    """
    try:
        from datasets import load_dataset
        logger.info(f"Loading dataset: {MPD_DATASET_NAME} in streaming mode")
        dataset = load_dataset(MPD_DATASET_NAME, streaming=True)
        if 'train' in dataset:
            train_ds = dataset['train']
        else:
            train_ds = dataset[list(dataset.keys())[0]]

        for item in train_ds:
            yield item
    except Exception as e:
        logger.error(f"Failed to stream MPD dataset: {e}")
        raise RuntimeError(f"Failed to stream MPD dataset: {e}") from e

def parse_playlists_to_tracks(playlists: List[Dict[str, Any]]) -> Iterator[Track]:
    """
    Parse playlist records into Track objects.

    Args:
        playlists: List of playlist dictionaries from the dataset.

    Yields:
        Track: Valid Track objects extracted from the playlist data.
    """
    for playlist in playlists:
        # Extract tracks from the playlist
        # MPD structure: playlist contains 'tracks' which is a list of track dicts
        tracks_list = playlist.get('tracks', [])
        if not tracks_list:
            continue

        for track_data in tracks_list:
            try:
                # Extract relevant fields
                track_id = track_data.get('track_uri', '').split(':')[-1] if track_data.get('track_uri') else None
                track_name = track_data.get('track_name', '')
                artist_name = track_data.get('artist_name', '')
                album_name = track_data.get('album_name', '')
                release_year = track_data.get('release_date', '').split('-')[0] if track_data.get('release_date') else None

                # Validate and convert year
                if release_year:
                    try:
                        year_int = int(release_year)
                        if MIN_YEAR <= year_int <= MAX_YEAR:
                            yield Track(
                                track_id=track_id,
                                track_name=track_name,
                                artist_name=artist_name,
                                album_name=album_name,
                                release_year=year_int
                            )
                    except (ValueError, TypeError):
                        continue
            except Exception as e:
                logger.debug(f"Skipping track due to parsing error: {e}")
                continue

def validate_year_range(tracks: List[Track]) -> Tuple[int, List[int]]:
    """
    Validate that the dataset contains the required historical year range.

    Args:
        tracks: List of Track objects to validate.

    Returns:
        Tuple of (count of valid tracks, list of excluded years due to low coverage)
    """
    years = [t.release_year for t in tracks if t.release_year]
    unique_years = sorted(set(years))

    if not unique_years:
        logger.warning("No valid years found in dataset")
        return 0, []

    min_year_found = min(unique_years)
    max_year_found = max(unique_years)

    logger.info(f"Dataset year range: {min_year_found} - {max_year_found}")

    # Check if we have sufficient coverage from mid-20th century to 2024
    if min_year_found > 1970:
        logger.warning(f"Dataset starts at {min_year_found}, missing early years (1950-1970)")
    if max_year_found < 2020:
        logger.warning(f"Dataset ends at {max_year_found}, missing recent years")

    # Identify years with low coverage (fewer than 1000 tracks)
    year_counts = {}
    for t in tracks:
        if t.release_year:
            year_counts[t.release_year] = year_counts.get(t.release_year, 0) + 1

    low_coverage_years = [y for y, count in year_counts.items() if count < 1000]
    logger.info(f"Found {len(low_coverage_years)} years with low coverage (<1000 tracks)")

    return len(tracks), low_coverage_years

def verify_track_count_file() -> int:
    """
    Verify the existence and format of the track count file.

    This function checks if data/derived/track_count.txt exists and
    contains a valid integer representing the count of unique tracks
    with valid release years.

    Returns:
        int: The track count value from the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file content is not a valid integer.
    """
    if not TRACK_COUNT_FILE.exists():
        raise FileNotFoundError(
            f"Track count file not found: {TRACK_COUNT_FILE}. "
            "Please run ingest_mpd first to generate this file."
        )

    try:
        content = TRACK_COUNT_FILE.read_text().strip()
        if not content:
            raise ValueError("Track count file is empty")

        track_count = int(content)
        if track_count <= 0:
            raise ValueError(f"Invalid track count: {track_count} (must be positive)")

        logger.info(f"Verified track count: {track_count}")
        return track_count

    except ValueError as e:
        raise ValueError(f"Invalid format in track count file: {e}")

def validate_coverage(total_tracks: int, valid_tracks: int) -> bool:
    """
    Validate that the dataset coverage meets the minimum threshold.

    This function implements SC-001 by checking if the number of valid
    tracks (with years 1950-2024) meets the 80% threshold of the total
    MPD tracks.

    Args:
        total_tracks: Total number of tracks in the MPD dataset.
        valid_tracks: Number of tracks with valid release years.

    Returns:
        bool: True if coverage is sufficient, False otherwise.

    Raises:
        RuntimeError: If coverage is below the 80% threshold.
    """
    if total_tracks == 0:
        raise RuntimeError("Total track count is zero, cannot calculate coverage")

    coverage_ratio = valid_tracks / total_tracks
    logger.info(f"Coverage: {valid_tracks}/{total_tracks} = {coverage_ratio:.2%}")

    if coverage_ratio < 0.80:
        error_msg = (
            f"Coverage insufficient: {coverage_ratio:.2%} < 80%. "
            f"Valid tracks: {valid_tracks}, Total tracks: {total_tracks}. "
            "Aborting to prevent analysis on insufficient data."
        )
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    logger.info("Coverage validation passed")
    return True

def ingest_mpd() -> int:
    """
    Ingest the MPD dataset and save track count.

    This function streams the entire MPD dataset, extracts unique tracks
    with valid release years (1950-2024), and writes the total count to
    data/derived/track_count.txt atomically.

    The function implements memory management by:
    1. Processing data in streaming chunks
    2. Monitoring memory usage and triggering GC when needed
    3. Not storing all tracks in memory simultaneously

    Returns:
        int: The total count of unique tracks with valid release years.

    Raises:
        RuntimeError: If the dataset fetch fails or memory limits are exceeded.
    """
    setup_memory_monitoring()
    set_deterministic_seed(42)

    logger.info("Starting MPD ingestion...")
    logger.info(f"Memory limit: {MEMORY_LIMIT_GB}GB")

    # Ensure output directory exists
    DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    # Track unique track IDs to avoid duplicates
    seen_track_ids = set()
    valid_track_count = 0

    try:
        stream = stream_mpd_dataset()
        batch = []
        batch_size = 10000

        for idx, playlist in enumerate(stream):
            # Check memory periodically
            if idx % 1000 == 0:
                mem_gb = get_memory_usage_gb()
                if mem_gb > MEMORY_LIMIT_GB * 0.9:
                    logger.warning(f"Memory usage high: {mem_gb:.2f}GB, triggering GC")
                    trigger_garbage_collection()

            # Parse tracks from this playlist
            tracks = list(parse_playlists_to_tracks([playlist]))

            # Process each track
            for track in tracks:
                if track.track_id and track.track_id not in seen_track_ids:
                    seen_track_ids.add(track.track_id)
                    if track.release_year and MIN_YEAR <= track.release_year <= MAX_YEAR:
                        valid_track_count += 1

            # Periodic checkpoint
            if idx % 10000 == 0 and idx > 0:
                logger.info(f"Processed {idx} playlists, {valid_track_count} valid tracks so far")
                check_memory_checkpoint(MEMORY_CHECKPOINT_MB)

        # Write track count atomically
        temp_file = TRACK_COUNT_FILE.with_suffix('.tmp')
        temp_file.write_text(str(valid_track_count))
        temp_file.rename(TRACK_COUNT_FILE)

        logger.info(f"Ingestion complete: {valid_track_count} tracks processed")

        # Log final memory state
        mem_stats = check_memory_thresholds()
        logger.info(f"Final memory stats: {mem_stats}")

        return valid_track_count

    except RuntimeError as e:
        logger.error(f"Ingestion failed: {e}")
        # Clean up partial file if exists
        if TRACK_COUNT_FILE.exists():
            TRACK_COUNT_FILE.unlink()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        raise RuntimeError(f"Ingestion failed with unexpected error: {e}") from e

def fetch_musicbrainz(track: Track, session: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch MusicBrainz metadata for a track.

    Args:
        track: Track object to fetch metadata for.
        session: Optional requests session.

    Returns:
        Dict containing MusicBrainz metadata, or None if not found.
    """
    # Implementation would use musicbrainzngs
    # This is a placeholder for the actual implementation
    logger.debug(f"Fetching MusicBrainz metadata for: {track.track_name} by {track.artist_name}")
    return None

def match_fuzzy_tracks(track: Track, threshold: float = 0.85) -> Optional[Dict[str, Any]]:
    """
    Perform fuzzy matching of tracks against MusicBrainz.

    Args:
        track: Track object to match.
        threshold: Minimum similarity threshold (0.0 to 1.0).

    Returns:
        Dict containing match result with confidence score, or None.
    """
    # Implementation would use thefuzz
    logger.debug(f"Performing fuzzy match for: {track.track_name} by {track.artist_name}")
    return None

def apply_matching_logic(track: Track) -> Optional[TrackMetadata]:
    """
    Apply the decision tree for selecting the best MusicBrainz match.

    Args:
        track: Original track object.

    Returns:
        TrackMetadata object if match found, None otherwise.
    """
    # Try direct ID lookup first, then fuzzy match
    # This is a placeholder for the actual implementation
    return None

def join_mpd_mb(mpd_tracks: List[Track], mb_metadata: List[Dict]) -> List[TrackMetadata]:
    """
    Join MPD tracks with MusicBrainz metadata.

    Args:
        mpd_tracks: List of MPD track objects.
        mb_metadata: List of MusicBrainz metadata dictionaries.

    Returns:
        List of joined TrackMetadata objects.
    """
    # Implementation would perform the join operation
    return []

def calculate_coverage(mpd_tracks: List[Track], matched_tracks: List[TrackMetadata]) -> float:
    """
    Calculate the coverage percentage of tracks with genre tags.

    Args:
        mpd_tracks: Total MPD tracks.
        matched_tracks: Tracks successfully matched with metadata.

    Returns:
        Coverage percentage as a float.
    """
    if not mpd_tracks:
        return 0.0
    return len(matched_tracks) / len(mpd_tracks)

def main():
    """Main entry point for the ingestion module."""
    setup_logging()
    try:
        count = ingest_mpd()
        logger.info(f"Successfully ingested {count} tracks")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()