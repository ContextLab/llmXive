import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import ensure_directories, get_seed
import cv2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/raw/frame_extraction.log')
    ]
)
logger = logging.getLogger(__name__)

def extract_frames_from_video(
    video_path: Path,
    output_dir: Path,
    target_fps: int = 1,
    max_frames: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Extract frames from a single video file.

    Args:
        video_path: Path to the input video file.
        output_dir: Directory to save extracted frames.
        target_fps: Target frames per second to extract (default 1 to reduce data).
        max_frames: Maximum number of frames to extract (None for all).

    Returns:
        List of metadata dictionaries for extracted frames.
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30.0  # Default fallback

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = max(1, int(fps / target_fps))

    frames_extracted = []
    frame_count = 0
    extracted_count = 0

    logger.info(f"Processing {video_path.name}: {total_frames} total frames, extracting every {frame_interval} frames")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            if max_frames is not None and extracted_count >= max_frames:
                break

            frame_filename = f"{video_path.stem}_frame_{extracted_count:04d}.png"
            frame_path = output_dir / frame_filename

            # Ensure directory exists for the specific frame (though output_dir is flat here)
            frame_path.parent.mkdir(parents=True, exist_ok=True)

            success = cv2.imwrite(str(frame_path), frame)
            if not success:
                logger.error(f"Failed to write frame: {frame_path}")
                continue

            frames_extracted.append({
                "file_path": str(frame_path),
                "source_video": str(video_path),
                "frame_index": frame_count,
                "extracted_index": extracted_count,
                "timestamp": frame_count / fps
            })
            extracted_count += 1

        frame_count += 1

    cap.release()
    logger.info(f"Extracted {extracted_count} frames from {video_path.name}")
    return frames_extracted

def extract_frames_from_dataset(
    raw_data_dir: Path,
    output_dir: Path,
    file_pattern: str = "*.mp4",
    target_fps: int = 1,
    max_frames_per_video: Optional[int] = None
) -> Dict[str, Any]:
    """
    Scan a directory for video files and extract frames.

    Args:
        raw_data_dir: Directory containing raw video files (e.g., data/raw).
        output_dir: Directory to save extracted frames (e.g., data/raw/frames).
        file_pattern: Glob pattern for video files.
        target_fps: Frames per second to extract.
        max_frames_per_video: Max frames to extract per video.

    Returns:
        Manifest dictionary containing metadata for all extracted frames.
    """
    ensure_directories([output_dir])

    video_files = list(raw_data_dir.rglob(file_pattern))
    if not video_files:
        logger.warning(f"No video files found matching '{file_pattern}' in {raw_data_dir}")
        return {"files": [], "total_frames": 0, "videos_processed": 0}

    manifest = {
        "files": [],
        "total_frames": 0,
        "videos_processed": 0,
        "errors": []
    }

    for video_path in video_files:
        try:
            frames = extract_frames_from_video(
                video_path,
                output_dir,
                target_fps=target_fps,
                max_frames=max_frames_per_video
            )
            manifest["files"].extend(frames)
            manifest["videos_processed"] += 1
        except Exception as e:
            logger.error(f"Error processing {video_path}: {e}")
            manifest["errors"].append({
                "video": str(video_path),
                "error": str(e)
            })

    manifest["total_frames"] = len(manifest["files"])
    return manifest

def main():
    """Main entry point for frame extraction."""
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_data_dir = project_root / "data" / "raw"
    output_dir = project_root / "data" / "raw" / "frames"

    logger.info(f"Starting frame extraction from {raw_data_dir}")
    logger.info(f"Output directory: {output_dir}")

    # Ensure directories exist
    ensure_directories([raw_data_dir, output_dir])

    # Check if raw data exists
    if not raw_data_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_data_dir}")
        logger.error("Please run T011 (download.py) first to fetch the RAVDESS dataset.")
        sys.exit(1)

    # Check for video files
    video_files = list(raw_data_dir.rglob("*.mp4"))
    if not video_files:
        logger.error(f"No MP4 files found in {raw_data_dir}")
        logger.error("Please run T011 (download.py) first to fetch the RAVDESS dataset.")
        sys.exit(1)

    # Extract frames
    manifest = extract_frames_from_dataset(
        raw_data_dir=raw_data_dir,
        output_dir=output_dir,
        file_pattern="*.mp4",
        target_fps=1,  # Extract 1 frame per second to manage size
        max_frames_per_video=10  # Limit per video for initial run if needed, or None for all
    )

    # Save manifest
    manifest_path = project_root / "data" / "raw" / "frame_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Frame extraction complete.")
    logger.info(f"Total frames extracted: {manifest['total_frames']}")
    logger.info(f"Videos processed: {manifest['videos_processed']}")
    logger.info(f"Errors: {len(manifest['errors'])}")
    logger.info(f"Manifest saved to: {manifest_path}")

    if manifest['errors']:
        logger.warning("Some videos failed to process. Check logs for details.")

    return manifest

if __name__ == "__main__":
    main()
