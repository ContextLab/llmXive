"""
Dataset Downloader for DAVIS and YouTube-VOS video clips.

This module implements a robust, streaming-based data loader that fetches
real video clips from the Hugging Face Datasets repository. It strictly
adheres to the "fail loudly" policy: if the real data source is unavailable,
it raises an exception rather than generating synthetic data.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from datasets import load_dataset
    from datasets.exceptions import DatasetNotFoundError, ConnectionError as HFConnectionError
except ImportError:
    raise ImportError(
        "The 'datasets' library is required. Install it via: pip install datasets"
    )

# Import local project utilities
from config import ensure_directories, get_default_config
from utils.logger import get_logger
from data.models import VideoClip

logger = get_logger(__name__)

# Constants
DATASET_ID_DAVIS = "DAVIS"
DATASET_ID_YOUTUBE_VOS = "youtube-vos"
DEFAULT_SPLIT = "train"
STREAMING_MODE = True
MAX_CLIPS_TO_FETCH = 50  # Limit for CI/Testing to ensure it fits in time/memory

def fetch_davis_clips(
    split: str = DEFAULT_SPLIT,
    max_clips: int = MAX_CLIPS_TO_FETCH,
    output_dir: Optional[str] = None
) -> List[VideoClip]:
    """
    Fetches video clips from the DAVIS dataset using streaming.

    Args:
        split: The dataset split to load (e.g., 'train', 'val', 'test').
        max_clips: Maximum number of clips to fetch.
        output_dir: Directory to save the raw video files.

    Returns:
        A list of VideoClip dataclass instances.

    Raises:
        RuntimeError: If the dataset cannot be fetched or is unavailable.
        FileNotFoundError: If the dataset is not found.
    """
    logger.info(f"Fetching DAVIS dataset (split={split}, max_clips={max_clips})...")
    
    if output_dir is None:
        config = get_default_config()
        output_dir = config.raw_data_dir
    
    ensure_directories([output_dir])

    try:
        # Load dataset in streaming mode to avoid downloading the full 7GB+ at once
        dataset = load_dataset(
            DATASET_ID_DAVIS,
            split=split,
            streaming=STREAMING_MODE
        )
    except Exception as e:
        # Explicitly fail loudly if the source is unreachable
        raise RuntimeError(
            f"CRITICAL: Failed to fetch real DAVIS dataset from Hugging Face. "
            f"Source: {DATASET_ID_DAVIS}. Error: {str(e)}. "
            "The pipeline cannot proceed without real data. No synthetic fallback is allowed."
        ) from e

    clips: List[VideoClip] = []
    count = 0

    for idx, item in enumerate(dataset):
        if count >= max_clips:
            break

        # DAVIS dataset structure: {'video': bytes, 'mask': bytes, 'id': str, 'split': str}
        # We expect 'video' to be a path or bytes that can be saved.
        # In the HuggingFace DAVIS dataset, 'video' is often a path to the video file in the repo
        # or a byte stream depending on the specific dataset version.
        # We assume the standard 'DAVIS' dataset returns video paths or bytes.
        
        # Handle potential missing keys gracefully by failing loudly
        if 'video' not in item:
            raise RuntimeError(
                f"CRITICAL: Unexpected dataset structure in DAVIS. "
                f"Expected 'video' key, got keys: {list(item.keys())}. "
                "Cannot proceed without valid real data."
            )

        video_data = item['video']
        video_id = item.get('id', f"davis_{idx}")
        
        # Ensure video data is saved to disk
        video_filename = f"{video_id}.mp4"
        video_path = os.path.join(output_dir, video_filename)

        # If video_data is a path (local cache), copy it. 
        # If it's bytes (streamed), write it.
        # The datasets library often returns a path to the cached file if not streaming,
        # but with streaming=True, it might return a generator or direct bytes depending on the loader.
        # We handle the most common case: writing bytes or copying.
        
        if isinstance(video_data, bytes):
            with open(video_path, 'wb') as f:
                f.write(video_data)
        elif isinstance(video_data, str):
            # If it's a path (e.g. from a local cache or remote URL that was downloaded)
            # We treat it as a source file to copy if it exists locally, or download if URL.
            # For HuggingFace streaming, it's often a path to the cached file.
            if os.path.exists(video_data):
                import shutil
                shutil.copy(video_data, video_path)
            else:
                # Fallback: try to download if it's a URL (unlikely for standard DAVIS loader)
                raise RuntimeError(f"Video source path '{video_data}' does not exist.")
        else:
            raise RuntimeError(
                f"CRITICAL: Unsupported video data type {type(video_data)}. "
                "Expected bytes or str path."
            )

        # Create the VideoClip object
        clip = VideoClip(
            id=video_id,
            source=DATASET_ID_DAVIS,
            split=split,
            path=video_path,
            mask_path=None, # Mask handling is separate or optional for this specific task
            metadata={
                "original_id": item.get('id'),
                "resolution": item.get('resolution', "unknown")
            }
        )
        clips.append(clip)
        count += 1
        logger.debug(f"Saved clip {count}/{max_clips}: {video_filename}")

    logger.info(f"Successfully fetched {len(clips)} clips from DAVIS.")
    return clips

def fetch_youtube_vos_clips(
    split: str = DEFAULT_SPLIT,
    max_clips: int = MAX_CLIPS_TO_FETCH,
    output_dir: Optional[str] = None
) -> List[VideoClip]:
    """
    Fetches video clips from the YouTube-VOS dataset using streaming.

    Args:
        split: The dataset split to load.
        max_clips: Maximum number of clips to fetch.
        output_dir: Directory to save the raw video files.

    Returns:
        A list of VideoClip dataclass instances.

    Raises:
        RuntimeError: If the dataset cannot be fetched.
    """
    logger.info(f"Fetching YouTube-VOS dataset (split={split}, max_clips={max_clips})...")

    if output_dir is None:
        config = get_default_config()
        output_dir = config.raw_data_dir
    
    ensure_directories([output_dir])

    try:
        # YouTube-VOS dataset on HF
        dataset = load_dataset(
            DATASET_ID_YOUTUBE_VOS,
            split=split,
            streaming=STREAMING_MODE
        )
    except Exception as e:
        raise RuntimeError(
            f"CRITICAL: Failed to fetch real YouTube-VOS dataset. "
            f"Source: {DATASET_ID_YOUTUBE_VOS}. Error: {str(e)}. "
            "No synthetic fallback allowed."
        ) from e

    clips: List[VideoClip] = []
    count = 0

    for idx, item in enumerate(dataset):
        if count >= max_clips:
            break

        if 'video' not in item:
            raise RuntimeError(
                f"CRITICAL: Unexpected YouTube-VOS structure. Expected 'video' key."
            )

        video_data = item['video']
        video_id = item.get('id', f"ytvos_{idx}")
        video_filename = f"{video_id}.mp4"
        video_path = os.path.join(output_dir, video_filename)

        if isinstance(video_data, bytes):
            with open(video_path, 'wb') as f:
                f.write(video_data)
        elif isinstance(video_data, str):
            if os.path.exists(video_data):
                import shutil
                shutil.copy(video_data, video_path)
            else:
                raise RuntimeError(f"Video source path '{video_data}' does not exist.")
        else:
            raise RuntimeError(f"Unsupported video data type {type(video_data)}.")

        clip = VideoClip(
            id=video_id,
            source=DATASET_ID_YOUTUBE_VOS,
            split=split,
            path=video_path,
            mask_path=None,
            metadata={"original_id": item.get('id')}
        )
        clips.append(clip)
        count += 1

    logger.info(f"Successfully fetched {len(clips)} clips from YouTube-VOS.")
    return clips

def download_dataset(
    dataset_name: str = DATASET_ID_DAVIS,
    split: str = DEFAULT_SPLIT,
    max_clips: int = MAX_CLIPS_TO_FETCH,
    output_dir: Optional[str] = None
) -> List[VideoClip]:
    """
    Main entry point to download a specific dataset.

    Args:
        dataset_name: 'DAVIS' or 'YouTube-VOS'.
        split: Dataset split.
        max_clips: Max clips to download.
        output_dir: Output directory for raw data.

    Returns:
        List of VideoClip objects.
    """
    if dataset_name == DATASET_ID_DAVIS:
        return fetch_davis_clips(split, max_clips, output_dir)
    elif dataset_name == DATASET_ID_YOUTUBE_VOS:
        return fetch_youtube_vos_clips(split, max_clips, output_dir)
    else:
        raise ValueError(f"Unsupported dataset: {dataset_name}. Choose 'DAVIS' or 'YouTube-VOS'.")

def main():
    """
    CLI entry point to download the dataset.
    Usage: python -m code.data.downloader [DAVIS|YouTube-VOS] [split] [max_clips]
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m code.data.downloader <dataset_name> [split] [max_clips]")
        print("Example: python -m code.data.downloader DAVIS train 10")
        sys.exit(1)

    dataset_name = sys.argv[1]
    split = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SPLIT
    max_clips = int(sys.argv[3]) if len(sys.argv) > 3 else MAX_CLIPS_TO_FETCH

    try:
        clips = download_dataset(dataset_name, split, max_clips)
        print(f"Downloaded {len(clips)} clips to {get_default_config().raw_data_dir}")
    except RuntimeError as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()