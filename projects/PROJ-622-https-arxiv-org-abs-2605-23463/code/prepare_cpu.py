#!/usr/bin/env python3
"""
CPU-Tractable Adaptation of StepAudio 2.5 Data Preparation.

Original Goal: Slice 7385+ long-form audio segments from large .opus files 
using ffmpeg in parallel, generating a dataset for training unified audio-language models.

Adaptation Strategy:
1. **No External Audio Files**: The original requires a massive external dataset 
   (WenetSpeech) and ffmpeg. We cannot assume these exist or fit in the CI environment.
2. **Synthetic Data Generation**: We generate a small, deterministic set of 
   "simulated" audio features (numpy arrays) and corresponding text transcripts.
   This mimics the *structure* of the output (sid, text, audio data) without 
   the heavy I/O and GPU dependencies.
3. **CPU-Only & Fast**: Uses only `numpy` and `json`. Runs in < 10 seconds.
4. **Output Compatibility**: Produces the same logical artifacts (text file, 
   JSON manifest of audio info) that a downstream StepAudio 2.5 trainer would 
   expect, but with synthetic data.

This script validates the *data pipeline logic* of the paper (handling segments, 
IDs, and text) rather than the heavy audio processing.
"""

import argparse
import json
import os
import sys
import random
from pathlib import Path
import numpy as np

# Try to import audio libraries for a "real" feel if available, 
# but fallback to pure numpy if not (ensuring it runs on minimal CI).
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

def generate_synthetic_audio_segment(duration_seconds: float, sample_rate: int = 16000) -> np.ndarray:
    """
    Generates a short synthetic audio signal.
    Uses a mix of sine waves and noise to simulate speech-like complexity.
    """
    t = np.linspace(0, duration_seconds, int(duration_seconds * sample_rate), endpoint=False)
    
    # Base frequency (approximate pitch)
    f0 = random.uniform(80, 250) 
    signal = 0.5 * np.sin(2 * np.pi * f0 * t)
    
    # Add harmonics and noise to simulate speech texture
    signal += 0.2 * np.sin(2 * np.pi * f0 * 2 * t)
    signal += 0.1 * np.random.randn(len(t))
    
    # Normalize to [-1, 1]
    if signal.max() > 0:
        signal = signal / signal.max() * 0.9
        
    return signal

def prepare_synthetic_dataset(output_dir: str, num_samples: int = 100, seed: int = 42):
    """
    Creates a small, self-contained dataset mimicking the WenetSpeech test_net structure.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    output_path = Path(output_dir)
    wav_dir = output_path / "wavs"
    wav_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample texts representing ASR/TTS pairs
    sample_texts = [
        "The quick brown fox jumps over the lazy dog.",
        "StepAudio 2.5 unifies speech understanding and generation.",
        "Reinforcement learning from human feedback improves alignment.",
        "Automatic speech recognition is a challenging task.",
        "Text to synthesis requires precise prosody modeling.",
        "Realtime dialogue systems need low latency responses.",
        "Audio language models are the future of multimodal AI.",
        "GPU acceleration is not available in this CPU-only adaptation.",
        "This is a synthetic segment for testing the pipeline.",
        "The system successfully processed the audio input."
    ]

    tasks = []
    text_lines = []
    metadata = []

    print(f"Generating {num_samples} synthetic audio segments...")

    for i in range(num_samples):
        sid = f"syn_seg_{i:05d}"
        # Random duration between 1 and 5 seconds
        duration = random.uniform(1.0, 5.0)
        text = random.choice(sample_texts)
        
        # Generate audio
        audio_data = generate_synthetic_audio_segment(duration, 16000)
        
        # Save as .npy (CPU friendly, no ffmpeg needed)
        # We use .npy instead of .wav to avoid dependency on scipy/wave in CI 
        # and keep it strictly numpy-based.
        out_path = wav_dir / f"{sid}.npy"
        np.save(out_path, audio_data)
        
        tasks.append(sid)
        text_lines.append(f"{sid}\t{text}")
        
        metadata.append({
            "sid": sid,
            "duration": duration,
            "sample_rate": 16000,
            "text": text,
            "file": str(out_path.relative_to(output_path))
        })

    # Write text file (mimicking original output format)
    text_path = output_path / "text"
    with open(text_path, "w", encoding="utf-8") as f:
        f.write("\n".join(text_lines) + "\n")
    
    # Write metadata JSON (for verification and downstream loading)
    meta_path = output_path / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nDone.")
    print(f"  Generated: {len(tasks)} segments")
    print(f"  WAVs (NPY): {wav_dir}")
    print(f"  Text: {text_path}")
    print(f"  Metadata: {meta_path}")

def main():
    parser = argparse.ArgumentParser(description="CPU-Tractable Data Preparation for StepAudio 2.5")
    parser.add_argument("--output-dir", type=str, default="data/synthetic_wenet", 
                        help="Output directory for synthetic data")
    parser.add_argument("--num-samples", type=int, default=100,
                        help="Number of synthetic segments to generate")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    
    args = parser.parse_args()

    try:
        prepare_synthetic_dataset(
            output_dir=args.output_dir,
            num_samples=args.num_samples,
            seed=args.seed
        )
    except Exception as e:
        print(f"ERROR: Failed to prepare dataset: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
