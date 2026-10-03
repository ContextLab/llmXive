"""
Synthetic Media Generation (T012_media)

Generates synthetic video (MP4) and audio (WAV) files that mimic the temporal structure
of real interactions. Used as a fallback when real data is unavailable.

Schema:
- Video: 15fps, 320x240, 5s duration.
- Audio: 44100Hz, 16-bit mono, 5s duration.

This module is imported by code/extract_features.py.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from code.logging_config import get_logger
except ImportError:
    from logging_config import get_logger

logger = get_logger(__name__)

def generate_synthetic_media_batch(
    n: int = 10,
    signal: bool = False,
    null: bool = False,
    output_dir: str = "data/raw"
) -> Optional[Dict[str, List[str]]]:
    """
    Generate N synthetic video and audio files.
    
    Args:
        n: Number of samples.
        signal: If True, include a synthetic 'signal' pattern.
        null: If True, generate noise-only (null) data.
        output_dir: Directory to save files.
    
    Returns:
        Dict with keys 'videos' and 'audios' containing lists of file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    videos = []
    audios = []
    
    # Generate audio first (easier to create raw data)
    for i in range(n):
        sample_id = f"synthetic_{i:03d}"
        
        # 1. Generate Audio (WAV)
        # 5 seconds @ 44100 Hz
        duration = 5.0
        sr = 44100
        t = np.linspace(0, duration, int(sr * duration))
        
        if null:
            # Pure noise
            audio_data = np.random.normal(0, 0.1, len(t))
        elif signal:
            # Signal + noise (e.g., a sine wave with varying frequency)
            # Simulate emotional prosody: frequency modulation
            freq = 200 + 50 * np.sin(2 * np.pi * 0.5 * t)
            audio_data = 0.5 * np.sin(2 * np.pi * freq * t) + 0.05 * np.random.normal(0, 1, len(t))
        else:
            # Default: simple tone
            audio_data = 0.5 * np.sin(2 * np.pi * 220 * t) + 0.05 * np.random.normal(0, 1, len(t))
        
        # Normalize to 16-bit range
        audio_data = np.clip(audio_data, -1, 1)
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        audio_path = os.path.join(output_dir, f"{sample_id}.wav")
        # Write WAV using scipy or raw bytes + header
        # Since scipy might not be installed, let's use a simple header + data
        # Or use soundfile if available. Let's try soundfile, fallback to raw.
        try:
            import soundfile as sf
            sf.write(audio_path, audio_int16, sr, subtype='PCM_16')
        except ImportError:
            # Fallback: write raw PCM with simple WAV header
            # This is a minimal implementation for compatibility
            import wave
            with wave.open(audio_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sr)
                wav_file.writeframes(audio_int16.tobytes())
        
        audios.append(audio_path)
        
        # 2. Generate Video (MP4)
        # 15fps, 320x240, 5s -> 75 frames
        # We generate a simple colored rectangle that moves slightly to mimic face
        # We use ffmpeg to generate this from a raw video stream or image sequence
        # To avoid heavy dependencies, we generate a simple pattern using ffmpeg's lavfi
        
        video_path = os.path.join(output_dir, f"{sample_id}.mp4")
        
        # Create a simple video using ffmpeg with color source and overlay
        # This command generates a 5s video with a moving colored box
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=blue:s=320x240:d={duration}:r=15",
            "-vf", f"drawbox=x=50:y=50:w=220:h=140:t=fill:c=red@0.5",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            video_path
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            videos.append(video_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate video {video_path}: {e}")
            # If ffmpeg fails, we might not have a video, but we have audio.
            # The extraction script should handle missing video gracefully.
            # We do not add to videos list.
            continue
        
        # 3. Generate Metadata (JSON) for the interaction
        # This mimics the schema expected by the extraction logic
        meta = {
            "interaction_id": sample_id,
            "duration": duration,
            "audio_path": audio_path,
            "video_path": video_path if os.path.exists(video_path) else None
        }
        meta_path = os.path.join(output_dir, f"{sample_id}.json")
        with open(meta_path, "w") as f:
            json.dump(meta, f)
    
    if not videos and not audios:
        logger.error("Failed to generate any synthetic media.")
        return None
        
    return {"videos": videos, "audios": audios}
