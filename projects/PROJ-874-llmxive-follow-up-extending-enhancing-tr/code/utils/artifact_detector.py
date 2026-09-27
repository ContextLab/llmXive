import os
import sys
import logging
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Import existing utilities from the project API surface
from code.utils.video import extract_frames, get_video_metadata
from code.config import get_results_dir, get_config

logger = logging.getLogger(__name__)

# Configuration for artifact detection
# Threshold for detecting tearing (gradient magnitude difference)
TEARING_THRESHOLD = 50.0
# Minimum number of consecutive bad lines to consider a tear
MIN_TEAR_LINES = 5

def detect_tearing_artifacts(frame: np.ndarray, threshold: float = TEARING_THRESHOLD) -> Tuple[bool, List[int]]:
    """
    Detect tearing artifacts in a single frame.
    
    Tearing is detected by finding horizontal lines where there is a sudden
    discontinuity in pixel values (gradient magnitude) that exceeds the threshold.
    This often happens when 3D drift causes severe misalignment during warping.
    
    Args:
        frame: Input frame as numpy array (H, W, C) or (H, W)
        threshold: Gradient magnitude threshold for tear detection
        
    Returns:
        Tuple of (has_tearing, list of row indices where tearing was detected)
    """
    # Convert to grayscale if necessary
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame.copy()
        
    # Convert to float for gradient calculation
    gray_float = gray.astype(np.float32)
    
    # Calculate vertical gradient (difference between consecutive rows)
    # This will highlight horizontal discontinuities (tearing)
    vertical_diff = np.abs(np.diff(gray_float, axis=0))
    
    # Find rows where the gradient magnitude exceeds the threshold
    # We look for the maximum gradient in each column and then check if
    # enough columns exceed the threshold at the same row
    row_max_gradients = np.max(vertical_diff, axis=1)
    
    # Identify rows with significant gradients
    bad_rows = np.where(row_max_gradients > threshold)[0].tolist()
    
    # Filter for consecutive bad rows (tearing usually spans multiple lines)
    if len(bad_rows) < MIN_TEAR_LINES:
        return False, []
        
    # Group consecutive rows
    tear_locations = []
    if bad_rows:
        current_group = [bad_rows[0]]
        for i in range(1, len(bad_rows)):
            if bad_rows[i] == bad_rows[i-1] + 1:
                current_group.append(bad_rows[i])
            else:
                if len(current_group) >= MIN_TEAR_LINES:
                    tear_locations.append(current_group)
                current_group = [bad_rows[i]]
        # Check the last group
        if len(current_group) >= MIN_TEAR_LINES:
            tear_locations.append(current_group)
    
    # Flatten the list of tear locations
    all_tear_rows = []
    for group in tear_locations:
        all_tear_rows.extend(group)
        
    has_tearing = len(all_tear_rows) > 0
    return has_tearing, all_tear_rows

def scan_video_for_artifacts(video_path: str, output_dir: Optional[str] = None) -> Dict:
    """
    Scan a video for tearing artifacts and generate a report.
    
    Args:
        video_path: Path to the input video file
        output_dir: Directory to save the artifact report (optional)
        
    Returns:
        Dictionary containing:
            - video_path: Path to the scanned video
            - total_frames: Total number of frames
            - frames_with_artifacts: Number of frames with tearing
            - artifact_details: List of dictionaries with frame index and tear locations
            - artifact_rate: Percentage of frames with artifacts
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
        
    logger.info(f"Scanning video for artifacts: {video_path}")
    
    # Extract frames
    frames = extract_frames(str(video_path))
    total_frames = len(frames)
    
    if total_frames == 0:
        logger.warning(f"No frames extracted from {video_path}")
        return {
            "video_path": str(video_path),
            "total_frames": 0,
            "frames_with_artifacts": 0,
            "artifact_details": [],
            "artifact_rate": 0.0
        }
    
    artifact_details = []
    frames_with_artifacts = 0
    
    for frame_idx, frame in enumerate(frames):
        has_tearing, tear_rows = detect_tearing_artifacts(frame)
        
        if has_tearing:
            frames_with_artifacts += 1
            artifact_details.append({
                "frame_index": frame_idx,
                "tear_rows": tear_rows,
                "num_tear_rows": len(tear_rows)
            })
            
            # Log severe cases immediately
            if len(tear_rows) > 20:  # Severe tearing
                logger.warning(
                    f"Severe tearing detected in {video_path.name} at frame {frame_idx}. "
                    f"Detected {len(tear_rows)} corrupted rows. Flagging for manual review."
                )
    
    artifact_rate = (frames_with_artifacts / total_frames * 100) if total_frames > 0 else 0.0
    
    result = {
        "video_path": str(video_path),
        "total_frames": total_frames,
        "frames_with_artifacts": frames_with_artifacts,
        "artifact_details": artifact_details,
        "artifact_rate": artifact_rate
    }
    
    # Save report if output directory specified
    if output_dir:
        output_path = Path(output_dir) / f"{video_path.stem}_artifacts.json"
        import json
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Artifact report saved to: {output_path}")
    
    return result

def main():
    """
    Main entry point for artifact detection script.
    Usage: python -m code.utils.artifact_detector --video <path> --output <dir>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Detect tearing artifacts in videos")
    parser.add_argument("--video", required=True, help="Path to input video")
    parser.add_argument("--output", help="Output directory for artifact report")
    parser.add_argument("--threshold", type=float, default=TEARING_THRESHOLD, 
                      help="Gradient threshold for tear detection")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Determine output directory
        output_dir = args.output
        if not output_dir:
            # Default to results directory
            config = get_config()
            output_dir = str(get_results_dir())
            
        # Run detection
        result = scan_video_for_artifacts(args.video, output_dir)
        
        # Print summary
        print(f"\nArtifact Detection Summary for: {args.video}")
        print(f"Total frames: {result['total_frames']}")
        print(f"Frames with artifacts: {result['frames_with_artifacts']}")
        print(f"Artifact rate: {result['artifact_rate']:.2f}%")
        
        if result['frames_with_artifacts'] > 0:
            print("\n⚠️  WARNING: Tearing artifacts detected!")
            print("These frames may have been corrupted by severe 3D drift.")
            print("Manual review is recommended before including these in final analysis.")
            
            # Log severe cases
            severe_cases = [
                detail for detail in result['artifact_details']
                if detail['num_tear_rows'] > 20
            ]
            if severe_cases:
                print(f"\nSevere tearing detected in {len(severe_cases)} frame(s):")
                for case in severe_cases:
                    print(f"  - Frame {case['frame_index']}: {case['num_tear_rows']} corrupted rows")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during artifact detection: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())