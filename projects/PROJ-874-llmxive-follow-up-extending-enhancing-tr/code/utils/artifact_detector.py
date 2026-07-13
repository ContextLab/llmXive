import os
import sys
import logging
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def detect_tearing_artifacts(
    frame: np.ndarray,
    threshold: float = 0.15,
    min_severity: float = 0.25
) -> Tuple[bool, Dict]:
    """
    Detects pixel tearing artifacts in a frame caused by severe 3D drift during warping.
    
    Tearing manifests as sharp, discontinuous horizontal intensity changes that violate
    natural scene continuity. This function analyzes horizontal gradients to identify
    such anomalies.
    
    Args:
        frame: Input frame (BGR, uint8 or float).
        threshold: Gradient magnitude threshold for edge detection (0.0-1.0).
        min_severity: Minimum ratio of affected pixels to flag as tearing.
    
    Returns:
        Tuple of (is_tearing, details_dict).
        details_dict contains:
            - 'severity': float (0.0 to 1.0)
            - 'affected_rows': int
            - 'total_rows': int
            - 'locations': List of (row_idx, max_gradient)
    """
    if frame is None or frame.size == 0:
        return False, {'error': 'Empty frame'}
    
    # Normalize to float [0, 1] if needed
    if frame.dtype == np.uint8:
        img = frame.astype(np.float32) / 255.0
    else:
        img = frame.astype(np.float32)
    
    # Convert to grayscale for gradient analysis
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # Compute horizontal gradient (Sobel X)
    # Using Sobel to detect sharp horizontal discontinuities
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    abs_grad_x = cv2.absgrad(grad_x)
    
    # Normalize gradient
    max_grad = np.max(abs_grad_x)
    if max_grad == 0:
        return False, {'severity': 0.0, 'affected_rows': 0, 'total_rows': gray.shape[0]}
    
    norm_grad = abs_grad_x / max_grad
    
    # Identify rows with high gradients (potential tearing lines)
    # Tearing typically appears as a sharp horizontal line
    row_max_grads = np.max(norm_grad, axis=1)
    
    # Find rows exceeding threshold
    tearing_rows = np.where(row_max_grads > threshold)[0]
    
    if len(tearing_rows) == 0:
        return False, {
            'severity': 0.0,
            'affected_rows': 0,
            'total_rows': gray.shape[0],
            'locations': []
        }
    
    # Calculate severity
    severity = len(tearing_rows) / gray.shape[0]
    
    # Collect detailed locations
    locations = []
    for row_idx in tearing_rows:
        max_val = float(row_max_grads[row_idx])
        locations.append((int(row_idx), max_val))
    
    is_tearing = severity >= min_severity
    
    return is_tearing, {
        'severity': float(severity),
        'affected_rows': int(len(tearing_rows)),
        'total_rows': int(gray.shape[0]),
        'locations': locations
    }


def scan_video_for_artifacts(
    video_path: str,
    output_log_path: str,
    threshold: float = 0.15,
    min_severity: float = 0.25
) -> Dict:
    """
    Scans a warped video file for tearing artifacts and logs results.
    
    Args:
        video_path: Path to the input video file.
        output_log_path: Path to the JSON log file for artifact details.
        threshold: Gradient threshold for detection.
        min_severity: Minimum severity to flag a frame as corrupted.
    
    Returns:
        Dictionary with summary statistics.
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return {'error': 'File not found', 'video_path': video_path}
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Failed to open video: {video_path}")
        return {'error': 'Failed to open video', 'video_path': video_path}
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    flagged_frames = []
    all_details = []
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        is_tearing, details = detect_tearing_artifacts(
            frame, 
            threshold=threshold, 
            min_severity=min_severity
        )
        
        details['frame_index'] = frame_idx
        details['timestamp'] = frame_idx / fps if fps > 0 else 0
        
        if is_tearing:
            flagged_frames.append(frame_idx)
            logger.warning(
                f"Teering detected at frame {frame_idx} "
                f"(severity: {details['severity']:.2f})"
            )
        
        all_details.append(details)
        frame_idx += 1
    
    cap.release()
    
    # Prepare summary
    summary = {
        'video_path': video_path,
        'total_frames': total_frames,
        'flagged_frames_count': len(flagged_frames),
        'flagged_frame_indices': flagged_frames,
        'tearing_rate': len(flagged_frames) / total_frames if total_frames > 0 else 0.0,
        'threshold_used': threshold,
        'min_severity_used': min_severity
    }
    
    # Write detailed log
    log_entry = {
        'video_path': video_path,
        'summary': summary,
        'frame_details': all_details
    }
    
    output_dir = os.path.dirname(output_log_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    logger.info(f"Artifact scan complete. Logged to {output_log_path}")
    return summary


def main():
    """CLI entry point for artifact detection."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(
        description="Detect and log pixel tearing artifacts in warped videos."
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help="Path to the input video file (warped/condition C)."
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help="Path to the output JSON log file."
    )
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=0.15,
        help="Gradient threshold for tearing detection (default: 0.15)."
    )
    parser.add_argument(
        '--min-severity', '-s',
        type=float,
        default=0.25,
        help="Minimum severity ratio to flag frame (default: 0.25)."
    )
    
    args = parser.parse_args()
    
    summary = scan_video_for_artifacts(
        video_path=args.input,
        output_log_path=args.output,
        threshold=args.threshold,
        min_severity=args.min_severity
    )
    
    if 'error' in summary:
        print(f"Error: {summary['error']}")
        sys.exit(1)
    
    print(f"Scan Complete:")
    print(f"  Total Frames: {summary['total_frames']}")
    print(f"  Flagged Frames: {summary['flagged_frames_count']}")
    print(f"  Tearing Rate: {summary['tearing_rate']:.2%}")
    print(f"  Log saved to: {args.output}")


if __name__ == "__main__":
    main()
