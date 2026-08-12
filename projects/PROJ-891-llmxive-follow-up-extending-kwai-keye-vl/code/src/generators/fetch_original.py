"""
Fetch Original Unmodified ActivityNet Captions clips for the control group.

This script retrieves a representative subset of source clips from the
ActivityNet Captions dataset using streaming to avoid loading the full
dataset into memory. It saves the raw video files to `data/raw/original/`
and generates a metadata CSV mapping video IDs to timestamps.

Requirements:
    - huggingface_hub
    - requests (for video download)
    - pandas
    - tqdm

Usage:
    python code/src/generators/fetch_original.py
"""
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from huggingface_hub import load_dataset
from tqdm import tqdm

# Constants
DATASET_ID = "ActivityNet/activitynet-captions"
SPLIT = "train"
MAX_SAMPLES = 100  # Representative subset size
OUTPUT_DIR = Path("data/raw/original")
METADATA_CSV = OUTPUT_DIR / "metadata.csv"
TIMEOUT_SECONDS = 600  # 10 minutes per video download attempt

def ensure_output_dir():
    """Create the output directory if it does not exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_video(url, dest_path):
    """
    Download a video file from a URL to a local path.

    Args:
        url (str): The source URL.
        dest_path (Path): The destination file path.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        response = requests.get(url, stream=True, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte

        with open(dest_path, 'wb') as f, tqdm(
            desc=dest_path.name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)
                    bar.update(len(chunk))
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error saving {dest_path}: {e}", file=sys.stderr)
        return False

def fetch_original_clips():
    """
    Main execution function to fetch original ActivityNet clips.
    """
    ensure_output_dir()

    print(f"Loading dataset {DATASET_ID} (split={SPLIT}) in streaming mode...")
    try:
        dataset = load_dataset(DATASET_ID, split=SPLIT, streaming=True)
    except Exception as e:
        print(f"Failed to load dataset from Hugging Face: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching up to {MAX_SAMPLES} original clips...")
    
    metadata_records = []
    count = 0
    skipped = 0
    failed_downloads = 0

    for item in dataset:
        if count >= MAX_SAMPLES:
            break

        video_id = item.get('video_id')
        if not video_id:
            skipped += 1
            continue

        # ActivityNet Captions format usually has 'url' or 'video_url'
        # depending on the specific revision, but standard is 'url' for video
        video_url = item.get('url') or item.get('video_url')
        
        if not video_url:
            print(f"Skipping {video_id}: No video URL found.", file=sys.stderr)
            skipped += 1
            continue

        # Determine file extension from URL or default to .mp4
        ext = os.path.splitext(video_url)[1] or '.mp4'
        filename = f"{video_id}{ext}"
        dest_path = OUTPUT_DIR / filename

        # Skip if already exists to avoid re-downloading
        if dest_path.exists():
            print(f"Skipping {video_id}: Already exists.")
            # Still record metadata if not present, but for this logic we assume
            # we are building the metadata from the successful download run.
            # We will re-scan later or just add it now.
            # To be safe and consistent with the "fetch" logic, we record it.
            # Check timestamps in item
            timestamps = item.get('timestamps', [])
            # ActivityNet often has a list of timestamps for multiple events.
            # We take the first one or the range if available.
            if timestamps:
                start_t = timestamps[0][0] if isinstance(timestamps[0], (list, tuple)) else timestamps[0]
                end_t = timestamps[0][1] if isinstance(timestamps[0], (list, tuple)) else timestamps[1]
            else:
                start_t, end_t = 0.0, 0.0

            metadata_records.append({
                'video_id': video_id,
                'filename': filename,
                'start_time': start_t,
                'end_time': end_t,
                'source_url': video_url,
                'status': 'exists'
            })
            count += 1
            continue

        print(f"Downloading: {video_id} ({video_url})")
        success = download_video(video_url, dest_path)

        if success:
            # Extract timestamps
            timestamps = item.get('timestamps', [])
            if timestamps:
                # Handle list of [start, end] pairs
                first_event = timestamps[0]
                start_t = float(first_event[0])
                end_t = float(first_event[1])
            else:
                start_t, end_t = 0.0, 0.0

            metadata_records.append({
                'video_id': video_id,
                'filename': filename,
                'start_time': start_t,
                'end_time': end_t,
                'source_url': video_url,
                'status': 'downloaded'
            })
            count += 1
        else:
            failed_downloads += 1
            # Remove partial file if exists
            if dest_path.exists():
                dest_path.unlink()

    if count == 0:
        print("ERROR: No videos were successfully fetched.", file=sys.stderr)
        sys.exit(1)

    # Save metadata
    df = pd.DataFrame(metadata_records)
    df.to_csv(METADATA_CSV, index=False)
    print(f"\nSuccess! Processed {count} videos.")
    print(f"Skipped (no URL): {skipped}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Metadata saved to: {METADATA_CSV}")

if __name__ == "__main__":
    fetch_original_clips()
