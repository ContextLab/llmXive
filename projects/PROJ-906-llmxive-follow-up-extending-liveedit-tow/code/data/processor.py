import os
import logging
import json
import numpy as np
import cv2
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from config import ensure_directories, get_default_config, STRATIFICATION_THRESHOLDS
from utils.logger import get_logger
from data.models import VideoClip

logger = get_logger("processor")

@dataclass
class ProcessedClip:
    clip_id: str
    path: str
    motion_category: str
    flow_magnitude: float
    mask: Optional[np.ndarray] = None
    frames: List[np.ndarray] = field(default_factory=list)

def generate_synthetic_mask(
    shape: Tuple[int, int],
    center: Tuple[int, int],
    radius: int,
    softness: float = 0.5
) -> np.ndarray:
    """
    Generate a soft circular mask for editing regions.
    
    Args:
        shape: (height, width) of the mask
        center: (x, y) center of the circle
        radius: radius of the circle
        softness: falloff factor for soft edges
    
    Returns:
        np.ndarray: Float mask values in [0, 1]
    """
    h, w = shape
    y, x = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    mask = np.clip(1.0 - (dist_from_center - radius) / (radius * softness), 0, 1)
    mask = np.clip(mask, 0, 1)
    return mask

def stratify_by_motion(
    flow_magnitude: float,
    thresholds: Optional[Set[float]] = None
) -> str:
    """
    Categorize a clip based on its mean optical flow magnitude.
    
    Categories:
        - Static: magnitude < low_threshold (0.5)
        - Slow Rigid: low_threshold <= magnitude < high_threshold (5.0)
        - Fast Non-Rigid: magnitude >= high_threshold
    
    Args:
        flow_magnitude: Mean magnitude of the optical flow field
        thresholds: Set of thresholds {low, high}. Defaults to STRATIFICATION_THRESHOLDS.
    
    Returns:
        str: Motion category label
    """
    if thresholds is None:
        thresholds = STRATIFICATION_THRESHOLDS
    
    # Sort thresholds to ensure order
    sorted_thresh = sorted(list(thresholds))
    if len(sorted_thresh) < 2:
        # Fallback if config is malformed
        low, high = 0.5, 5.0
    else:
        low, high = sorted_thresh[0], sorted_thresh[1]
    
    if flow_magnitude < low:
        return "Static"
    elif flow_magnitude < high:
        return "Slow Rigid"
    else:
        return "Fast Non-Rigid"

def process_video_clip(
    clip_path: str,
    flow_field: Optional[np.ndarray] = None
) -> ProcessedClip:
    """
    Process a single video clip: load frames, compute flow if missing,
    and assign a motion category.
    
    Args:
        clip_path: Path to the video file
        flow_field: Pre-computed optical flow field (optional)
    
    Returns:
        ProcessedClip: Dataclass with processed metadata
    """
    cap = cv2.VideoCapture(clip_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {clip_path}")
    
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    
    if not frames:
        raise ValueError(f"No frames found in video: {clip_path}")
    
    # Compute flow magnitude if not provided
    if flow_field is None and len(frames) >= 2:
        # Simple Farneback flow for magnitude estimation
        prev_gray = cv2.cvtColor(frames[0], cv2.COLOR_RGB2GRAY)
        curr_gray = cv2.cvtColor(frames[1], cv2.COLOR_RGB2GRAY)
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        magnitude = cv2.magnitude(flow[:,:,0], flow[:,:,1])
        mean_magnitude = float(np.mean(magnitude))
    elif flow_field is not None:
        magnitude = cv2.magnitude(flow_field[:,:,0], flow_field[:,:,1])
        mean_magnitude = float(np.mean(magnitude))
    else:
        # Fallback for single frame or missing flow
        mean_magnitude = 0.0
    
    category = stratify_by_motion(mean_magnitude)
    
    return ProcessedClip(
        clip_id=os.path.splitext(os.path.basename(clip_path))[0],
        path=clip_path,
        motion_category=category,
        flow_magnitude=mean_magnitude,
        frames=frames
    )

def process_dataset_stratification(
    clips: List[VideoClip],
    target_count: int = 50,
    min_per_category: int = 5
) -> Tuple[List[VideoClip], Dict[str, Any]]:
    """
    Stratify a dataset to ensure representative distribution of motion categories.
    
    Strategy:
        1. Group clips by motion category.
        2. Check if each category meets the minimum threshold.
        3. If a category is under-represented, attempt to fetch more (simulated by
           returning the request for additional data).
        4. If the dataset is exhausted and distribution is still skewed, log a WARNING
           and proceed, recording the imbalance.
    
    Args:
        clips: List of VideoClip objects to stratify
        target_count: Target number of clips (default 50)
        min_per_category: Minimum clips required per category (default 5)
    
    Returns:
        Tuple[List[VideoClip], Dict[str, Any]]:
            - Selected clips list
            - Stratification report dict
    """
    # Group by category
    categories: Dict[str, List[VideoClip]] = {
        "Static": [],
        "Slow Rigid": [],
        "Fast Non-Rigid": []
    }
    
    for clip in clips:
        cat = stratify_by_motion(clip.flow_magnitude)
        categories[cat].append(clip)
    
    # Analyze distribution
    distribution = {cat: len(lst) for cat, lst in categories.items()}
    total_available = sum(distribution.values())
    
    selected_clips: List[VideoClip] = []
    imbalance_detected = False
    warnings: List[str] = []
    
    # Check minimum thresholds
    for cat, count in distribution.items():
        if count < min_per_category:
            imbalance_detected = True
            warnings.append(
                f"Category '{cat}' has only {count} clips (min: {min_per_category}). "
                "Distribution is skewed."
            )
    
    # Select clips to meet target, prioritizing under-represented categories
    # Simple stratified sampling: take min(target/3, available) from each, then fill remainder
    base_per_cat = max(1, target_count // 3)
    
    for cat in ["Static", "Slow Rigid", "Fast Non-Rigid"]:
        available = categories[cat]
        take = min(base_per_cat, len(available))
        selected_clips.extend(available[:take])
    
    # Fill remaining spots if needed
    remaining = target_count - len(selected_clips)
    if remaining > 0:
        # Collect remaining available clips
        remaining_pool = []
        for cat in categories:
            already_taken = set(c.clip_id for c in selected_clips if c.motion_category == cat)
            remaining_pool.extend([c for c in categories[cat] if c.clip_id not in already_taken])
        
        # Take up to 'remaining' from the pool
        selected_clips.extend(remaining_pool[:remaining])
    
    # Final distribution check
    final_distribution = {}
    for cat in ["Static", "Slow Rigid", "Fast Non-Rigid"]:
        count = sum(1 for c in selected_clips if c.motion_category == cat)
        final_distribution[cat] = count
    
    report = {
        "target_count": target_count,
        "actual_count": len(selected_clips),
        "initial_distribution": distribution,
        "final_distribution": final_distribution,
        "total_available": total_available,
        "imbalance_detected": imbalance_detected,
        "warnings": warnings
    }
    
    if imbalance_detected:
        logger.warning("Stratification imbalance detected. Proceeding with available data.")
        for w in warnings:
            logger.warning(w)
    
    return selected_clips, report

def main():
    """
    CLI entry point for dataset stratification validation.
    Reads processed clips from data/flow/magnitudes.json (or similar),
    stratifies them, and writes the report to data/metrics/stratification_report.json.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Stratify dataset for motion categories")
    parser.add_argument("--input", type=str, default="data/flow/magnitudes.json",
                        help="Path to input flow magnitudes JSON")
    parser.add_argument("--output", type=str, default="data/metrics/stratification_report.json",
                        help="Path to output stratification report")
    parser.add_argument("--target", type=int, default=50,
                        help="Target number of clips")
    parser.add_argument("--min-per-cat", type=int, default=5,
                        help="Minimum clips per category")
    
    args = parser.parse_args()
    
    # Load input data
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    # Convert to VideoClip objects
    clips = []
    for item in data.get("magnitudes", []):
        clip = VideoClip(
            id=item.get("clip_id", "unknown"),
            path=item.get("path", ""),
            motion_category="",
            flow_field=None,
            mask=None,
            flow_magnitude=item.get("magnitude", 0.0)
        )
        clips.append(clip)
    
    # Stratify
    selected, report = process_dataset_stratification(
        clips, 
        target_count=args.target, 
        min_per_category=args.min_per_cat
    )
    
    # Write report
    ensure_directories(args.output)
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Stratification complete. Report written to {args.output}")
    logger.info(f"Selected {len(selected)} clips. Imbalance: {report['imbalance_detected']}")

if __name__ == "__main__":
    main()
