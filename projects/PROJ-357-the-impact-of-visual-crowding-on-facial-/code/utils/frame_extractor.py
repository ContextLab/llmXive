"""
Frame extraction utility for RAVDESS dataset.

Extracts frames from video files in the RAVDESS dataset and saves them
to the specified output directory with metadata tracking.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure parent directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import cv2
except ImportError:
    print("ERROR: OpenCV (cv2) is required. Install with: pip install opencv-python")
    sys.exit(1)

from config import ensure_directories, get_env_config

# Setup logging
LOG_DIR = Path("data/raw")
LOG_FILE = LOG_DIR / "frame_extraction.log"
ERROR_LOG = Path("data/interim") / "generation_errors.log"

def setup_logging():
    """Configure logging to file and console."""
    ensure_directories([LOG_DIR, ERROR_LOG.parent])
    
    # Create handlers
    file_handler = logging.FileHandler(LOG_FILE, mode='w')
    console_handler = logging.StreamHandler()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger(__name__)

def extract_frames_from_video(
    video_path: Path,
    output_dir: Path,
    frame_interval: int = 30,
    max_frames: Optional[int] = None
) -> Dict[str, Any]:
    """
    Extract frames from a single video file.
    
    Args:
        video_path: Path to the video file
        output_dir: Directory to save extracted frames
        frame_interval: Extract every Nth frame (default: 30)
        max_frames: Maximum number of frames to extract (optional)
        
    Returns:
        Dictionary with extraction metadata
    """
    logger = logging.getLogger(__name__)
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return {"status": "error", "reason": "file_not_found", "video": str(video_path)}
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return {"status": "error", "reason": "cannot_open", "video": str(video_path)}
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        extracted_count = 0
        frame_paths = []
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Extract every Nth frame
            if frame_idx % frame_interval == 0:
                if max_frames and extracted_count >= max_frames:
                    break
                
                # Create frame filename with metadata
                frame_filename = f"{video_path.stem}_f{frame_idx:06d}.jpg"
                frame_path = output_dir / frame_filename
                
                cv2.imwrite(str(frame_path), frame)
                frame_paths.append(str(frame_path))
                extracted_count += 1
            
            frame_idx += 1
        
        cap.release()
        
        logger.info(f"Extracted {extracted_count} frames from {video_path.name} "
                   f"(total {total_frames} frames, {fps} fps)")
        
        return {
            "status": "success",
            "video": str(video_path),
            "output_dir": str(output_dir),
            "total_frames": total_frames,
            "fps": fps,
            "dimensions": {"width": width, "height": height},
            "extracted_count": extracted_count,
            "frame_interval": frame_interval,
            "frame_paths": frame_paths
        }
        
    except Exception as e:
        logger.error(f"Error processing {video_path}: {str(e)}")
        return {"status": "error", "reason": str(e), "video": str(video_path)}

def extract_frames_from_dataset(
    dataset_dir: Path,
    output_base_dir: Path,
    frame_interval: int = 30,
    max_frames_per_video: Optional[int] = None,
    video_extensions: List[str] = None
) -> Dict[str, Any]:
    """
    Extract frames from all videos in a dataset directory.
    
    Args:
        dataset_dir: Root directory containing video files
        output_base_dir: Base directory for extracted frames
        frame_interval: Extract every Nth frame
        max_frames_per_video: Maximum frames per video
        video_extensions: List of video extensions to process
        
    Returns:
        Summary dictionary with overall extraction results
    """
    logger = logging.getLogger(__name__)
    dataset_dir = Path(dataset_dir)
    output_base_dir = Path(output_base_dir)
    
    if video_extensions is None:
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    
    # Find all video files
    video_files = []
    for ext in video_extensions:
        video_files.extend(list(dataset_dir.rglob(f"*{ext}")))
        video_files.extend(list(dataset_dir.rglob(f"*{ext.upper()}")))
    
    if not video_files:
        logger.warning(f"No video files found in {dataset_dir}")
        return {
            "status": "warning",
            "reason": "no_videos_found",
            "dataset_dir": str(dataset_dir),
            "total_videos": 0,
            "processed": 0,
            "success": 0,
            "error": 0
        }
    
    logger.info(f"Found {len(video_files)} video files to process")
    
    results = {
        "status": "success",
        "dataset_dir": str(dataset_dir),
        "output_base_dir": str(output_base_dir),
        "total_videos": len(video_files),
        "processed": 0,
        "success": 0,
        "error": 0,
        "details": []
    }
    
    error_count = 0
    
    for video_path in video_files:
        # Create output subdirectory mirroring video structure
        relative_path = video_path.relative_to(dataset_dir)
        output_subdir = output_base_dir / relative_path.parent
        output_subdir.mkdir(parents=True, exist_ok=True)
        
        result = extract_frames_from_video(
            video_path,
            output_subdir,
            frame_interval,
            max_frames_per_video
        )
        
        results["processed"] += 1
        if result["status"] == "success":
            results["success"] += 1
        else:
            results["error"] += 1
            error_count += 1
            # Log error to error log
            with open(ERROR_LOG, 'a') as f:
                f.write(f"ERROR: Frame extraction failed for {video_path}: {result.get('reason', 'unknown')}\n")
        
        results["details"].append(result)
    
    logger.info(f"Extraction complete: {results['success']}/{results['total_videos']} videos processed successfully")
    
    if error_count > 0:
        logger.warning(f"{error_count} videos failed to process")
    
    return results

def main():
    """Main entry point for frame extraction."""
    logger = setup_logging()
    logger.info("Starting frame extraction from RAVDESS dataset")
    
    # Get configuration
    config = get_env_config()
    dataset_dir = Path(config.get('RAVDESS_DIR', 'data/raw/RAVDESS'))
    output_dir = Path("data/raw/frames")
    frame_interval = config.get('FRAME_INTERVAL', 30)
    max_frames = config.get('MAX_FRAMES_PER_VIDEO', None)
    
    logger.info(f"Dataset directory: {dataset_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Frame interval: {frame_interval}")
    if max_frames:
        logger.info(f"Max frames per video: {max_frames}")
    
    # Check if dataset exists
    if not dataset_dir.exists():
        logger.error(f"Dataset directory not found: {dataset_dir}")
        logger.error("Please run download.py first to fetch the RAVDESS dataset")
        sys.exit(1)
    
    # Extract frames
    results = extract_frames_from_dataset(
        dataset_dir,
        output_dir,
        frame_interval,
        max_frames
    )
    
    # Save results summary
    summary_path = output_dir / "extraction_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Summary saved to {summary_path}")
    
    if results["status"] == "error":
        sys.exit(1)
    
    logger.info("Frame extraction completed successfully")

if __name__ == "__main__":
    main()
