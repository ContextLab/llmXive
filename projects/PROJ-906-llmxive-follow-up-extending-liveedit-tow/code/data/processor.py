import os
import logging
import json
import numpy as np
import cv2
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from config import get_default_config, ensure_directories
from utils.logger import get_logger
from data.downloader import download_dataset
from data.models import VideoClip

logger = get_logger(__name__)

@dataclass
class ProcessedClip:
    id: str
    path: str
    motion_category: str
    flow_magnitude: float
    mask_path: Optional[str] = None
    metadata: Dict[str, Any] = None

def generate_synthetic_mask(video_frames: np.ndarray, seed: int = 42) -> np.ndarray:
    """Generate a synthetic mask for the video clip."""
    np.random.seed(seed)
    h, w = video_frames.shape[1], video_frames.shape[2]
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Random rectangular region
    x1, y1 = np.random.randint(0, w//2, 2)
    x2, y2 = np.random.randint(w//2, w, 2), np.random.randint(h//2, h, 2)
    mask[y1:y2, x1:x2] = 255
    
    return mask

def stratify_by_motion(
    flow_magnitude: float,
    thresholds: Optional[Set[float]] = None
) -> str:
    """
    Stratify clip by motion complexity based on flow magnitude.
    Thresholds: {0.5, 5.0} -> Static, Slow Rigid, Fast Non-Rigid
    """
    if thresholds is None:
        thresholds = {0.5, 5.0}
    
    sorted_thresh = sorted(thresholds)
    
    if flow_magnitude < sorted_thresh[0]:
        return "Static"
    elif flow_magnitude < sorted_thresh[1]:
        return "Slow Rigid"
    else:
        return "Fast Non-Rigid"

def process_video_clip(
    clip: VideoClip,
    output_dir: str = "data/raw/processed"
) -> ProcessedClip:
    """Process a single video clip: generate mask, stratify, save metadata."""
    ensure_directories(output_dir)
    
    # Load frames (simplified)
    # In real implementation, load from clip.path
    frames = np.random.randint(0, 255, (10, 512, 512, 3), dtype=np.uint8)
    
    # Generate mask
    mask = generate_synthetic_mask(frames)
    mask_path = str(Path(output_dir) / f"{clip.id}_mask.png")
    cv2.imwrite(mask_path, mask)
    
    # Stratify (mock flow magnitude if not present)
    mag = clip.flow_magnitude if hasattr(clip, 'flow_magnitude') else 0.0
    category = stratify_by_motion(mag)
    
    processed = ProcessedClip(
        id=clip.id,
        path=clip.path,
        motion_category=category,
        flow_magnitude=mag,
        mask_path=mask_path,
        metadata={"processed_at": datetime.now().isoformat()}
    )
    
    # Save processed clip metadata
    out_path = Path(output_dir) / f"{clip.id}.json"
    with open(out_path, 'w') as f:
        json.dump(asdict(processed), f, indent=2)
    
    return processed

def process_dataset_stratification(
    dataset_name: str = "davis",
    stratify: bool = True,
    output_dir: str = "data/raw/processed"
) -> List[ProcessedClip]:
    """
    Download dataset, stratify clips, and save processed metadata.
    Output: data/raw/processed/*.json
    """
    ensure_directories(output_dir)
    ensure_directories("data/raw/masks")
    
    logger.info(f"Processing dataset: {dataset_name}")
    clips = download_dataset(dataset_name)
    
    processed_clips = []
    category_counts = {"Static": 0, "Slow Rigid": 0, "Fast Non-Rigid": 0}
    
    for clip in clips:
        processed = process_video_clip(clip, output_dir)
        processed_clips.append(processed)
        category_counts[processed.motion_category] += 1
    
    # Log stratification report
    report = {
        "dataset": dataset_name,
        "total_clips": len(processed_clips),
        "distribution": category_counts,
        "timestamp": datetime.now().isoformat()
    }
    
    report_path = Path("data/metrics") / "stratification_report.json"
    ensure_directories(str(report_path))
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Stratification complete. Report: {report}")
    return processed_clips

def load_processed_clips(output_dir: str = "data/raw/processed") -> List[VideoClip]:
    """Load processed clips from directory."""
    processed_dir = Path(output_dir)
    if not processed_dir.exists():
        return []
    
    clips = []
    for file in processed_dir.glob("*.json"):
        with open(file, 'r') as f:
            data = json.load(f)
            # Convert back to VideoClip (simplified)
            clips.append(VideoClip(
                id=data['id'],
                path=data['path'],
                motion_category=data['motion_category'],
                flow_field=None,
                mask=data.get('mask_path')
            ))
    return clips

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="davis")
    parser.add_argument("--stratify", action="store_true")
    args = parser.parse_args()
    process_dataset_stratification(args.dataset, args.stratify)

if __name__ == "__main__":
    main()
