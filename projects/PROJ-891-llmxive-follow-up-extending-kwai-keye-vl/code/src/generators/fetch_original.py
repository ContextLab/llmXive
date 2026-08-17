"""
Fetch original, unmodified ActivityNet Captions video clips for the control group.

This script retrieves a representative subset of source clips from the
ActivityNet Captions dataset using the Hugging Face datasets library.
It saves the raw video files to `data/raw/original/` and generates a
metadata CSV mapping video IDs to their original timestamps and URLs.

CRITICAL: This loader fails loudly if the real data source is unavailable.
It does NOT fall back to synthetic or mock data.
"""

import os
import sys
import time
import logging
from pathlib import Path
import json

import pandas as pd
import requests
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
DATASET_NAME = "ActivityNet/activitynet-captions"
DATASET_SPLIT = "train"
OUTPUT_DIR = Path("data/raw/original")
METADATA_FILE = OUTPUT_DIR / "original_clips_metadata.csv"
MAX_CLIPS_TO_FETCH = 50  # Representative subset size for the control group
TIMEOUT_SECONDS = 300    # Timeout per download request

def ensure_output_dir(path: Path) -> None:
    """Create the output directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {path}")

def download_video(video_url: str, output_path: Path, timeout: int = TIMEOUT_SECONDS) -> bool:
    """
    Download a video file from a URL to the specified output path.

    Args:
        video_url: The URL of the video to download.
        output_path: The local path where the video should be saved.
        timeout: Request timeout in seconds.

    Returns:
        True if download was successful, False otherwise.
    """
    if output_path.exists():
        logger.info(f"Video already exists, skipping: {output_path.name}")
        return True

    logger.info(f"Downloading: {video_url} -> {output_path}")
    try:
        response = requests.get(video_url, stream=True, timeout=timeout)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        if os.path.getsize(output_path) == 0:
            logger.error(f"Downloaded file is empty: {output_path}")
            os.remove(output_path)
            return False

        logger.info(f"Successfully downloaded: {output_path.name}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {video_url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {video_url}: {e}")
        return False

def fetch_original_clips() -> pd.DataFrame:
    """
    Fetch original unmodified ActivityNet Captions clips.

    This function:
    1. Loads the ActivityNet Captions dataset in streaming mode.
    2. Extracts unique video IDs and their associated timestamps/URLs.
    3. Downloads a representative subset of videos to `data/raw/original/`.
    4. Saves a metadata CSV mapping IDs to timestamps and file paths.

    Returns:
        A pandas DataFrame containing the metadata of fetched clips.
    """
    ensure_output_dir(OUTPUT_DIR)

    logger.info(f"Loading dataset: {DATASET_NAME} (split={DATASET_SPLIT}, streaming=True)")
    try:
        dataset = load_dataset(DATASET_NAME, split=DATASET_SPLIT, streaming=True)
    except Exception as e:
        logger.critical(f"Failed to load dataset from Hugging Face: {e}")
        raise RuntimeError("Failed to load real data source. Aborting.")

    # ActivityNet Captions dataset structure typically includes:
    # 'video_id', 'timestamps', 'sentences', 'url' (or similar)
    # We need to extract unique video entries with their URLs and timestamps.
    # Since the dataset is streaming, we iterate and collect unique video_ids.

    video_data = {} # video_id -> {url, timestamps}
    count = 0

    logger.info("Iterating through dataset to collect unique video metadata...")
    for item in dataset:
        if count >= MAX_CLIPS_TO_FETCH * 2: # Fetch slightly more to ensure we have enough unique ones
            break

        vid = item.get('video_id')
        url = item.get('url')
        timestamps = item.get('timestamps', []) # List of [start, end]

        if not vid or not url:
            continue

        # ActivityNet often has multiple entries per video (different captions)
        # We want unique videos, so we take the first occurrence of the URL/ID pair
        if vid not in video_data:
            video_data[vid] = {
                'url': url,
                'timestamps': timestamps,
                'video_id': vid
            }
            count += 1

        if len(video_data) >= MAX_CLIPS_TO_FETCH:
            break

    if not video_data:
        raise RuntimeError("No video data found in the dataset stream.")

    logger.info(f"Collected {len(video_data)} unique video entries.")

    # Download videos
    downloaded_rows = []
    failed_count = 0

    for vid, info in video_data.items():
        # Sanitize filename
        safe_vid = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in vid)
        filename = f"{safe_vid}.mp4"
        output_path = OUTPUT_DIR / filename

        success = download_video(info['url'], output_path)

        if success:
            # Determine a representative timestamp range if multiple exist
            # Usually the first caption's timestamp is a good representative for the clip
            if info['timestamps']:
                start_time = info['timestamps'][0][0]
                end_time = info['timestamps'][0][1]
            else:
                start_time = 0.0
                end_time = 0.0 # Fallback, though rare

            downloaded_rows.append({
                'video_id': vid,
                'original_filename': filename,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'source_url': info['url'],
                'local_path': str(output_path.resolve())
            })
        else:
            failed_count += 1

    if failed_count > 0:
        logger.warning(f"Failed to download {failed_count} videos.")

    if not downloaded_rows:
        raise RuntimeError("No videos were successfully downloaded. Check network and data source.")

    # Create DataFrame
    df = pd.DataFrame(downloaded_rows)

    # Save metadata
    df.to_csv(METADATA_FILE, index=False)
    logger.info(f"Saved metadata to {METADATA_FILE}")

    return df

def main():
    """Entry point for the script."""
    logger.info("Starting fetch_original.py")
    try:
        df = fetch_original_clips()
        logger.info(f"Successfully fetched {len(df)} original clips.")
        logger.info(f"Metadata saved to: {METADATA_FILE}")
        logger.info("Fetch original clips completed.")
    except Exception as e:
        logger.critical(f"Fetch original clips failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()