"""
Baseline metrics calculation for motion artifact analysis.

Generates a random-noise video and calculates the motion artifact baseline score.
This baseline is used to subtract from raw fidelity scores to isolate true model performance.
"""
import os
import sys
import json
import random
import numpy as np
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, log_info, log_error, log_exception
from utils.errors import fail_loudly

logger = get_logger(__name__)

# Constants
DEFAULT_VIDEO_WIDTH = 256
DEFAULT_VIDEO_HEIGHT = 256
DEFAULT_VIDEO_FRAMES = 30
DEFAULT_VIDEO_FPS = 24
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "baseline_scores.json"
TEMP_VIDEO_FILE = OUTPUT_DIR / "temp_baseline_noise.mp4"


def generate_random_noise_video(
    width: int = DEFAULT_VIDEO_WIDTH,
    height: int = DEFAULT_VIDEO_HEIGHT,
    num_frames: int = DEFAULT_VIDEO_FRAMES,
    fps: int = DEFAULT_VIDEO_FPS,
    output_path: Path = TEMP_VIDEO_FILE
) -> Path:
    """
    Generate a random noise video file.
    
    Args:
        width: Video width in pixels
        height: Video height in pixels
        num_frames: Number of frames in the video
        fps: Frames per second
        output_path: Path to save the video file
    
    Returns:
        Path to the generated video file
    
    Raises:
        RuntimeError: If video generation fails
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to import cv2 for video writing
        try:
            import cv2
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(
                str(output_path),
                fourcc,
                fps,
                (width, height)
            )
            
            if not out.isOpened():
                fail_loudly("Failed to open VideoWriter for noise video generation")
            
            # Generate random frames
            for i in range(num_frames):
                # Generate random noise frame (0-255 for each pixel)
                frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
                out.write(frame)
            
            out.release()
            logger.info(f"Generated random noise video: {output_path}")
            return output_path
            
        except ImportError:
            fail_loudly("OpenCV (cv2) is required for video generation but not installed. Install with: pip install opencv-python-headless")
            
    except Exception as e:
        log_exception(logger, e, "Failed to generate random noise video")
        fail_loudly(f"Video generation failed: {str(e)}")


def calculate_motion_artifact_score(video_path: Path) -> float:
    """
    Calculate the motion artifact baseline score for a video.
    
    The score is computed as the average frame-to-frame difference,
    normalized to [0, 1]. For pure random noise, this should be high.
    
    Args:
        video_path: Path to the video file
    
    Returns:
        Motion artifact score (float between 0 and 1)
    
    Raises:
        RuntimeError: If score calculation fails
    """
    try:
        import cv2
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            fail_loudly(f"Failed to open video file: {video_path}")
        
        frame_count = 0
        total_diff = 0.0
        prev_frame = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if prev_frame is not None:
                # Calculate absolute difference between consecutive frames
                diff = cv2.absdiff(prev_frame, frame)
                # Compute mean difference across all pixels and channels
                frame_diff = np.mean(diff)
                total_diff += frame_diff
                frame_count += 1
            
            prev_frame = frame.copy()
        
        cap.release()
        
        if frame_count < 2:
            fail_loudly("Video has fewer than 2 frames, cannot compute motion artifact score")
        
        # Average frame-to-frame difference
        avg_diff = total_diff / frame_count
        
        # Normalize to [0, 1] range (max possible difference is 255)
        normalized_score = avg_diff / 255.0
        
        # Clamp to [0, 1]
        normalized_score = max(0.0, min(1.0, normalized_score))
        
        logger.info(f"Calculated motion artifact score: {normalized_score:.6f}")
        return normalized_score
        
    except ImportError:
        fail_loudly("OpenCV (cv2) is required for video analysis but not installed.")
    except Exception as e:
        log_exception(logger, e, "Failed to calculate motion artifact score")
        fail_loudly(f"Score calculation failed: {str(e)}")


def save_baseline_scores(baseline_score: float, output_path: Path = OUTPUT_FILE) -> None:
    """
    Save baseline scores to a JSON file.
    
    Args:
        baseline_score: The computed motion artifact baseline score
        output_path: Path to save the JSON file
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        baseline_data = {
            "baseline_score": baseline_score,
            "description": "Motion artifact baseline score from random noise video",
            "video_specs": {
                "width": DEFAULT_VIDEO_WIDTH,
                "height": DEFAULT_VIDEO_HEIGHT,
                "num_frames": DEFAULT_VIDEO_FRAMES,
                "fps": DEFAULT_VIDEO_FPS
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        
        logger.info(f"Saved baseline scores to: {output_path}")
        
    except Exception as e:
        log_exception(logger, e, "Failed to save baseline scores")
        fail_loudly(f"Failed to save baseline scores: {str(e)}")


def run_baseline_calculation() -> Dict[str, Any]:
    """
    Run the complete baseline calculation pipeline.
    
    Returns:
        Dictionary containing the baseline score and metadata
    """
    logger.info("Starting baseline calculation pipeline...")
    
    # Generate random noise video
    video_path = generate_random_noise_video()
    
    # Calculate motion artifact score
    baseline_score = calculate_motion_artifact_score(video_path)
    
    # Save results
    save_baseline_scores(baseline_score)
    
    # Clean up temporary video file
    if video_path.exists():
        try:
            video_path.unlink()
            logger.info(f"Cleaned up temporary video file: {video_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary video file: {e}")
    
    result = {
        "baseline_score": baseline_score,
        "output_file": str(OUTPUT_FILE)
    }
    
    logger.info(f"Baseline calculation complete. Score: {baseline_score:.6f}")
    return result


def main():
    """Main entry point for baseline calculation."""
    try:
        result = run_baseline_calculation()
        print(f"Baseline calculation completed successfully.")
        print(f"Baseline score: {result['baseline_score']:.6f}")
        print(f"Results saved to: {result['output_file']}")
        return 0
    except Exception as e:
        log_exception(logger, e, "Baseline calculation failed")
        print(f"ERROR: Baseline calculation failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
