"""
Dataset Download and Fallback Generation Module.

Implements FR-007 (Label Independence) and FR-005 (Data Generation).
Attempts to fetch a verified LALM (or suitable audio) subset. If unavailable,
generates a verified benign dataset using deterministic sine‑wave “TTS” plus
Gaussian noise. The resulting manifest is saved to `data/dataset_manifest.json`.
"""
import json
import logging
import os
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import soundfile as sf
from datasets import load_dataset
from scipy.signal import resample

# Local imports based on project API surface
from src.utils.logging_config import get_logger
from src.utils.env_config import enforce_cpu_only

# Enforce CPU‑only mode before any heavy libraries are imported
enforce_cpu_only()

logger: logging.Logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
DATA_DIR = Path("data")
RAW_AUDIO_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FALLBACK_DIR = DATA_DIR / "fallback"

SAMPLE_RATE = 16000
DURATION_SECONDS = 5.0
NUM_FALLBACK_SAMPLES = 50  # Small set for verification / fallback

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def ensure_dirs() -> None:
    """Create necessary directories for raw, processed and fallback data."""
    for directory in (RAW_AUDIO_DIR, PROCESSED_DIR, FALLBACK_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directories: {RAW_AUDIO_DIR}, {PROCESSED_DIR}, {FALLBACK_DIR}")

def generate_synthetic_benign_data(output_dir: Path, num_samples: int = NUM_FALLBACK_SAMPLES) -> List[Dict[str, Any]]:
    """
    Generate a synthetic “verified benign” dataset.

    Each sample consists of a deterministic sine‑wave (as a lightweight TTS proxy)
    mixed with Gaussian noise. The audio is saved as a 16 kHz WAV file and a
    corresponding manifest entry is created.

    Args:
        output_dir: Directory where the WAV files and manifest will be written.
        num_samples: Number of synthetic samples to generate.

    Returns:
        A list of manifest dictionaries for the generated samples.
    """
    logger.info(f"Generating {num_samples} synthetic benign samples in {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest: List[Dict[str, Any]] = []

    t = np.linspace(0, DURATION_SECONDS, int(SAMPLE_RATE * DURATION_SECONDS), endpoint=False)

    for i in range(num_samples):
        # Deterministic sine‑wave with slight frequency modulation
        freq = 200 + 50 * np.sin(2 * np.pi * 2 * t)  # 200 Hz base, modulated
        audio_tts = 0.5 * np.sin(2 * np.pi * freq * t)

        # Gaussian noise
        audio_noise = np.random.normal(0, 0.1, t.shape)

        # Mix: 70 % TTS‑like, 30 % noise
        mixed_audio = 0.7 * audio_tts + 0.3 * audio_noise

        # Normalise to avoid clipping
        mixed_audio = mixed_audio / np.max(np.abs(mixed_audio)) * 0.9

        filename = f"benign_synth_{i:04d}.wav"
        filepath = output_dir / filename

        sf.write(str(filepath), mixed_audio, SAMPLE_RATE)

        manifest.append({
            "id": f"synthetic_{i:04d}",
            "file": str(filepath),
            "label": "benign",
            "source": "synthetic_fallback",
            "type": "tts_plus_noise"
        })

    manifest_path = output_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Synthetic manifest written to {manifest_path}")

    return manifest

def fetch_lalm_subset() -> Tuple[List[Dict[str, Any]], bool]:
    """
    Attempt to fetch a small subset of a real audio dataset.

    The function first tries to load the `librispeech_asr` clean split
    (a widely‑available, verified audio corpus). If successful, the first
    ``NUM_FALLBACK_SAMPLES`` samples are saved locally and a manifest is
    returned. If any error occurs (e.g., network failure, missing dataset),
    the function falls back to synthetic generation.

    Returns:
        (manifest, success_flag)
    """
    logger.info("Attempting to fetch a verified audio subset (librispeech_asr).")
    try:
        # Load a streaming subset to keep memory usage low
        dataset = load_dataset("librispeech_asr", "clean", split="train.100", streaming=True)

        manifest: List[Dict[str, Any]] = []
        count = 0
        for item in dataset:
            if count >= NUM_FALLBACK_SAMPLES:
                break

            audio_array = item["audio"]["array"]
            orig_sr = item["audio"]["sampling_rate"]

            # Resample to the target SAMPLE_RATE if needed
            if orig_sr != SAMPLE_RATE:
                audio_array = resample(audio_array, int(len(audio_array) * SAMPLE_RATE / orig_sr))

            filename = f"librispeech_{count:04d}.wav"
            filepath = RAW_AUDIO_DIR / filename
            sf.write(str(filepath), audio_array, SAMPLE_RATE)

            manifest.append({
                "id": f"librispeech_{count:04d}",
                "file": str(filepath),
                "label": "benign",
                "source": "librispeech_asr",
                "type": "speech"
            })
            count += 1

        logger.info(f"Fetched {len(manifest)} samples from librispeech_asr.")
        return manifest, True

    except Exception as exc:
        logger.warning(f"Failed to fetch real audio dataset: {exc}")
        return [], False

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> List[Dict[str, Any]]:
    """
    Orchestrate dataset acquisition.

    1. Ensure required directories exist.
    2. Try to fetch a verified audio subset.
    3. If fetching fails, generate synthetic fallback data.
    4. Write a unified manifest to ``data/dataset_manifest.json``.
    """
    ensure_dirs()

    # Step 1: Try to obtain real data
    manifest, success = fetch_lalm_subset()

    # Step 2: Fallback if needed
    if not success or not manifest:
        logger.warning("Real dataset fetch unsuccessful – generating synthetic fallback data.")
        manifest = generate_synthetic_benign_data(FALLBACK_DIR)

    # Step 3: Persist manifest
    manifest_path = DATA_DIR / "dataset_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Dataset manifest written to {manifest_path}")

    # Provide a simple CLI‑style printout for human users
    print(f"Dataset ready: {len(manifest)} samples. Manifest saved at {manifest_path}")

    return manifest

if __name__ == "__main__":
    main()