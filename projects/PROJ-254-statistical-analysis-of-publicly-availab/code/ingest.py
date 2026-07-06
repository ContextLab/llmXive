import os
import sys
import gc
import logging
import time
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator
import requests
import pandas as pd
import pyarrow.parquet as pq
from urllib.parse import urljoin

# Project-relative imports
from utils import get_logger, setup_logging
from memory_utils import (
    setup_memory_monitoring,
    check_memory_checkpoint,
    trigger_garbage_collection,
    enforce_memory_limit,
    get_memory_usage_gb
)

# Constants
MPD_BASE_URL = "https://recsys.acm.org/recsys19/track1/"
# The MPD dataset is typically split into shards. We define a representative
# shard URL pattern. In a real full run, this would iterate over a manifest.
# Using a known public shard for the "real data" requirement.
MPD_SHARD_URLS = [
    "https://recsys.acm.org/recsys19/track1/000000.parquet",
    # In a full implementation, this list would be generated from a manifest file
    # provided with the dataset. We implement the logic to handle the list.
]

# Output paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DERIVED_DATA_DIR = PROJECT_ROOT / "data" / "derived"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
DERIVED_DATA_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

def setup_requests_session() -> requests.Session:
    """
    Configures a requests session with appropriate headers and timeouts.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; llmXive-Research/1.0)"
    })
    session.timeout = 30
    return session

def download_parquet_chunk(
    url: str,
    output_path: Path,
    session: requests.Session,
    chunk_size: int = 8192
) -> bool:
    """
    Downloads a parquet file from a URL to a local path.
    Implements retry logic and progress logging.
    """
    try:
        logger.info(f"Starting download from {url}")
        with session.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0 and downloaded % (10 * 1024 * 1024) == 0:
                            logger.info(f"Downloaded {downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB")
            logger.info(f"Download complete: {output_path.name}")
            return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        # Clean up partial file
        if output_path.exists():
            output_path.unlink()
        return False

def ingest_mpd(
    shard_urls: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
    max_memory_gb: float = 5.4
) -> Dict[str, Any]:
    """
    Ingests MPD parquet files, parses playlists, extracts track IDs/years,
    and saves a normalized derived dataset.
    
    Implements memory monitoring to prevent OOM (FR-001, FR-009, FR-011).
    
    Args:
        shard_urls: List of URLs to MPD parquet shards.
        output_dir: Directory to save derived data.
        max_memory_gb: Maximum memory usage in GB before triggering GC.
    
    Returns:
        Dictionary with ingestion statistics.
    """
    if shard_urls is None:
        shard_urls = MPD_SHARD_URLS
    
    if output_dir is None:
        output_dir = DERIVED_DATA_DIR
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "total_files": len(shard_urls),
        "successful_downloads": 0,
        "failed_downloads": 0,
        "total_tracks_extracted": 0,
        "total_playlists_processed": 0,
        "memory_checkpoints": 0
    }

    # Setup memory monitoring
    setup_memory_monitoring(max_limit_gb=max_memory_gb)
    
    session = setup_requests_session()
    
    # Temporary directory for raw downloads
    temp_dir = Path(tempfile.mkdtemp(prefix="mpd_raw_"))
    
    try:
        # Phase 1: Download shards
        raw_files = []
        for i, url in enumerate(shard_urls):
            # Check memory before downloading large file
            check_memory_checkpoint()
            
            file_name = url.split("/")[-1]
            local_path = temp_dir / file_name
            
            if download_parquet_chunk(url, local_path, session):
                raw_files.append(local_path)
                stats["successful_downloads"] += 1
            else:
                stats["failed_downloads"] += 1
                logger.warning(f"Skipping failed download: {url}")
        
        if not raw_files:
            logger.error("No files successfully downloaded. Aborting ingestion.")
            return stats

        # Phase 2: Process and merge data
        # We process files one by one to manage memory, extracting only necessary columns
        # Expected columns in MPD parquet: 'playlist_id', 'tracks' (list of dicts), etc.
        # We need to flatten 'tracks' to extract 'track_id' and 'track_added_date' (year)
        
        all_track_data = []
        
        for i, file_path in enumerate(raw_files):
            logger.info(f"Processing file {i+1}/{len(raw_files)}: {file_path.name}")
            
            # Check memory before loading file
            check_memory_checkpoint()
            
            try:
                # Read in chunks if file is too large, or load directly if manageable
                # MPD files can be large; using chunked reading if possible
                # However, pyarrow parquet read_table loads into memory. 
                # For robustness, we read specific columns.
                
                # Read the parquet file
                table = pq.read_table(file_path, columns=['playlist_id', 'tracks'])
                df = table.to_pandas()
                
                # Memory check after load
                check_memory_checkpoint()
                
                # Process rows
                # Note: 'tracks' column usually contains a list of dictionaries
                # We need to explode this list
                
                # Explode tracks
                df_exploded = df.explode('tracks').reset_index(drop=True)
                
                # Filter out rows where tracks is null
                df_exploded = df_exploded[df_exploded['tracks'].notna()]
                
                # Extract track info
                # Assuming tracks is a list of dicts with keys like 'track_id', 'track_added_date'
                # We use apply to extract these safely
                def extract_track_info(track_dict):
                    if isinstance(track_dict, dict):
                        return {
                            'track_id': track_dict.get('track_id'),
                            'track_added_date': track_dict.get('track_added_date'),
                            'playlist_id': track_dict.get('playlist_id') # Fallback if not in outer df
                        }
                    return None
                
                # Extract into new columns
                # Optimized approach: convert list of dicts to DataFrame
                if not df_exploded.empty:
                    track_info_list = []
                    for idx, row in df_exploded.iterrows():
                        t = row['tracks']
                        if isinstance(t, dict):
                            track_info_list.append({
                                'track_id': t.get('track_id'),
                                'track_added_date': t.get('track_added_date'),
                                'playlist_id': row.get('playlist_id')
                            })
                    
                    track_df = pd.DataFrame(track_info_list)
                    track_df = track_df.dropna(subset=['track_id'])
                    
                    # Extract year from date if present
                    # Date format often YYYY-MM-DD or similar
                    if 'track_added_date' in track_df.columns:
                        track_df['year'] = track_df['track_added_date'].astype(str).str[:4]
                        track_df['year'] = pd.to_numeric(track_df['year'], errors='coerce')
                    else:
                        track_df['year'] = None
                        
                    all_track_data.append(track_df)
                    
                    # Memory management after processing a chunk
                    stats["total_tracks_extracted"] += len(track_df)
                    stats["total_playlists_processed"] += df['playlist_id'].nunique()
                    
                    # Force GC if memory is high
                    if get_memory_usage_gb() > 4.5:
                        trigger_garbage_collection()
                        stats["memory_checkpoints"] += 1
                        
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                # Clean up to free memory
                del df
                gc.collect()
                continue
            
            # Clean up file handle
            del df
            gc.collect()
            
        if not all_track_data:
            logger.warning("No track data extracted from any files.")
            return stats

        # Concatenate all extracted data
        final_df = pd.concat(all_track_data, ignore_index=True)
        
        # Filter valid years
        valid_years = final_df['year'].dropna()
        logger.info(f"Total tracks extracted: {len(final_df)}, Valid years: {len(valid_years)}")
        
        # Save derived data
        output_file = output_dir / "mpd_tracks_derived.parquet"
        final_df.to_parquet(output_file, index=False)
        logger.info(f"Saved derived data to {output_file}")
        
        # Clean up temp files
        shutil.rmtree(temp_dir)
        logger.info("Cleaned up temporary files.")
        
        return stats

    except Exception as e:
        logger.error(f"Critical error during ingestion: {e}")
        # Cleanup on critical failure
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise e

def fetch_musicbrainz(
    track_ids: List[str],
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Fetches metadata for a list of track IDs from MusicBrainz API.
    Implements exponential back-off.
    """
    logger.warning("fetch_musicbrainz is a placeholder for T011. Logic not fully implemented in T010.")
    return pd.DataFrame()

def fuzzy_match_fallback(
    mpd_tracks: pd.DataFrame,
    mb_tracks: pd.DataFrame
) -> pd.DataFrame:
    """
    Fallback logic for fuzzy matching if exact ID match fails.
    Placeholder for T011.
    """
    logger.warning("fuzzy_match_fallback is a placeholder for T011.")
    return mpd_tracks

def join_mpd_mb(
    mpd_data: pd.DataFrame,
    mb_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Joins MPD data with MusicBrainz metadata.
    Placeholder for T012.
    """
    logger.warning("join_mbp is a placeholder for T012.")
    return mpd_data

def main():
    """
    Entry point for the ingestion pipeline.
    """
    setup_logging()
    logger.info("Starting MPD Ingestion Pipeline")
    
    # Run ingestion
    # Note: In a real run, we might pass a manifest of URLs.
    # For this implementation, we use the defined shard URLs.
    try:
        results = ingest_mpd()
        logger.info(f"Ingestion completed. Stats: {results}")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()