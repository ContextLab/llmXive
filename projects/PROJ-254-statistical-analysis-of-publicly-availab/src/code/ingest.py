import os
import sys
import gc
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

import requests

from utils import get_logger, setup_logging, set_deterministic_seed
from memory_utils import monitor_and_maybe_gc, enforce_memory_limit, get_memory_usage_gb

def setup_requests_session() -> requests.Session:
    """Setup a requests session with retries and timeout."""
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        max_retries=requests.adapters.Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def download_parquet_chunk(
    url: str,
    output_path: Path,
    session: Optional[requests.Session] = None,
    chunk_size: int = 1024 * 1024
) -> None:
    """
    Download a parquet file with progress and error handling.

    Args:
        url: URL to download from.
        output_path: Local path to save the file.
        session: Requests session to use.
        chunk_size: Size of chunks to download.
    """
    if session is None:
        session = setup_requests_session()

    logger = get_logger()
    logger.info(f"Downloading {url} to {output_path}")

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        response = session.get(url, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                monitor_and_maybe_gc()

        logger.info(f"Downloaded {output_path.name}")
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise

def fetch_musicbrainz(
    track_id: str,
    session: Optional[requests.Session] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata from MusicBrainz API.

    Args:
        track_id: MusicBrainz recording ID.
        session: Requests session to use.

    Returns:
        Metadata dictionary or None if not found.
    """
    if session is None:
        session = setup_requests_session()

    logger = get_logger()
    url = f"https://musicbrainz.org/ws/2/recording/{track_id}?inc=artists+releases"

    try:
        response = session.get(url, headers={'User-Agent': 'llmXive/0.1'})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.debug(f"Track {track_id} not found in MusicBrainz")
        else:
            logger.error(f"API error for {track_id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error fetching {track_id}: {str(e)}")
        return None

def fuzzy_match_fallback(
    track_title: str,
    artist_name: str,
    year: Optional[int] = None
) -> Optional[str]:
    """
    Fallback fuzzy matching when exact MBID is not available.

    Args:
        track_title: Track title.
        artist_name: Artist name.
        year: Release year.

    Returns:
        Matched MusicBrainz ID or None.
    """
    logger = get_logger()
    logger.warning(f"Fuzzy matching not fully implemented for: {track_title} - {artist_name}")
    # Placeholder for future implementation
    return None

def ingest_mpd(
    mpd_base_url: str = "https://mlp.cs.cornell.edu/MPD/",
    output_dir: str = "data/raw"
) -> List[Path]:
    """
    Download MPD dataset files.

    Args:
        mpd_base_url: Base URL for MPD dataset.
        output_dir: Directory to save downloaded files.

    Returns:
        List of downloaded file paths.
    """
    logger = get_logger()
    logger.info("Starting MPD ingestion...")

    session = setup_requests_session()
    downloaded_files = []

    # Note: Actual MPD URLs would be specified here
    # This is a placeholder for the actual download logic
    urls = [
        # Example URLs - these would be the real MPD dataset URLs
        # f"{mpd_base_url}/part_0000.parquet",
        # f"{mpd_base_url}/part_0001.parquet",
    ]

    for i, url in enumerate(urls):
        filename = Path(url).name
        output_path = Path(output_dir) / filename
        try:
            download_parquet_chunk(url, output_path, session)
            downloaded_files.append(output_path)
            monitor_and_maybe_gc()
        except Exception as e:
            logger.error(f"Failed to download {url}: {str(e)}")
            continue

    logger.info(f"Downloaded {len(downloaded_files)} files")
    return downloaded_files

def join_mpd_mb(
    mpd_data: List[Dict[str, Any]],
    output_path: str = "data/derived/metadata_mpd.parquet"
) -> None:
    """
    Join MPD data with MusicBrainz metadata.

    Args:
        mpd_data: List of MPD track records.
        output_path: Path to save joined metadata.
    """
    logger = get_logger()
    logger.info("Joining MPD and MusicBrainz data...")

    try:
        import pandas as pd

        # Convert to DataFrame
        df = pd.DataFrame(mpd_data)

        # Filter tracks with missing years
        initial_count = len(df)
        df = df[df['year'].notna()]
        excluded_count = initial_count - len(df)

        logger.info(f"Excluded {excluded_count} tracks with missing years")

        # Save normalized metadata
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved joined metadata to {output_path}")

    except Exception as e:
        logger.error(f"Error joining data: {str(e)}")
        raise

def main() -> int:
    """Main entry point for ingestion pipeline."""
    set_deterministic_seed(42)
    setup_logging("pipeline_log.txt")
    logger = get_logger()

    try:
        # Download MPD data
        downloaded_files = ingest_mpd()

        if not downloaded_files:
            logger.error("No files downloaded")
            return 1

        # Process and join with MusicBrainz
        # This would load the parquet files and join with MB data
        logger.info("Ingestion pipeline completed")
        return 0

    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
