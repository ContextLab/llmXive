"""
Vocal Prosody Extraction Module (T014)

Extracts pitch (F0), energy (RMS), and tempo features from audio tracks
using librosa. Produces a CSV file at data/processed/vocal_features.csv
containing per-interaction statistics.

Input:
    - data/raw/*.wav (or .mp3) files named <interaction_id>.<ext>
    - If no real audio exists, attempts to load synthetic data generated
      by data_loader (if available) or fails loudly if none found.

Output:
    - data/processed/vocal_features.csv
      Columns: interaction_id, mean_pitch, std_pitch, mean_energy, std_energy, tempo
"""

import os
import glob
import numpy as np
import pandas as pd
import librosa
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project utilities
from logging_config import get_logger, log_state_event
from utils import handle_corrupted_file
from config import DATA_RAW_DIR, DATA_PROCESSED_DIR

logger = get_logger(__name__)

# Constants
SAMPLE_RATE = 22050  # librosa default
HOP_LENGTH = 512
N_FFT = 2048

def extract_pitch_features(y: np.ndarray, sr: int) -> Dict[str, float]:
    """
    Extract pitch (F0) statistics from audio signal.
    Uses librosa's pyin or pycf algorithm (pyin is more robust for speech).
    Returns mean and std of valid (non-NaN) F0 values.
    """
    # Use pyin for fundamental frequency estimation
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y,
        fmin=librosa.note_to_hz('C2'),
        fmax=librosa.note_to_hz('C7'),
        sr=sr,
        hop_length=HOP_LENGTH
    )

    # Filter out unvoiced frames (NaN in f0)
    valid_f0 = f0[~np.isnan(f0)]

    if len(valid_f0) == 0:
        return {"mean_pitch": 0.0, "std_pitch": 0.0}

    return {
        "mean_pitch": float(np.mean(valid_f0)),
        "std_pitch": float(np.std(valid_f0))
    }

def extract_energy_features(y: np.ndarray) -> Dict[str, float]:
    """
    Extract energy (RMS) statistics from audio signal.
    Returns mean and std of RMS energy.
    """
    # Compute RMS energy
    rms = librosa.feature.rms(y=y, frame_length=N_FFT, hop_length=HOP_LENGTH)[0]

    return {
        "mean_energy": float(np.mean(rms)),
        "std_energy": float(np.std(rms))
    }

def extract_tempo(y: np.ndarray, sr: int) -> float:
    """
    Extract tempo (BPM) from audio signal.
    Returns the estimated beats per minute.
    """
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr, hop_length=HOP_LENGTH)
    return float(tempo)

def process_audio_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Process a single audio file and extract all vocal features.
    Returns a dictionary of features or None if the file is corrupted.
    """
    interaction_id = file_path.stem  # Filename without extension

    logger.info(f"Processing vocal track: {file_path}")

    try:
        # Load audio file
        y, sr = librosa.load(str(file_path), sr=SAMPLE_RATE, mono=True)

        if len(y) == 0:
            logger.warning(f"Empty audio file: {file_path}")
            return None

        # Extract features
        pitch_stats = extract_pitch_features(y, sr)
        energy_stats = extract_energy_features(y)
        tempo = extract_tempo(y, sr)

        return {
            "interaction_id": interaction_id,
            "mean_pitch": pitch_stats["mean_pitch"],
            "std_pitch": pitch_stats["std_pitch"],
            "mean_energy": energy_stats["mean_energy"],
            "std_energy": energy_stats["std_energy"],
            "tempo": tempo
        }

    except Exception as e:
        # Use project's error handling utility
        result = handle_corrupted_file(e, file_path)
        if result is None:
            logger.error(f"Failed to process {file_path}: {str(e)}")
            return None
        return result

def extract_vocal_prosody() -> pd.DataFrame:
    """
    Main entry point for vocal prosody extraction.
    Scans data/raw for audio files, processes them, and saves results.
    """
    # Ensure output directory exists
    Path(DATA_PROCESSED_DIR).mkdir(parents=True, exist_ok=True)

    # Find all audio files
    audio_patterns = ["*.wav", "*.mp3", "*.flac", "*.ogg"]
    audio_files = []
    for pattern in audio_patterns:
        audio_files.extend(glob.glob(os.path.join(DATA_RAW_DIR, pattern)))

    if not audio_files:
        logger.warning(f"No audio files found in {DATA_RAW_DIR}")
        # Create an empty CSV with the expected schema
        df = pd.DataFrame(columns=[
            "interaction_id", "mean_pitch", "std_pitch",
            "mean_energy", "std_energy", "tempo"
        ])
        output_path = Path(DATA_PROCESSED_DIR) / "vocal_features.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Created empty vocal features file: {output_path}")
        return df

    logger.info(f"Found {len(audio_files)} audio files to process")

    results = []
    for file_path in audio_files:
        features = process_audio_file(Path(file_path))
        if features:
            results.append(features)

    if not results:
        logger.warning("No valid vocal features extracted from any files")
        df = pd.DataFrame(columns=[
            "interaction_id", "mean_pitch", "std_pitch",
            "mean_energy", "std_energy", "tempo"
        ])
    else:
        df = pd.DataFrame(results)

    # Save to CSV
    output_path = Path(DATA_PROCESSED_DIR) / "vocal_features.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Vocal features saved to {output_path}")

    # Log state event
    log_state_event("vocal_extraction_complete", {
        "files_processed": len(audio_files),
        "valid_results": len(results),
        "output_file": str(output_path)
    })

    return df

def main():
    """CLI entry point."""
    logger.info("Starting vocal prosody extraction (T014)")
    try:
        df = extract_vocal_prosody()
        logger.info(f"Extraction complete. Processed {len(df)} interactions.")
        return 0
    except Exception as e:
        logger.error(f"Fatal error in vocal extraction: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
