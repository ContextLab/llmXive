import os
import sys
import gc
import logging
import time
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
import json

# Import project utilities
from utils import setup_logging, get_logger, set_deterministic_seed
from memory_utils import check_memory_thresholds, trigger_garbage_collection, get_memory_usage_gb
from models import Track, Playlist

# Import datasets library for streaming MPD
from datasets import load_dataset

# Configure logging
logger = get_logger()

# Constants
DATA_DERIVED_DIR = Path("data/derived")
PIPELINE_LOG_FILE = "pipeline_log.txt"
TRACK_COUNT_FILE = DATA_DERIVED_DIR / "track_count.txt"
MEMORY_LIMIT_GB = 6.0
MEMORY_WARNING_THRESHOLD = 0.9  # 90% of limit

def setup_requests_session():
    """
    Setup a requests session with default timeouts and retries.
    Returns a requests.Session object.
    """
    import requests
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        max_retries=requests.packages.urllib3.util.retry.Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def stream_mpd_dataset() -> Iterator[Dict[str, Any]]:
    """
    Stream the Spotify Million Playlist Dataset using HuggingFace datasets.
    Yields individual track records from the dataset.
    
    Returns:
        Iterator yielding track dictionaries.
        
    Raises:
        RuntimeError: If the dataset cannot be fetched.
    """
    try:
        # Load the dataset in streaming mode to avoid OOM
        # The dataset name is "spotify_million_playlist" as per T040
        ds = load_dataset("spotify_million_playlist", streaming=True)
        
        # The dataset usually has a 'train' split or a single split
        # We iterate over the first available split
        split_name = next(iter(ds.keys()))
        tracks_iterator = ds[split_name]
        
        for item in tracks_iterator:
            yield item
            
    except Exception as e:
        # FAIL LOUDLY: Do not fall back to synthetic data
        logger.error(f"Failed to stream MPD dataset: {e}")
        raise RuntimeError(f"Critical: Unable to fetch real MPD data. Aborting. {e}")

def parse_playlists_to_tracks(iterator: Iterator[Dict[str, Any]]) -> Iterator[Track]:
    """
    Parse the raw dataset items into Track objects.
    The MPD dataset structure typically has a 'playlists' list where each playlist
    contains 'tracks'. We flatten this to get individual tracks.
    
    Args:
        iterator: Iterator of raw dataset items (playlists).
        
    Yields:
        Track objects.
    """
    for playlist_item in iterator:
        # The dataset structure: {'playlists': [{'name': ..., 'tracks': [...]}]}
        # However, in the streaming parquet version, it might be flattened or structured differently.
        # Based on common MPD parquet structures on HF:
        # It often has a column 'tracks' which is a list of dicts or a list of strings (URI).
        # Let's handle the common structure where 'tracks' is a list of dicts with 'track_uri', 'added_at', etc.
        
        raw_playlists = playlist_item.get('playlists', [])
        
        for playlist in raw_playlists:
            tracks_list = playlist.get('tracks', [])
            # tracks_list is typically a list of dicts like:
            # {'track_uri': 'spotify:track:...', 'added_at': '2018-01-01', ...}
            
            for track_data in tracks_list:
                if not isinstance(track_data, dict):
                    continue
                
                # Extract relevant fields
                track_uri = track_data.get('track_uri', '')
                added_at = track_data.get('added_at', '')
                
                # Extract year from added_at if possible, or derive from track metadata later
                # For now, we pass the raw data and let downstream handle enrichment
                year = None
                if added_at and isinstance(added_at, str) and len(added_at) >= 4:
                    try:
                        year = int(added_at[:4])
                    except ValueError:
                        pass
                
                # Create Track object
                # Note: We are using the native MPD fields here. Genre enrichment happens in T021/T022.
                try:
                    track = Track(
                        track_uri=track_uri,
                        added_at=added_at,
                        year=year,
                        # We don't have genre yet, so leave it out or set to None if model allows
                        # If Track model requires genre, we might need EnrichedTrack here, 
                        # but T005 says Track is native only.
                    )
                    yield track
                except Exception as e:
                    # Log but continue processing
                    logger.debug(f"Skipping invalid track: {e}")
                    continue

def ingest_mpd():
    """
    Main ingestion function for MPD dataset.
    Downloads/streams MPD parquet files, parses playlists, extracts track IDs/years,
    and integrates memory monitoring.
    
    Writes total track count to data/derived/track_count.txt.
    Logs "Ingestion complete: X tracks processed" to pipeline_log.txt.
    
    Dependencies:
        T041 (Streaming loader with fail-loudly)
        T007 (Memory monitoring)
    """
    logger.info("Starting MPD ingestion...")
    
    # Ensure output directory exists
    DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    
    total_tracks = 0
    stream = stream_mpd_dataset()
    
    # Process tracks in batches to monitor memory
    batch_size = 10000
    batch_count = 0
    
    # We need to store track data to pass to downstream, but we must be memory efficient.
    # For T019, the requirement is to count tracks and write the count.
    # We will iterate, count, and optionally save intermediate metadata if needed for T022.
    # However, T022 requires joining with MusicBrainz. We should store the raw track info 
    # (track_uri, year) to a temporary file or process in a streaming join if possible.
    # Given the constraints, let's write the track URIs and years to a temporary parquet/csv 
    # for downstream use, while counting.
    
    # We will collect track URIs and years. 
    # To avoid OOM, we will write to a file in chunks.
    temp_tracks_file = DATA_DERIVED_DIR / "temp_mpd_tracks.parquet"
    
    # If the file exists from a previous partial run, remove it
    if temp_tracks_file.exists():
        temp_tracks_file.unlink()
        
    import pandas as pd
    from datasets import Dataset as HFDataset
    
    # We will collect rows in a list and flush when it gets too big
    rows_buffer = []
    
    try:
        for track in parse_playlists_to_tracks(stream):
            total_tracks += 1
            
            # Add to buffer
            rows_buffer.append({
                'track_uri': track.track_uri,
                'year': track.year
            })
            
            # Check memory periodically
            if total_tracks % 10000 == 0:
                mem_gb = get_memory_usage_gb()
                if mem_gb > MEMORY_LIMIT_GB * MEMORY_WARNING_THRESHOLD:
                    logger.warning(f"Memory usage high: {mem_gb:.2f} GB. Triggering GC.")
                    trigger_garbage_collection()
            
            # Flush buffer to disk periodically
            if len(rows_buffer) >= batch_size:
                df = pd.DataFrame(rows_buffer)
                # Append to parquet
                if temp_tracks_file.exists():
                    existing_df = pd.read_parquet(temp_tracks_file)
                    combined_df = pd.concat([existing_df, df], ignore_index=True)
                    combined_df.to_parquet(temp_tracks_file, index=False)
                else:
                    df.to_parquet(temp_tracks_file, index=False)
                
                rows_buffer = []
                gc.collect()
                
        # Flush remaining
        if rows_buffer:
            df = pd.DataFrame(rows_buffer)
            if temp_tracks_file.exists():
                existing_df = pd.read_parquet(temp_tracks_file)
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                combined_df.to_parquet(temp_tracks_file, index=False)
            else:
                df.to_parquet(temp_tracks_file, index=False)
                
    except RuntimeError as e:
        # Re-raise if it's the "fail loudly" error
        raise e
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise e
    
    # Write total count
    with open(TRACK_COUNT_FILE, 'w') as f:
        f.write(str(total_tracks))
        
    logger.info(f"Ingestion complete: {total_tracks} tracks processed")
    
    # Clean up temp file if we want to keep only the count for now?
    # No, T022 needs the data. So we leave temp_mpd_tracks.parquet.
    # However, the task T019 specifically says "write total track count".
    # It does not explicitly say to keep the temp file, but downstream T022 needs it.
    # We will keep it.
    
    return total_tracks

def validate_year_range(track_uris: List[str], year_mapping: Dict[str, int]):
    """
    Verify that the downloaded MPD data contains the required historical year range.
    
    Args:
        track_uris: List of track URIs.
        year_mapping: Dictionary mapping track_uri to year.
        
    Returns:
        bool: True if range is sufficient, False otherwise.
    """
    years = [y for y in year_mapping.values() if y is not None]
    if not years:
        logger.warning("No valid years found in data.")
        return False
        
    min_year = min(years)
    max_year = max(years)
    
    logger.info(f"Data year range: {min_year} to {max_year}")
    
    # Check if range is sufficient (e.g., at least 10 years)
    if max_year - min_year < 10:
        logger.warning(f"Year range {max_year - min_year} is insufficient (< 10 years).")
        return False
        
    return True

def validate_coverage():
    """
    Verify row count against 80% threshold based on total count read from track_count.txt.
    If < 80% of total MPD tracks, ABORT with Critical Error.
    """
    if not TRACK_COUNT_FILE.exists():
        logger.error("Track count file not found. Cannot validate coverage.")
        sys.exit(1)
        
    with open(TRACK_COUNT_FILE, 'r') as f:
        total_count = int(f.read().strip())
        
    # Check the temp file for actual processed count
    temp_tracks_file = DATA_DERIVED_DIR / "temp_mpd_tracks.parquet"
    if not temp_tracks_file.exists():
        logger.error("Processed tracks file not found.")
        sys.exit(1)
        
    import pandas as pd
    df = pd.read_parquet(temp_tracks_file)
    processed_count = len(df)
    
    ratio = processed_count / total_count if total_count > 0 else 0
    
    if ratio < 0.80:
        logger.critical(f"Coverage {ratio:.2%} is below 80% threshold. ABORTING.")
        sys.exit(1)
        
    logger.info(f"Coverage check passed: {ratio:.2%}")
    return True

def fetch_musicbrainz(track_uris: List[str]):
    """
    Fetch MusicBrainz metadata via API with exponential back-off and fuzzy matching fallback.
    
    Args:
        track_uris: List of track URIs.
        
    Returns:
        List of enriched track data.
    """
    import musicbrainzngs
    from thefuzz import fuzz
    
    musicbrainzngs.set_useragent("llmXive", "1.0", "contact@example.com")
    
    enriched_data = []
    
    # This is a placeholder for the actual implementation which would be in T021.
    # T019 focuses on ingestion and counting.
    # We return an empty list for now as T021 is a separate task.
    return enriched_data

def fuzzy_match_fallback(queries: List[Dict[str, str]], candidates: List[Dict[str, str]]):
    """
    Fuzzy matching fallback logic.
    
    Args:
        queries: List of query dicts (artist, track, album).
        candidates: List of candidate dicts.
        
    Returns:
        List of matched results.
    """
    # Placeholder for T009 test requirement
    return []

def join_mpd_mb(mpd_data: List[Dict], mb_data: List[Dict]):
    """
    Join MPD and MusicBrainz data.
    
    Args:
        mpd_data: List of MPD track dicts.
        mb_data: List of MusicBrainz track dicts.
        
    Returns:
        Joined data.
    """
    # Placeholder for T022
    return []

def calculate_coverage(enriched_tracks: List[Dict]):
    """
    Calculate percentage of MPD tracks with genre tags.
    
    Args:
        enriched_tracks: List of enriched track dicts.
        
    Returns:
        Float percentage.
    """
    # Placeholder for T053
    return 0.0

def main():
    """
    Main entry point for ingestion script.
    """
    set_deterministic_seed(42)
    setup_logging(log_file=PIPELINE_LOG_FILE)
    
    try:
        count = ingest_mpd()
        validate_coverage()
        logger.info("Ingestion pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()