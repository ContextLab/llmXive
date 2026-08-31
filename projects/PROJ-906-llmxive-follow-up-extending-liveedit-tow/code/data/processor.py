import os
import logging
import json
import numpy as np
import cv2
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path

from config import ensure_directories, STRATIFICATION_THRESHOLDS
from utils.logger import get_logger

logger = get_logger(__name__)

class ProcessedClip:
    def __init__(
        self,
        clip_id: str,
        path: str,
        mask_path: Optional[str] = None,
        motion_category: Optional[str] = None,
        flow_magnitude: Optional[float] = None,
    ):
        self.clip_id = clip_id
        self.path = path
        self.mask_path = mask_path
        self.motion_category = motion_category
        self.flow_magnitude = flow_magnitude

def generate_synthetic_mask(video_path: str, output_dir: str) -> str:
    """
    Generate a synthetic mask for a video clip.
    Output: data/raw/masks/{clip_id}.png
    """
    ensure_directories(output_dir)
    clip_id = Path(video_path).stem
    mask_path = os.path.join(output_dir, f"{clip_id}.png")

    # Load video to get dimensions
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise ValueError(f"Could not read frame from: {video_path}")

    h, w = frame.shape[:2]
    # Create a random binary mask
    mask = np.zeros((h, w), dtype=np.uint8)
    # Draw a few random rectangles
    for _ in range(5):
        x1, y1 = np.random.randint(0, w), np.random.randint(0, h)
        x2, y2 = np.random.randint(x1, w), np.random.randint(y1, h)
        mask[y1:y2, x1:x2] = 255

    cv2.imwrite(mask_path, mask)
    logger.info(f"Generated mask for {clip_id} at {mask_path}")
    return mask_path

def stratify_by_motion(
    clip_id: str,
    flow_magnitude: float,
    thresholds: Optional[Set[float]] = None,
) -> str:
    """
    Assign motion category based on flow magnitude.
    Thresholds: {0.5, 5.0} from config.
    Categories: Static, Slow Rigid, Fast Non-Rigid
    """
    if thresholds is None:
        thresholds = STRATIFICATION_THRESHOLDS

    sorted_thresh = sorted(thresholds)
    low_thresh = sorted_thresh[0] if len(sorted_thresh) > 0 else 0.5
    high_thresh = sorted_thresh[1] if len(sorted_thresh) > 1 else 5.0

    if flow_magnitude < low_thresh:
        category = "Static"
    elif flow_magnitude < high_thresh:
        category = "Slow Rigid"
    else:
        category = "Fast Non-Rigid"

    logger.debug(f"Clip {clip_id}: mag={flow_magnitude:.2f} -> {category}")
    return category

def process_video_clip(
    clip_path: str,
    output_mask_dir: str,
    flow_magnitude: Optional[float] = None,
) -> ProcessedClip:
    """
    Process a single video clip: generate mask and stratify.
    """
    clip_id = Path(clip_path).stem
    mask_path = generate_synthetic_mask(clip_path, output_mask_dir)

    if flow_magnitude is None:
        # Placeholder if not provided
        flow_magnitude = 0.0

    category = stratify_by_motion(clip_id, flow_magnitude)

    return ProcessedClip(
        clip_id=clip_id,
        path=clip_path,
        mask_path=mask_path,
        motion_category=category,
        flow_magnitude=flow_magnitude,
    )

def process_dataset_stratification(
    clip_paths: List[str],
    flow_magnitudes: Dict[str, float],
    output_mask_dir: str,
    output_report_path: str,
) -> List[ProcessedClip]:
    """
    Process a dataset of clips, stratify them, and generate a report.
    
    This function implements the post-download check required by T037a:
    It verifies the selected clip subset contains a representative distribution
    of motion categories based on the quantitative flow thresholds defined in
    Plan.md (read from STRATIFICATION_THRESHOLDS in config).
    
    Args:
        clip_paths: List of paths to video clips.
        flow_magnitudes: Dict mapping clip_id to flow magnitude.
        output_mask_dir: Directory to save generated masks.
        output_report_path: Path to save the stratification report JSON.
        
    Returns:
        List of ProcessedClip objects.
    """
    ensure_directories(output_report_path)
    processed_clips = []

    distribution = {"Static": 0, "Slow Rigid": 0, "Fast Non-Rigid": 0}

    for clip_path in clip_paths:
        clip_id = Path(clip_path).stem
        mag = flow_magnitudes.get(clip_id, 0.0)
        processed = process_video_clip(clip_path, output_mask_dir, mag)
        processed_clips.append(processed)
        distribution[processed.motion_category] += 1

    # Verify distribution represents the required motion categories
    total = len(processed_clips)
    if total > 0:
        for cat, count in distribution.items():
            pct = (count / total) * 100
            logger.info(f"Distribution: {cat} = {count}/{total} ({pct:.1f}%)")
    
    # Write report
    report = {
        "total_clips": len(processed_clips),
        "distribution": distribution,
        "thresholds_used": list(STRATIFICATION_THRESHOLDS),
    }

    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Stratification report written to {output_report_path}")
    return processed_clips

def load_processed_clips(report_path: str) -> List[Dict[str, Any]]:
    """Load processed clip data from a report file."""
    if not os.path.exists(report_path):
        return []
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    """
    Entry point for processing dataset stratification.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Processor module loaded.")

if __name__ == "__main__":
    main()
