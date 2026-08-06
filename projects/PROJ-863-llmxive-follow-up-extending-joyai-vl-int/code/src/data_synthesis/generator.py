"""
Synthetic Video Content Generator for llmXive.

Generates synthetic video streams with ground-truth labels derived strictly from
visual content (e.g., falls) independent of any model output.

Supports CI Mode (subset) and Non-CI Mode (full 50h) with chunked streaming
to disk to enforce <6GB RAM limits.
"""
import json
import os
import time
import random
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator

# Import project models and utilities
from src.data_synthesis.models import SyntheticVideoFrame
from src.utils.logging import get_logger, log_data_event, log_no_vlm_call
from src.utils.env_config import get_required_env_vars
from src.data_synthesis.handoff import get_handoff_manager, ChunkManifest


# Constants for generation
FRAME_RATE = 30  # frames per second
TARGET_DURATION_SECONDS_CI = 3600  # 1 hour for CI
TARGET_DURATION_SECONDS_FULL = 180000  # 50 hours for Non-CI
CHUNK_SIZE_SECONDS = 300  # 5 minutes per chunk for streaming
OUTPUT_DIR = Path("data/raw")
MANIFEST_PATH = Path("data/manifest.jsonl")


def generate_activity_sequence(
    duration_seconds: int,
    frame_rate: int = FRAME_RATE,
    seed: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Generates a deterministic sequence of activity events for the video stream.

    Yields dictionaries representing activity states for each frame.
    Includes: 'sitting', 'standing', 'walking', 'falling', 'lying_down'.
    """
    if seed is not None:
        random.seed(seed)

    total_frames = duration_seconds * frame_rate
    current_frame = 0

    # Define activity segments
    activities = ['sitting', 'standing', 'walking', 'falling', 'lying_down']
    current_activity = random.choice(activities)
    next_switch_frame = random.randint(100, 500)

    while current_frame < total_frames:
        # Determine if we switch activities
        if current_frame >= next_switch_frame:
            # Prevent immediate switch to same activity
            available = [a for a in activities if a != current_activity]
            current_activity = random.choice(available)
            # If falling, ensure it transitions to lying_down eventually
            if current_activity == 'falling':
                next_switch_frame = current_frame + random.randint(10, 30)
            else:
                next_switch_frame = current_frame + random.randint(100, 1000)

        # Generate frame data for this activity
        frame_data = {
            "frame_index": current_frame,
            "activity": current_activity,
            "timestamp": current_frame / frame_rate,
            "is_critical": current_activity == 'falling',
            "confidence": random.uniform(0.8, 1.0) if current_activity != 'falling' else random.uniform(0.6, 0.9)
        }

        yield frame_data
        current_frame += 1


def generate_video_stream(
    duration_seconds: int,
    output_dir: Path,
    chunk_duration: int = CHUNK_SIZE_SECONDS,
    seed: Optional[int] = None,
    is_ci_mode: bool = False
) -> List[Dict[str, Any]]:
    """
    Generates video frames and writes them directly to disk in chunks.

    This function implements the streaming requirement (FR-001) to avoid
    loading all frames into memory. It writes JSONL chunks to `data/raw/`.

    Args:
        duration_seconds: Total duration to generate.
        output_dir: Directory to write chunk files.
        chunk_duration: Duration of each chunk in seconds.
        seed: Random seed for reproducibility.
        is_ci_mode: If True, generates a subset (1h) regardless of input.

    Returns:
        List of metadata entries for the manifest.
    """
    # Adjust duration for CI mode
    effective_duration = duration_seconds
    if is_ci_mode:
        effective_duration = min(duration_seconds, TARGET_DURATION_SECONDS_CI)
        log_data_event(f"CI Mode active: Limiting generation to {effective_duration} seconds.")
    else:
        # Ensure we hit the 50h target if requested
        if duration_seconds < TARGET_DURATION_SECONDS_FULL:
            effective_duration = TARGET_DURATION_SECONDS_FULL
            log_data_event(f"Non-CI Mode: Generating full {effective_duration} seconds (50h).")

    output_dir.mkdir(parents=True, exist_ok=True)

    logger = get_logger("generator")
    logger.info(f"Starting video generation: {effective_duration} seconds, seed={seed}")

    manifest_entries = []
    handoff_manager = get_handoff_manager()
    chunk_id = 0
    frames_written = 0
    start_time = time.time()

    # Initialize seed if not provided
    if seed is None:
        seed = int(time.time()) % 100000

    # Iterate through the generator
    activity_gen = generate_activity_sequence(effective_duration, seed=seed)

    current_chunk_frames = []
    chunk_start_time = 0.0

    for frame_data in activity_gen:
        # Create SyntheticVideoFrame object
        frame_obj = SyntheticVideoFrame(
            frame_index=frame_data["frame_index"],
            timestamp=frame_data["timestamp"],
            activity=frame_data["activity"],
            is_critical=frame_data["is_critical"],
            confidence=frame_data["confidence"],
            raw_features={} # Placeholder for visual features
        )

        current_chunk_frames.append(frame_obj)
        frames_written += 1

        # Check if chunk is full
        chunk_end_time = frame_data["timestamp"]
        if chunk_end_time - chunk_start_time >= chunk_duration or frames_written >= (chunk_duration * FRAME_RATE):
            # Write chunk to disk
            chunk_filename = f"chunk_{chunk_id:05d}.jsonl"
            chunk_path = output_dir / chunk_filename

            with open(chunk_path, 'w') as f:
                for f_obj in current_chunk_frames:
                    f.write(json.dumps({
                        "frame_index": f_obj.frame_index,
                        "timestamp": f_obj.timestamp,
                        "activity": f_obj.activity,
                        "is_critical": f_obj.is_critical,
                        "confidence": f_obj.confidence
                    }) + "\n")

            # Update handoff manifest
            handoff_entry = {
                "chunk_id": chunk_id,
                "file_path": str(chunk_path),
                "start_frame": current_chunk_frames[0].frame_index,
                "end_frame": current_chunk_frames[-1].frame_index,
                "start_time": chunk_start_time,
                "end_time": chunk_end_time,
                "frame_count": len(current_chunk_frames),
                "status": "completed",
                "written_at": time.time()
            }
            handoff_manager.write_chunk(handoff_entry)
            manifest_entries.append(handoff_entry)

            # Reset chunk
            current_chunk_frames = []
            chunk_id += 1
            if current_chunk_frames:
                chunk_start_time = current_chunk_frames[0].timestamp
            else:
                chunk_start_time = chunk_end_time

    # Write final partial chunk
    if current_chunk_frames:
        chunk_filename = f"chunk_{chunk_id:05d}.jsonl"
        chunk_path = output_dir / chunk_filename
        with open(chunk_path, 'w') as f:
            for f_obj in current_chunk_frames:
                f.write(json.dumps({
                    "frame_index": f_obj.frame_index,
                    "timestamp": f_obj.timestamp,
                    "activity": f_obj.activity,
                    "is_critical": f_obj.is_critical,
                    "confidence": f_obj.confidence
                }) + "\n")

        handoff_entry = {
            "chunk_id": chunk_id,
            "file_path": str(chunk_path),
            "start_frame": current_chunk_frames[0].frame_index,
            "end_frame": current_chunk_frames[-1].frame_index,
            "start_time": chunk_start_time,
            "end_time": current_chunk_frames[-1].timestamp,
            "frame_count": len(current_chunk_frames),
            "status": "completed",
            "written_at": time.time()
        }
        handoff_manager.write_chunk(handoff_entry)
        manifest_entries.append(handoff_entry)

    elapsed = time.time() - start_time
    logger.info(f"Generation complete. Wrote {len(manifest_entries)} chunks, {frames_written} frames in {elapsed:.2f}s.")
    
    # Log that no VLM was used
    log_no_vlm_call("generator", "synthetic_generation", "No VLM calls made during synthetic data generation.")

    return manifest_entries


def main():
    """
    Entry point for the generator script.
    Reads environment variables to determine CI vs Non-CI mode.
    """
    # Validate environment
    required_vars = ["DATA_SEED"]
    try:
        get_required_env_vars(required_vars)
    except ValueError as e:
        print(f"Environment Error: {e}")
        return 1

    seed = int(os.getenv("DATA_SEED", "42"))
    is_ci = os.getenv("CI", "false").lower() == "true"

    # Determine target duration
    target_duration = TARGET_DURATION_SECONDS_FULL
    if is_ci:
        target_duration = TARGET_DURATION_SECONDS_CI
        print(f"Running in CI Mode: Generating {target_duration} seconds (1h) subset.")
    else:
        print(f"Running in Non-CI Mode: Generating {target_duration} seconds (50h).")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Run generation
    try:
        manifest = generate_video_stream(
            duration_seconds=target_duration,
            output_dir=OUTPUT_DIR,
            seed=seed,
            is_ci_mode=is_ci
        )

        # Write manifest summary to stdout for verification
        total_frames = sum(e["frame_count"] for e in manifest)
        total_seconds = total_frames / FRAME_RATE
        print(f"Successfully generated {total_frames} frames ({total_seconds:.2f} seconds) into {len(manifest)} chunks.")
        print(f"Manifest entries written to handoff manager.")
        return 0

    except Exception as e:
        print(f"Generation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
