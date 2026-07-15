"""
T032: Fetch Real Meeting Clips (Main Study)

Downloads meeting background frames/clips from the 'video-conference-backgrounds'
HuggingFace dataset. This task implements the data fetching logic for User Story 2.

Output:
    data/raw/meeting_clips/: Directory containing downloaded video/image files.
    data/raw/meeting_clips_manifest.json: Manifest with metadata for each downloaded item.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports if running as script
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from datasets import load_dataset
from PIL import Image
import io

# Constants
DATASET_NAME = "HuggingFaceM4/video-conference-backgrounds"
DATASET_SPLIT = "train"
MAX_ITEMS = 500  # Limit to match pilot study scale for initial fetch
OUTPUT_DIR = Path("data/raw/meeting_clips")
MANIFEST_PATH = OUTPUT_DIR / "meeting_clips_manifest.json"

def ensure_output_directory():
    """Create the output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_dataset_items(max_items: int = MAX_ITEMS) -> List[Dict[str, Any]]:
    """
    Download items from the HuggingFace dataset.

    Args:
        max_items: Maximum number of items to download.

    Returns:
        List of metadata dictionaries for downloaded items.
    """
    print(f"Loading dataset: {DATASET_NAME} (split: {DATASET_SPLIT})...")
    try:
        dataset = load_dataset(DATASET_NAME, split=DATASET_SPLIT)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        sys.exit(1)

    print(f"Dataset loaded. Total items: {len(dataset)}")
    print(f"Fetching first {max_items} items...")

    downloaded_items = []
    processed_count = 0

    # Iterate through the dataset
    for idx, item in enumerate(dataset):
        if processed_count >= max_items:
            break

        try:
            # Extract video frame or image based on dataset structure
            # The dataset typically contains 'video' or 'image' keys
            # We'll handle both cases
            if "video" in item:
                # If it's a video, extract frames (we'll take the first frame for now)
                video_data = item["video"]
                if isinstance(video_data, dict) and "bytes" in video_data:
                    # Decode video bytes to extract frames
                    # For simplicity, we'll save the video file directly if possible
                    # or extract a frame if we have the right library
                    video_bytes = video_data["bytes"]
                    filename = f"clip_{idx:05d}.mp4"
                    file_path = OUTPUT_DIR / filename

                    with open(file_path, "wb") as f:
                        f.write(video_bytes)

                    downloaded_items.append({
                        "id": idx,
                        "filename": filename,
                        "type": "video",
                        "source_index": idx,
                        "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    processed_count += 1
                    print(f"Downloaded video: {filename} ({processed_count}/{max_items})")
                elif isinstance(video_data, bytes):
                    filename = f"clip_{idx:05d}.mp4"
                    file_path = OUTPUT_DIR / filename
                    with open(file_path, "wb") as f:
                        f.write(video_data)
                    downloaded_items.append({
                        "id": idx,
                        "filename": filename,
                        "type": "video",
                        "source_index": idx,
                        "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    processed_count += 1
                    print(f"Downloaded video: {filename} ({processed_count}/{max_items})")
            elif "image" in item:
                # Handle image data
                image_data = item["image"]
                if isinstance(image_data, Image.Image):
                    filename = f"clip_{idx:05d}.png"
                    file_path = OUTPUT_DIR / filename
                    image_data.save(file_path)
                    downloaded_items.append({
                        "id": idx,
                        "filename": filename,
                        "type": "image",
                        "source_index": idx,
                        "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    processed_count += 1
                    print(f"Downloaded image: {filename} ({processed_count}/{max_items})")
                elif isinstance(image_data, dict) and "bytes" in image_data:
                    # Load from bytes
                    image_bytes = image_data["bytes"]
                    img = Image.open(io.BytesIO(image_bytes))
                    filename = f"clip_{idx:05d}.png"
                    file_path = OUTPUT_DIR / filename
                    img.save(file_path)
                    downloaded_items.append({
                        "id": idx,
                        "filename": filename,
                        "type": "image",
                        "source_index": idx,
                        "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    processed_count += 1
                    print(f"Downloaded image: {filename} ({processed_count}/{max_items})")
            else:
                # Skip items without valid video or image data
                print(f"Skipping item {idx}: no valid video or image data")

        except Exception as e:
            print(f"Error processing item {idx}: {e}")
            continue

    return downloaded_items

def save_manifest(items: List[Dict[str, Any]]):
    """Save the manifest of downloaded items."""
    manifest = {
        "dataset_name": DATASET_NAME,
        "split": DATASET_SPLIT,
        "total_downloaded": len(items),
        "items": items
    }

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest saved to: {MANIFEST_PATH}")

def main():
    """Main entry point for fetching meeting clips."""
    print("Starting T032: Fetch Real Meeting Clips (Main Study)")
    print("=" * 60)

    # Ensure output directory exists
    ensure_output_directory()

    # Check if we already have a manifest and skip if done
    if MANIFEST_PATH.exists():
        print(f"Manifest already exists at {MANIFEST_PATH}. Skipping download.")
        # Optionally, we could check if the files still exist
        # For now, we'll just skip
        return

    # Download items
    downloaded_items = download_dataset_items()

    if not downloaded_items:
        print("No items were downloaded. Check the dataset or logs.")
        sys.exit(1)

    # Save manifest
    save_manifest(downloaded_items)

    print("=" * 60)
    print(f"Completed T032: Successfully downloaded {len(downloaded_items)} items.")

if __name__ == "__main__":
    main()
