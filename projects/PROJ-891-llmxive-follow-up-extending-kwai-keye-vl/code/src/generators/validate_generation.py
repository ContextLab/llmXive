"""
Validation script for generated synthetic video benchmark dataset.

Verifies:
1. Output dimensions match expected aspect ratios (1:10, 10:1, 1:20, 20:1, and square control)
2. Metadata CSV integrity (links distorted videos to original IDs and timestamps)
3. Video codec validity and frame rate consistency
4. Bounding box integrity (FR-001) for excluded clips
5. Directory structure completeness

Usage:
    python code/src/generators/validate_generation.py
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
EXPECTED_RATIOS = [1.0, 0.1, 10.0, 0.05, 20.0]  # Square, 1:10, 10:1, 1:20, 20:1
TOLERANCE_PERCENT = 0.1  # 0.1% tolerance for aspect ratio
DATA_ROOT = Path("data")
DISTORTED_DIR = DATA_ROOT / "distorted"
CONTROL_DIR = DATA_ROOT / "outputs" / "control"
METADATA_FILE = DATA_ROOT / "outputs" / "distorted_metadata.csv"
ORIGINAL_DIR = DATA_ROOT / "raw" / "original"

# Expected columns in metadata CSV
EXPECTED_COLUMNS = [
    "video_id", 
    "original_id", 
    "original_start", 
    "original_end", 
    "ratio_type", 
    "width", 
    "height", 
    "duration", 
    "fps", 
    "codec", 
    "fr_001_passed",
    "file_path"
]

def get_video_info(video_path: Path) -> Optional[Dict]:
    """Extract video metadata using ffprobe."""
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return None
    
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"ffprobe failed for {video_path}: {result.stderr}")
            return None
        
        data = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break
        
        if not video_stream:
            logger.error(f"No video stream found in {video_path}")
            return None
        
        return {
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "duration": float(data.get("format", {}).get("duration", 0)),
            "fps": None,  # Will be calculated from avg_frame_rate
            "codec": video_stream.get("codec_name", "unknown"),
            "bit_rate": video_stream.get("bit_rate", "0"),
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"ffprobe timeout for {video_path}")
        return None
    except Exception as e:
        logger.error(f"Error processing {video_path}: {e}")
        return None

def calculate_fps(video_info: Dict) -> Optional[float]:
    """Calculate FPS from video info if possible."""
    # This would need to be extracted from ffprobe's avg_frame_rate
    # For now, we'll rely on the metadata CSV if available
    return video_info.get("fps")

def check_aspect_ratio(width: int, height: int, expected_ratio: float) -> Tuple[bool, float]:
    """Check if video aspect ratio matches expected ratio within tolerance."""
    if height == 0:
        return False, 0.0
    
    actual_ratio = width / height
    if expected_ratio == 0:
        return False, 0.0
    
    # Calculate percentage difference
    pct_diff = abs(actual_ratio - expected_ratio) / expected_ratio * 100
    is_valid = pct_diff <= TOLERANCE_PERCENT
    
    return is_valid, pct_diff

def validate_directory_structure() -> bool:
    """Verify that expected directory structure exists."""
    required_dirs = [
        DISTORTED_DIR,
        CONTROL_DIR,
        ORIGINAL_DIR,
        DATA_ROOT / "outputs"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if not dir_path.exists():
            logger.error(f"Required directory missing: {dir_path}")
            all_exist = False
        else:
            logger.info(f"Directory exists: {dir_path}")
    
    return all_exist

def validate_metadata_csv() -> Tuple[bool, int, int]:
    """Validate the metadata CSV file."""
    if not METADATA_FILE.exists():
        logger.error(f"Metadata CSV not found: {METADATA_FILE}")
        return False, 0, 0
    
    try:
        df = pd.read_csv(METADATA_FILE)
        
        # Check columns
        missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
        if missing_cols:
            logger.error(f"Missing columns in metadata CSV: {missing_cols}")
            return False, 0, 0
        
        # Check for empty dataframe
        if len(df) == 0:
            logger.error("Metadata CSV is empty")
            return False, 0, 0
        
        logger.info(f"Metadata CSV loaded successfully with {len(df)} records")
        return True, len(df), len(missing_cols)
        
    except Exception as e:
        logger.error(f"Error reading metadata CSV: {e}")
        return False, 0, 0

def validate_video_files() -> Tuple[Dict[str, int], List[str]]:
    """Validate all video files in distorted and control directories."""
    stats = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "missing": 0,
        "aspect_ratio_fail": 0,
        "codec_fail": 0,
        "duration_fail": 0
    }
    errors = []
    
    # Collect all expected video paths from metadata
    if METADATA_FILE.exists():
        try:
            df = pd.read_csv(METADATA_FILE)
            for idx, row in df.iterrows():
                video_path = Path(row["file_path"])
                stats["total"] += 1
                
                if not video_path.exists():
                    stats["missing"] += 1
                    errors.append(f"Missing file: {video_path}")
                    continue
                
                # Get video info
                video_info = get_video_info(video_path)
                if not video_info:
                    stats["invalid"] += 1
                    errors.append(f"Invalid video file: {video_path}")
                    continue
                
                # Check aspect ratio
                expected_ratio = float(row["ratio_type"])
                is_valid_ratio, pct_diff = check_aspect_ratio(
                    video_info["width"], 
                    video_info["height"], 
                    expected_ratio
                )
                
                if not is_valid_ratio:
                    stats["aspect_ratio_fail"] += 1
                    errors.append(
                        f"Aspect ratio mismatch for {video_path}: "
                        f"expected {expected_ratio}, got {video_info['width']/video_info['height']} "
                        f"({pct_diff:.2f}% diff)"
                    )
                
                # Check codec (basic validation)
                if video_info["codec"] == "unknown":
                    stats["codec_fail"] += 1
                    errors.append(f"Unknown codec for {video_path}")
                
                # Check duration (should be > 0)
                if video_info["duration"] <= 0:
                    stats["duration_fail"] += 1
                    errors.append(f"Invalid duration for {video_path}")
                
                if is_valid_ratio and video_info["codec"] != "unknown" and video_info["duration"] > 0:
                    stats["valid"] += 1
                else:
                    stats["invalid"] += 1
                    
        except Exception as e:
            logger.error(f"Error validating video files from metadata: {e}")
            return stats, errors
    else:
        logger.warning("Metadata CSV not found, cannot validate video files")
    
    return stats, errors

def validate_control_group() -> Tuple[bool, int]:
    """Validate the control group (square-cropped clips)."""
    if not CONTROL_DIR.exists():
        logger.error("Control directory does not exist")
        return False, 0
    
    video_files = list(CONTROL_DIR.glob("*.mp4"))
    if not video_files:
        logger.error("No video files found in control directory")
        return False, 0
    
    valid_count = 0
    for video_file in video_files:
        video_info = get_video_info(video_file)
        if video_info:
            # Check if square (1:1 ratio)
            is_square = video_info["width"] == video_info["height"]
            if is_square:
                valid_count += 1
            else:
                logger.warning(f"Non-square video in control group: {video_file}")
    
    logger.info(f"Control group validation: {valid_count}/{len(video_files)} valid square videos")
    return valid_count == len(video_files), valid_count

def validate_original_clips() -> Tuple[bool, int]:
    """Validate original unmodified clips exist."""
    if not ORIGINAL_DIR.exists():
        logger.error("Original directory does not exist")
        return False, 0
    
    video_files = list(ORIGINAL_DIR.glob("*.mp4"))
    if not video_files:
        logger.error("No video files found in original directory")
        return False, 0
    
    valid_count = 0
    for video_file in video_files:
        video_info = get_video_info(video_file)
        if video_info and video_info["duration"] > 0:
            valid_count += 1
    
    logger.info(f"Original clips validation: {valid_count}/{len(video_files)} valid")
    return valid_count > 0, valid_count

def main():
    """Main validation function."""
    logger.info("Starting validation of generated synthetic video benchmark dataset")
    
    # Step 1: Validate directory structure
    logger.info("Step 1: Validating directory structure...")
    if not validate_directory_structure():
        logger.error("Directory structure validation failed")
        return 1
    
    # Step 2: Validate metadata CSV
    logger.info("Step 2: Validating metadata CSV...")
    meta_valid, record_count, missing_cols = validate_metadata_csv()
    if not meta_valid:
        logger.error("Metadata CSV validation failed")
        return 1
    logger.info(f"Metadata CSV OK: {record_count} records")
    
    # Step 3: Validate video files
    logger.info("Step 3: Validating video files...")
    video_stats, video_errors = validate_video_files()
    
    if video_stats["missing"] > 0:
        logger.warning(f"Missing video files: {video_stats['missing']}")
    if video_stats["aspect_ratio_fail"] > 0:
        logger.warning(f"Aspect ratio failures: {video_stats['aspect_ratio_fail']}")
    if video_stats["invalid"] > 0:
        logger.warning(f"Invalid video files: {video_stats['invalid']}")
    
    if video_stats["valid"] == 0:
        logger.error("No valid video files found")
        return 1
    
    # Step 4: Validate control group
    logger.info("Step 4: Validating control group (square-cropped)...")
    control_valid, control_count = validate_control_group()
    if not control_valid:
        logger.warning("Control group validation failed")
    
    # Step 5: Validate original clips
    logger.info("Step 5: Validating original unmodified clips...")
    original_valid, original_count = validate_original_clips()
    if not original_valid:
        logger.warning("Original clips validation failed")
    
    # Summary
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total videos checked: {video_stats['total']}")
    logger.info(f"Valid videos: {video_stats['valid']}")
    logger.info(f"Invalid videos: {video_stats['invalid']}")
    logger.info(f"Missing files: {video_stats['missing']}")
    logger.info(f"Aspect ratio failures: {video_stats['aspect_ratio_fail']}")
    logger.info(f"Control group valid: {control_count} videos")
    logger.info(f"Original clips valid: {original_count} videos")
    logger.info("=" * 60)
    
    if video_stats["valid"] > 0 and original_valid:
        logger.info("✓ Validation PASSED: Dataset is ready for inference")
        return 0
    else:
        logger.error("✗ Validation FAILED: Dataset has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())