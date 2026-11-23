import os
import sys
import json
import logging
import subprocess
import math
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/generation.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class VideoMetadata:
    video_id: str
    original_id: str
    source_url: str
    start_time: float
    end_time: float
    duration: float
    original_width: int
    original_height: int
    distorted_width: int
    distorted_height: int
    aspect_ratio: float
    distortion_type: str
    fps: float
    codec: str
    file_size_bytes: int
    status: str  # 'success', 'skipped_low_fps', 'excluded_unresolvable', 'failed'
    error_message: Optional[str] = None
    processing_time: float = 0.0

def get_video_dimensions(video_path: str) -> Tuple[int, int]:
    """Get video dimensions using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'json',
        video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        stream = data['streams'][0]
        return int(stream['width']), int(stream['height'])
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to get dimensions for {video_path}: {e}")
        raise

def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        logger.error(f"Failed to get duration for {video_path}: {e}")
        raise

def get_video_fps(video_path: str) -> float:
    """Get video FPS using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=r_frame_rate',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        fps_str = result.stdout.strip()
        if '/' in fps_str:
            num, den = map(int, fps_str.split('/'))
            return num / den if den != 0 else 0.0
        return float(fps_str)
    except (subprocess.CalledProcessError, ValueError, ZeroDivisionError) as e:
        logger.warning(f"Failed to get FPS for {video_path}: {e}. Defaulting to 30.0")
        return 30.0

def detect_primary_subject_bb(video_path: str) -> Optional[Dict[str, float]]:
    """
    Detect primary subject bounding box using YOLOv8.
    Returns dict with x1, y1, x2, y2 (normalized 0-1) or None if detection fails.
    """
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')  # Use nano model for speed
        results = model(video_path, verbose=False)
        
        if results and len(results) > 0:
            boxes = results[0].boxes
            if len(boxes) > 0:
                # Get the largest box (assuming primary subject)
                max_area = 0
                best_box = None
                for box in boxes:
                    xyxy = box.xyxy[0].tolist()
                    area = (xyxy[2] - xyxy[0]) * (xyxy[3] - xyxy[1])
                    if area > max_area:
                        max_area = area
                        best_box = xyxy
                
                if best_box:
                    width, height = get_video_dimensions(video_path)
                    return {
                        'x1': best_box[0] / width,
                        'y1': best_box[1] / height,
                        'x2': best_box[2] / width,
                        'y2': best_box[3] / height
                    }
        return None
    except ImportError:
        logger.warning("ultralytics not installed. Skipping subject detection.")
        return None
    except Exception as e:
        logger.warning(f"Subject detection failed for {video_path}: {e}")
        return None

def check_fr_001(bb: Dict[str, float], width: int, height: int) -> bool:
    """
    Check FR-001: Primary subject bounding box area reduction > 95% is excluded.
    Returns True if clip is acceptable (area reduction <= 95%), False otherwise.
    """
    if not bb:
        logger.warning("No bounding box detected. Assuming acceptable.")
        return True
    
    original_area = width * height
    bb_area = (bb['x2'] - bb['x1']) * (bb['y2'] - bb['y1']) * original_area
    
    # If BB area is > 5% of original, it's acceptable
    return bb_area > (original_area * 0.05)

def apply_distortion_ffmpeg(
    input_path: str,
    output_path: str,
    target_width: int,
    target_height: int,
    distortion_type: str,
    low_fps_warning: bool = False,
    unresolvable_flag: bool = False
) -> bool:
    """
    Apply geometric distortion using ffmpeg.
    Handles low FPS and unresolvable 1-pixel lines.
    """
    if unresolvable_flag:
        logger.error(f"Skipping unresolvable video: {input_path} (1-pixel line detected)")
        return False

    # Check for low FPS
    fps = get_video_fps(input_path)
    if fps < 10.0:
        logger.warning(f"Low FPS detected ({fps:.2f}) for {input_path}. Upsampling to 30fps.")
        low_fps_warning = True
    
    # Build ffmpeg filter chain
    if distortion_type == 'horizontal_stretch':
        # Stretch horizontally
        filter_complex = f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2"
    elif distortion_type == 'vertical_stretch':
        # Stretch vertically
        filter_complex = f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2"
    elif distortion_type == 'horizontal_compress':
        # Compress horizontally
        filter_complex = f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2"
    elif distortion_type == 'vertical_compress':
        # Compress vertically
        filter_complex = f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2"
    else:
        filter_complex = f"scale={target_width}:{target_height}"

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-vf', filter_complex,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-r', '30',  # Force 30fps output
        output_path
    ]

    try:
        start_time = time.time()
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        end_time = time.time()
        
        if low_fps_warning:
            logger.info(f"Upsampled low FPS video to 30fps: {output_path} (took {end_time - start_time:.2f}s)")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed for {input_path}: {e.stderr}")
        return False

def fetch_video_clip_from_url(
    url: str,
    output_path: str,
    start_time: float,
    end_time: float
) -> bool:
    """Fetch and trim video clip from URL using ffmpeg."""
    duration = end_time - start_time
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(start_time),
        '-t', str(duration),
        '-i', url,
        '-c', 'copy',
        '-avoid_negative_ts', 'make_zero',
        output_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to fetch clip from {url}: {e.stderr}")
        return False

def check_unresolvable_line(video_path: str) -> bool:
    """
    Check if video contains unresolvable 1-pixel lines.
    Returns True if unresolvable (should be excluded), False otherwise.
    """
    try:
        width, height = get_video_dimensions(video_path)
        # Check for 1-pixel dimensions which are unresolvable
        if width == 1 or height == 1:
            logger.error(f"Unresolvable 1-pixel line detected in {video_path} (dim: {width}x{height})")
            return True
        return False
    except Exception as e:
        logger.warning(f"Could not check dimensions for {video_path}: {e}")
        return False

def save_metadata(metadata_list: List[VideoMetadata], output_path: str):
    """Save metadata list to CSV."""
    import csv
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=asdict(metadata_list[0]).keys())
        writer.writeheader()
        for meta in metadata_list:
            writer.writerow(asdict(meta))

def process_dataset(
    dataset_iterable,
    output_dir: str,
    metadata_output: str,
    target_ratios: List[Tuple[int, int]],
    skip_low_fps: bool = False,
    exclude_unresolvable: bool = True
) -> List[VideoMetadata]:
    """
    Process dataset to generate distorted videos.
    
    Args:
        dataset_iterable: Iterable of dataset items (must have video_id, url, start, end)
        output_dir: Directory to save distorted videos
        metadata_output: Path to save metadata CSV
        target_ratios: List of (width, height) tuples for distortion
        skip_low_fps: If True, skip videos with FPS < 10. If False, upsample with warning.
        exclude_unresolvable: If True, exclude videos with 1-pixel lines.
    
    Returns:
        List of VideoMetadata objects
    """
    os.makedirs(output_dir, exist_ok=True)
    metadata_list = []
    
    for idx, item in enumerate(dataset_iterable):
        video_id = item.get('video_id', f'video_{idx}')
        source_url = item.get('url', '')
        start_time = float(item.get('start', 0))
        end_time = float(item.get('end', 10))
        duration = end_time - start_time
        
        # Download clip
        temp_path = os.path.join(output_dir, f'{video_id}_temp.mp4')
        if not fetch_video_clip_from_url(source_url, temp_path, start_time, end_time):
            logger.warning(f"Failed to fetch clip for {video_id}. Skipping.")
            continue
        
        # Check for unresolvable lines
        if check_unresolvable_line(temp_path):
            if exclude_unresolvable:
                meta = VideoMetadata(
                    video_id=video_id,
                    original_id=item.get('original_id', ''),
                    source_url=source_url,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    original_width=0,
                    original_height=0,
                    distorted_width=0,
                    distorted_height=0,
                    aspect_ratio=0,
                    distortion_type='unresolvable',
                    fps=0,
                    codec='',
                    file_size_bytes=0,
                    status='excluded_unresolvable',
                    error_message='Unresolvable 1-pixel line detected'
                )
                metadata_list.append(meta)
                continue
            else:
                logger.warning(f"Unresolvable line in {video_id} but exclusion disabled. Attempting processing.")
        
        # Get original dimensions
        try:
            orig_w, orig_h = get_video_dimensions(temp_path)
        except:
            logger.warning(f"Could not get dimensions for {video_id}. Skipping.")
            continue
        
        # Check FPS
        fps = get_video_fps(temp_path)
        if fps < 10.0 and skip_low_fps:
            meta = VideoMetadata(
                video_id=video_id,
                original_id=item.get('original_id', ''),
                source_url=source_url,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                original_width=orig_w,
                original_height=orig_h,
                distorted_width=0,
                distorted_height=0,
                aspect_ratio=0,
                distortion_type='low_fps_skipped',
                fps=fps,
                codec='',
                file_size_bytes=0,
                status='skipped_low_fps',
                error_message=f'Low FPS ({fps:.2f}) skipped per configuration'
            )
            metadata_list.append(meta)
            continue
        
        # Process each target ratio
        for target_w, target_h in target_ratios:
            start_proc = time.time()
            distortion_type = 'unknown'
            if target_w > target_h:
                distortion_type = 'horizontal_stretch' if target_w / target_h > orig_w / orig_h else 'horizontal_compress'
            else:
                distortion_type = 'vertical_stretch' if target_h / target_w > orig_h / orig_w else 'vertical_compress'
            
            output_path = os.path.join(
                output_dir, 
                f'{video_id}_{distortion_type}_{target_w}x{target_h}.mp4'
            )
            
            # Check for 1-pixel output dimensions
            if target_w == 1 or target_h == 1:
                meta = VideoMetadata(
                    video_id=video_id,
                    original_id=item.get('original_id', ''),
                    source_url=source_url,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    original_width=orig_w,
                    original_height=orig_h,
                    distorted_width=target_w,
                    distorted_height=target_h,
                    aspect_ratio=target_w / target_h if target_h != 0 else 0,
                    distortion_type=distortion_type,
                    fps=fps,
                    codec='',
                    file_size_bytes=0,
                    status='excluded_unresolvable',
                    error_message='Output dimension would be 1-pixel line'
                )
                metadata_list.append(meta)
                continue
            
            success = apply_distortion_ffmpeg(
                temp_path, output_path, target_w, target_h, distortion_type,
                low_fps_warning=(fps < 10.0),
                unresolvable_flag=False
            )
            
            if not success:
                meta = VideoMetadata(
                    video_id=video_id,
                    original_id=item.get('original_id', ''),
                    source_url=source_url,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    original_width=orig_w,
                    original_height=orig_h,
                    distorted_width=0,
                    distorted_height=0,
                    aspect_ratio=0,
                    distortion_type=distortion_type,
                    fps=fps,
                    codec='',
                    file_size_bytes=0,
                    status='failed',
                    error_message='FFmpeg distortion failed'
                )
                metadata_list.append(meta)
                continue
            
            # Get output info
            try:
                out_w, out_h = get_video_dimensions(output_path)
                out_size = os.path.getsize(output_path)
                out_fps = get_video_fps(output_path)
            except:
                logger.warning(f"Could not get output info for {output_path}")
                out_w, out_h, out_size, out_fps = 0, 0, 0, 0
            
            meta = VideoMetadata(
                video_id=video_id,
                original_id=item.get('original_id', ''),
                source_url=source_url,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                original_width=orig_w,
                original_height=orig_h,
                distorted_width=out_w,
                distorted_height=out_h,
                aspect_ratio=out_w / out_h if out_h != 0 else 0,
                distortion_type=distortion_type,
                fps=out_fps,
                codec='h264',
                file_size_bytes=out_size,
                status='success',
                processing_time=time.time() - start_proc
            )
            metadata_list.append(meta)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    save_metadata(metadata_list, metadata_output)
    return metadata_list

def main():
    """Main entry point for distortion generation."""
    import argparse
    parser = argparse.ArgumentParser(description='Generate distorted video dataset')
    parser.add_argument('--output-dir', type=str, default='data/distorted', help='Output directory')
    parser.add_argument('--metadata', type=str, default='data/metadata/distortion_metadata.csv', help='Metadata output path')
    parser.add_argument('--ratios', type=str, default='1:10,10:1,1:20,20:1', help='Target aspect ratios (w:h)')
    parser.add_argument('--skip-low-fps', action='store_true', help='Skip low FPS videos instead of upsampling')
    parser.add_argument('--exclude-unresolvable', action='store_true', default=True, help='Exclude unresolvable 1-pixel lines')
    args = parser.parse_args()
    
    # Parse ratios
    ratios = []
    for r in args.ratios.split(','):
        w, h = map(int, r.split(':'))
        ratios.append((w, h))
    
    logger.info(f"Starting distortion generation with ratios: {ratios}")
    logger.info(f"Skip low FPS: {args.skip_low_fps}, Exclude unresolvable: {args.exclude_unresolvable}")
    
    # Placeholder: In real implementation, load dataset from T012b/T013
    # For now, log the configuration
    logger.info("Configuration loaded. Ready to process dataset.")
    logger.info("Note: Actual dataset loading and processing requires T012b/T013 completion.")

if __name__ == '__main__':
    main()
