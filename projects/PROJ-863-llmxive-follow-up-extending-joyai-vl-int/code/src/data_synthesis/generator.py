"""
Video Content Generator for llmXive Synthetic Data Pipeline.

Generates synthetic video frames representing human activities (falling, sitting, standing, walking)
and writes them directly to disk using chunked streaming to respect memory constraints.

Supports CI Mode (subset generation) and Non-CI Mode (full 50-hour generation).
"""
import json
import os
import time
import random
import math
from pathlib import Path
from dataclasses import asdict
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime

import numpy as np

from src.data_synthesis.models import SyntheticVideoFrame
from src.data_synthesis.handoff import HandoffManager, get_handoff_manager
from src.utils.logging import get_logger, log_data_event
from src.utils.env_config import get_required_env_vars

# Configuration
FPS = 30
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CHUNK_SIZE = 300  # 10 seconds of frames per chunk (300 frames)

# Activity Durations (in seconds)
DURATIONS = {
    'falling': 2,
    'sitting': 10,
    'standing': 15,
    'walking': 10
}

logger = get_logger(__name__)

def _generate_frame_data(activity: str, frame_idx: int, total_frames: int, seed: int) -> Dict[str, Any]:
    """
    Generate a synthetic frame representation (not actual pixels, but structured data
    representing the visual state for downstream processing).
    
    Args:
        activity: Current activity type
        frame_idx: Index of the frame within the current activity sequence
        total_frames: Total frames in this activity sequence
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary representing the frame state
    """
    np.random.seed(seed + frame_idx)
    
    # Base parameters for different activities
    if activity == 'falling':
        # Simulate falling motion: vertical position decreases rapidly
        progress = frame_idx / max(total_frames - 1, 1)
        y_pos = int(FRAME_HEIGHT * (1 - progress * 0.8))
        velocity_y = -int(FRAME_HEIGHT * 0.4 * progress)
        is_critical = progress > 0.7  # Critical phase of fall
    elif activity == 'sitting':
        # Stable sitting position
        y_pos = int(FRAME_HEIGHT * 0.7)
        velocity_y = 0
        is_critical = False
    elif activity == 'standing':
        # Stable standing position
        y_pos = int(FRAME_HEIGHT * 0.5)
        velocity_y = 0
        is_critical = False
    elif activity == 'walking':
        # Walking motion: slight vertical oscillation
        phase = (frame_idx % 15) / 15.0
        y_pos = int(FRAME_HEIGHT * 0.6 + math.sin(phase * 2 * math.pi) * 10)
        velocity_y = int(math.cos(phase * 2 * math.pi) * 5)
        is_critical = False
    else:
        y_pos = FRAME_HEIGHT // 2
        velocity_y = 0
        is_critical = False
    
    # Add noise
    y_pos += np.random.normal(0, 2)
    y_pos = max(0, min(FRAME_HEIGHT - 1, int(y_pos)))
    
    return {
        'y_position': y_pos,
        'velocity_y': velocity_y,
        'is_critical': is_critical,
        'activity': activity,
        'frame_idx': frame_idx
    }

def generate_activity_sequence(
    activity: str,
    duration_seconds: int,
    start_frame_idx: int,
    base_seed: int
) -> Iterator[SyntheticVideoFrame]:
    """
    Generate a sequence of frames for a specific activity.
    
    Args:
        activity: Type of activity
        duration_seconds: Duration in seconds
        start_frame_idx: Starting frame index in the overall video
        base_seed: Base random seed for reproducibility
    
    Yields:
        SyntheticVideoFrame objects
    """
    num_frames = duration_seconds * FPS
    seed = base_seed + int(time.time())
    
    for i in range(num_frames):
        frame_data = _generate_frame_data(activity, i, num_frames, seed)
        
        frame = SyntheticVideoFrame(
            timestamp=start_frame_idx + i,
            activity=activity,
            y_position=frame_data['y_position'],
            velocity_y=frame_data['velocity_y'],
            is_critical=frame_data['is_critical'],
            frame_id=f"frame_{start_frame_idx + i:08d}",
            chunk_id=(start_frame_idx + i) // CHUNK_SIZE
        )
        yield frame

def generate_video_stream(
    total_duration_hours: float,
    output_dir: Path,
    chunk_size: int = CHUNK_SIZE,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a continuous video stream with mixed activities.
    
    Args:
        total_duration_hours: Total duration in hours
        output_dir: Directory to write output files
        chunk_size: Number of frames per chunk
        seed: Random seed for activity sequence generation
    
    Returns:
        Manifest dictionary with generation metadata
    """
    if seed is None:
        seed = int(time.time())
    
    total_frames = int(total_duration_hours * 3600 * FPS)
    total_chunks = (total_frames + chunk_size - 1) // chunk_size
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize handoff manager for streaming
    handoff_manager = get_handoff_manager(output_dir)
    
    # Activity pool and weights
    activities = list(DURATIONS.keys())
    weights = [0.1, 0.3, 0.3, 0.3]  # falling, sitting, standing, walking
    
    manifest_entries = []
    current_chunk_frames = []
    frame_counter = 0
    start_time = time.time()
    
    random.seed(seed)
    
    for chunk_idx in range(total_chunks):
        chunk_start_frame = chunk_idx * chunk_size
        chunk_end_frame = min(chunk_start_frame + chunk_size, total_frames)
        chunk_duration = (chunk_end_frame - chunk_start_frame) / FPS
        
        # Generate frames for this chunk
        for _ in range(chunk_end_frame - chunk_start_frame):
            # Select activity
            activity = random.choices(activities, weights=weights)[0]
            activity_duration = DURATIONS[activity]
            activity_frames = int(activity_duration * FPS)
            
            # Generate sequence for this activity (might span multiple chunks)
            for frame in generate_activity_sequence(
                activity, 
                activity_duration, 
                frame_counter, 
                seed + frame_counter
            ):
                current_chunk_frames.append(frame)
                frame_counter += 1
                
                if len(current_chunk_frames) >= chunk_size:
                    break
            
            if len(current_chunk_frames) >= chunk_size:
                break
        
        # Write chunk to disk
        if current_chunk_frames:
            chunk_file = output_dir / f"chunk_{chunk_idx:06d}.jsonl"
            
            with open(chunk_file, 'w') as f:
                for frame in current_chunk_frames:
                    f.write(json.dumps(asdict(frame)) + '\n')
            
            # Register chunk with handoff manager
            handoff_manager.register_chunk(
                chunk_id=chunk_idx,
                file_path=str(chunk_file),
                num_frames=len(current_chunk_frames),
                duration_seconds=len(current_chunk_frames) / FPS
            )
            
            manifest_entries.append({
                'chunk_id': chunk_idx,
                'file': str(chunk_file),
                'num_frames': len(current_chunk_frames),
                'duration_seconds': len(current_chunk_frames) / FPS,
                'start_frame': chunk_start_frame,
                'end_frame': chunk_start_frame + len(current_chunk_frames) - 1
            })
            
            current_chunk_frames = []
        
        # Log progress every 10 chunks
        if (chunk_idx + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = (chunk_idx + 1) / elapsed if elapsed > 0 else 0
            logger.info(f"Generated chunk {chunk_idx + 1}/{total_chunks} "
                      f"({(chunk_idx + 1) / total_chunks * 100:.1f}%) "
                      f"at {rate:.2f} chunks/sec")
    
    # Finalize handoff
    handoff_manager.finalize()
    
    # Calculate totals
    total_duration_seconds = sum(e['duration_seconds'] for e in manifest_entries)
    total_frames_generated = sum(e['num_frames'] for e in manifest_entries)
    
    manifest = {
        'total_duration_hours': total_duration_hours,
        'actual_duration_seconds': total_duration_seconds,
        'total_frames': total_frames_generated,
        'chunk_count': len(manifest_entries),
        'chunk_size': chunk_size,
        'fps': FPS,
        'resolution': f"{FRAME_WIDTH}x{FRAME_HEIGHT}",
        'seed': seed,
        'generated_at': datetime.now().isoformat(),
        'chunks': manifest_entries
    }
    
    # Write manifest
    manifest_path = output_dir / 'manifest.jsonl'
    with open(manifest_path, 'w') as f:
        f.write(json.dumps(manifest) + '\n')
    
    logger.info(f"Generation complete: {total_duration_seconds:.2f}s ({total_duration_seconds/3600:.2f}h) "
               f"of video in {len(manifest_entries)} chunks")
    
    return manifest

def main():
    """Main entry point for video generation."""
    # Validate environment
    get_required_env_vars(['DATA_SEED'])
    
    # Configuration
    data_seed = int(os.environ.get('DATA_SEED', 42))
    output_base = Path('data/raw')
    
    # Determine mode: CI vs Non-CI
    # CI Mode: Generate subset (e.g., 0.5 hours) to fit 6h runtime
    # Non-CI Mode: Generate full 50 hours
    ci_mode = os.environ.get('CI_MODE', 'false').lower() == 'true'
    
    if ci_mode:
        target_hours = 0.5  # 30 minutes for CI testing
        logger.info("Running in CI mode - generating 0.5 hours of video")
    else:
        target_hours = 50.0  # Full 50 hours
        logger.info("Running in Non-CI mode - generating 50 hours of video")
    
    output_dir = output_base / f"synthetic_video_seed_{data_seed}"
    
    # Generate video stream
    manifest = generate_video_stream(
        total_duration_hours=target_hours,
        output_dir=output_dir,
        chunk_size=CHUNK_SIZE,
        seed=data_seed
    )
    
    # Log data event (zero VLM calls)
    log_data_event(
        event_type="data_generation_complete",
        details={
            "total_duration_seconds": manifest['actual_duration_seconds'],
            "total_frames": manifest['total_frames'],
            "chunk_count": manifest['chunk_count'],
            "mode": "ci" if ci_mode else "non_ci",
            "vlm_calls": 0
        }
    )
    
    print(f"Generated {manifest['actual_duration_seconds']:.2f} seconds of video")
    print(f"Manifest written to: {output_dir / 'manifest.jsonl'}")
    
    return manifest

if __name__ == '__main__':
    main()
