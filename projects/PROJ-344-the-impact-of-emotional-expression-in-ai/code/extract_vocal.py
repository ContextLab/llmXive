"""Vocal prosody extraction using librosa.

Extracts pitch, energy, and tempo features from audio tracks (.wav)
and writes them to data/processed/raw_vocal_features.csv.

Skips execution if synthetic feature data exists (T012_gen path).
Raises FileNotFoundError if no valid audio files are found.
"""
from __future__ import annotations

import csv
import glob
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import librosa
import numpy as np

# Import the tolerant logger from the shared module
# This module (code/visualize.py) defines get_logger which is the canonical source
# for the ReproducibilityLogger used across the project.
# We import it from visualize to satisfy the cross-module contract.
try:
    from visualize import get_logger
except ImportError:
    # Fallback if visualize.py is not yet imported in the path, though it should be.
    # In a real run, logging_config is the source, but visualize defines the tolerant logger.
    # To avoid circular imports or missing definitions, we define a minimal fallback here
    # that matches the signature required by the callers in the "Shared-Module Contract".
    class ReproducibilityLogger:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.name = args[0] if args else kwargs.get("name", "reproducibility")
            self.entries: list = []

        def log(self, *args: Any, **kwargs: Any) -> "ReproducibilityLogger":
            return self

        def __getattr__(self, name: str):
            def _noop(*args: Any, **kwargs: Any) -> None:
                return None
            return _noop

    _GLOBAL_LOGGER: Optional[ReproducibilityLogger] = None

    def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
        global _GLOBAL_LOGGER
        if _GLOBAL_LOGGER is None:
            _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
        return _GLOBAL_LOGGER

logger = get_logger(__name__)


def check_skip_condition() -> bool:
    """Check if synthetic features exist (T012_gen path).

    Returns:
        True if synthetic features exist (skip extraction), False otherwise.
    """
    synthetic_path = "data/processed/synthetic_features.csv"
    if os.path.exists(synthetic_path):
        logger.log("SKIP_CONDITION_MET", reason="Synthetic features exist", path=synthetic_path)
        return True
    return False


def find_audio_files() -> List[str]:
    """Find all .wav files in data/raw/.

    Returns:
        List of paths to .wav files.

    Raises:
        FileNotFoundError: If no .wav files are found.
    """
    pattern = "data/raw/*.wav"
    files = glob.glob(pattern)
    if not files:
        logger.log("NO_FILES_FOUND", pattern=pattern, path="data/raw")
        raise FileNotFoundError(f"No .wav files found in data/raw/ matching '{pattern}'. "
                                "Ensure T012_media has populated the directory with valid audio files.")
    logger.log("AUDIO_FILES_FOUND", count=len(files), files=files)
    return files


def extract_pitch_features(y: np.ndarray, sr: int) -> Dict[str, float]:
    """Extract pitch-related features (F0, variance).

    Args:
        y: Audio time series.
        sr: Sample rate.

    Returns:
        Dictionary with mean_f0, std_f0.
    """
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr
    )
    # Filter out NaNs (unvoiced frames)
    f0_clean = f0[~np.isnan(f0)]
    if len(f0_clean) == 0:
        return {"mean_f0": 0.0, "std_f0": 0.0}
    return {
        "mean_f0": float(np.mean(f0_clean)),
        "std_f0": float(np.std(f0_clean))
    }


def extract_energy_features(y: np.ndarray) -> Dict[str, float]:
    """Extract energy-related features (RMS, variance).

    Args:
        y: Audio time series.

    Returns:
        Dictionary with mean_rms, std_rms.
    """
    rms = librosa.feature.rms(y=y)[0]
    return {
        "mean_rms": float(np.mean(rms)),
        "std_rms": float(np.std(rms))
    }


def extract_tempo(y: np.ndarray, sr: int) -> Dict[str, float]:
    """Extract tempo features.

    Args:
        y: Audio time series.
        sr: Sample rate.

    Returns:
        Dictionary with tempo_bpm, tempo_variance.
    """
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    # tempo is a scalar or array depending on librosa version, ensure float
    if isinstance(tempo, np.ndarray):
        tempo_val = float(np.mean(tempo))
        tempo_std = float(np.std(tempo))
    else:
        tempo_val = float(tempo)
        tempo_std = 0.0
    return {
        "tempo_bpm": tempo_val,
        "tempo_std": tempo_std
    }


def process_audio_file(file_path: str, interaction_id: str) -> Dict[str, Any]:
    """Process a single audio file and extract all features.

    Args:
        file_path: Path to the .wav file.
        interaction_id: ID for the interaction (derived from filename).

    Returns:
        Dictionary containing all extracted features.
    """
    logger.log("PROCESSING_AUDIO", file=file_path, interaction_id=interaction_id)
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        logger.log("AUDIO_LOAD_ERROR", file=file_path, error=str(e))
        # Return a row with zeros or None to allow pipeline to continue/clean
        return {
            "interaction_id": interaction_id,
            "mean_f0": 0.0,
            "std_f0": 0.0,
            "mean_rms": 0.0,
            "std_rms": 0.0,
            "tempo_bpm": 0.0,
            "tempo_std": 0.0,
            "duration_sec": 0.0,
            "sample_rate": sr,
            "valid": False
        }

    pitch_features = extract_pitch_features(y, sr)
    energy_features = extract_energy_features(y)
    tempo_features = extract_tempo(y, sr)

    duration = float(len(y) / sr)

    return {
        "interaction_id": interaction_id,
        **pitch_features,
        **energy_features,
        **tempo_features,
        "duration_sec": duration,
        "sample_rate": sr,
        "valid": True
    }


def extract_vocal_prosody() -> List[Dict[str, Any]]:
    """Main extraction logic.

    Returns:
        List of dictionaries, one per interaction.
    """
    if check_skip_condition():
        return []

    audio_files = find_audio_files()
    results = []

    for file_path in audio_files:
        # Derive interaction_id from filename (remove extension)
        interaction_id = os.path.splitext(os.path.basename(file_path))[0]
        row = process_audio_file(file_path, interaction_id)
        results.append(row)

    logger.log("EXTRACTION_COMPLETE", total_processed=len(results))
    return results


def write_output(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write results to CSV.

    Args:
        results: List of feature dictionaries.
        output_path: Path to the output CSV file.
    """
    if not results:
        logger.log("NO_RESULTS_TO_WRITE", path=output_path)
        # Create an empty file with headers if no results
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["interaction_id", "mean_f0", "std_f0", "mean_rms", "std_rms",
                             "tempo_bpm", "tempo_std", "duration_sec", "sample_rate", "valid"])
        return

    fieldnames = results[0].keys()
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    logger.log("OUTPUT_WRITTEN", path=output_path, rows=len(results))


def main() -> None:
    """Entry point for the vocal extraction task."""
    output_path = "data/processed/raw_vocal_features.csv"
    logger.log("STARTING_VOCAL_EXTRACTION", output_path=output_path)

    try:
        results = extract_vocal_prosody()
        write_output(results, output_path)
        logger.log("TASK_COMPLETE", status="success")
    except FileNotFoundError as e:
        logger.log("TASK_FAILED", status="file_not_found", error=str(e))
        # Re-raise to indicate failure to the pipeline orchestrator
        raise
    except Exception as e:
        logger.log("TASK_FAILED", status="unexpected_error", error=str(e))
        raise


if __name__ == "__main__":
    main()
