import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import csv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/validation.log')
    ]
)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def get_video_info(video_path: str) -> Dict[str, Any]:
    """Get video information using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,r_frame_rate,duration,codec_name',
        '-show_entries', 'format=duration',
        '-of', 'json',
        video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        stream = data['streams'][0] if data.get('streams') else {}
        format_info = data.get('format', {})
        
        width = int(stream.get('width', 0))
        height = int(stream.get('height', 0))
        fps_str = stream.get('r_frame_rate', '0/1')
        if '/' in fps_str:
            num, den = map(int, fps_str.split('/'))
            fps = num / den if den != 0 else 0.0
        else:
            fps = float(fps_str)
        
        duration = float(format_info.get('duration', stream.get('duration', 0)))
        codec = stream.get('codec_name', 'unknown')
        
        return {
            'width': width,
            'height': height,
            'fps': fps,
            'duration': duration,
            'codec': codec,
            'file_size': os.path.getsize(video_path)
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to get video info for {video_path}: {e}")
        raise ValidationError(f"Could not read video info: {e}")

def calculate_fps(video_path: str) -> float:
    """Calculate FPS from video file."""
    info = get_video_info(video_path)
    return info['fps']

def check_aspect_ratio(video_path: str, expected_ratio: float, tolerance: float = 0.001) -> bool:
    """Check if video aspect ratio matches expected value within tolerance."""
    info = get_video_info(video_path)
    actual_ratio = info['width'] / info['height'] if info['height'] != 0 else 0
    return abs(actual_ratio - expected_ratio) <= tolerance

def validate_directory_structure(output_dir: str, expected_subdirs: List[str]) -> bool:
    """Validate that expected subdirectories exist."""
    for subdir in expected_subdirs:
        path = os.path.join(output_dir, subdir)
        if not os.path.isdir(path):
            logger.error(f"Missing directory: {path}")
            return False
    return True

def validate_metadata_csv(csv_path: str, required_columns: List[str]) -> bool:
    """Validate metadata CSV structure."""
    if not os.path.exists(csv_path):
        logger.error(f"Metadata file not found: {csv_path}")
        return False
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if not headers:
            logger.error("CSV file is empty")
            return False
        
        missing = set(required_columns) - set(headers)
        if missing:
            logger.error(f"Missing columns in metadata: {missing}")
            return False
    
    return True

def validate_video_files(video_dir: str, expected_count: int = None) -> bool:
    """Validate that video files exist and are readable."""
    video_files = [f for f in os.listdir(video_dir) if f.endswith(('.mp4', '.avi', '.mov'))]
    
    if expected_count and len(video_files) != expected_count:
        logger.warning(f"Expected {expected_count} videos, found {len(video_files)}")
    
    for video_file in video_files:
        video_path = os.path.join(video_dir, video_file)
        try:
            get_video_info(video_path)
        except ValidationError as e:
            logger.error(f"Invalid video file {video_file}: {e}")
            return False
    
    return True

def validate_control_group(control_dir: str, expected_ratio: float = 1.0) -> bool:
    """Validate control group videos have correct aspect ratio."""
    video_files = [f for f in os.listdir(control_dir) if f.endswith(('.mp4', '.avi', '.mov'))]
    
    for video_file in video_files:
        video_path = os.path.join(control_dir, video_file)
        try:
            info = get_video_info(video_path)
            actual_ratio = info['width'] / info['height'] if info['height'] != 0 else 0
            if abs(actual_ratio - expected_ratio) > 0.01:  # 1% tolerance for control
                logger.error(f"Control video {video_file} has incorrect aspect ratio: {actual_ratio}")
                return False
        except Exception as e:
            logger.error(f"Error validating control video {video_file}: {e}")
            return False
    
    return True

def validate_original_clips(original_dir: str) -> bool:
    """Validate original unmodified clips from T012b."""
    if not os.path.exists(original_dir):
        logger.error(f"Original clips directory not found: {original_dir}")
        return False
    
    return validate_video_files(original_dir)

def validate_distorted_videos(distorted_dir: str, metadata_path: str) -> bool:
    """Validate distorted videos against metadata."""
    if not os.path.exists(metadata_path):
        logger.error(f"Metadata file not found: {metadata_path}")
        return False
    
    with open(metadata_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('status') == 'success':
                video_id = row.get('video_id')
                distortion_type = row.get('distortion_type')
                expected_w = int(row.get('distorted_width', 0))
                expected_h = int(row.get('distorted_height', 0))
                
                # Find the video file
                video_files = [f for f in os.listdir(distorted_dir) if video_id in f]
                if not video_files:
                    logger.warning(f"No video found for {video_id}")
                    continue
                
                video_path = os.path.join(distorted_dir, video_files[0])
                try:
                    info = get_video_info(video_path)
                    if info['width'] != expected_w or info['height'] != expected_h:
                        logger.error(f"Dimension mismatch for {video_id}: expected {expected_w}x{expected_h}, got {info['width']}x{info['height']}")
                        return False
                except Exception as e:
                    logger.error(f"Error validating video {video_id}: {e}")
                    return False
    
    return True

def main():
    """Main entry point for validation."""
    import argparse
    parser = argparse.ArgumentParser(description='Validate generated video dataset')
    parser.add_argument('--distorted-dir', type=str, default='data/distorted', help='Distorted videos directory')
    parser.add_argument('--control-dir', type=str, default='data/control', help='Control videos directory')
    parser.add_argument('--original-dir', type=str, default='data/raw/original', help='Original clips directory')
    parser.add_argument('--metadata', type=str, default='data/metadata/distortion_metadata.csv', help='Metadata CSV path')
    args = parser.parse_args()
    
    all_valid = True
    
    # Validate distorted videos
    if os.path.exists(args.distorted_dir):
        logger.info(f"Validating distorted videos in {args.distorted_dir}")
        if not validate_video_files(args.distorted_dir):
            all_valid = False
        
        if os.path.exists(args.metadata):
            if not validate_distorted_videos(args.distorted_dir, args.metadata):
                all_valid = False
    else:
        logger.warning(f"Distorted directory not found: {args.distorted_dir}")
    
    # Validate control group
    if os.path.exists(args.control_dir):
        logger.info(f"Validating control group in {args.control_dir}")
        if not validate_control_group(args.control_dir):
            all_valid = False
    else:
        logger.warning(f"Control directory not found: {args.control_dir}")
    
    # Validate original clips
    if os.path.exists(args.original_dir):
        logger.info(f"Validating original clips in {args.original_dir}")
        if not validate_original_clips(args.original_dir):
            all_valid = False
    else:
        logger.warning(f"Original directory not found: {args.original_dir}")
    
    if all_valid:
        logger.info("Validation PASSED")
        sys.exit(0)
    else:
        logger.error("Validation FAILED")
        sys.exit(1)

if __name__ == '__main__':
    main()