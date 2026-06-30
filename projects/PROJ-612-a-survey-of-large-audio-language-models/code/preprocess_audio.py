"""
Audio Preprocessing Module for LALM Hallucination Analysis.

Implements:
- Resampling to a standard audio sampling rate (16kHz).
- Truncating or discarding samples > 10 seconds.
- Logging discards and processing stats (FR-002).

Dependencies:
- librosa (for audio loading and resampling)
- logging infrastructure from setup_logging
- config from config
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json

import librosa
import numpy as np

from config import get_audio_config, get_dataset_paths, get_sample_limits
from setup_logging import get_logger, init_logging
from utils import AudioSample

# Constants
TARGET_SAMPLE_RATE = 16000  # Standard for speech/audio models
MAX_DURATION_SECONDS = 10.0
MAX_SAMPLES_PER_SAMPLE = int(TARGET_SAMPLE_RATE * MAX_DURATION_SECONDS)

# Initialize logger for this module
logger = get_logger("preprocess_audio")

def resample_audio(
    audio_data: np.ndarray,
    original_sr: int,
    target_sr: int = TARGET_SAMPLE_RATE
) -> np.ndarray:
    """
    Resamples audio data to the target sample rate.

    Args:
        audio_data: numpy array of audio samples.
        original_sr: Original sample rate of the audio.
        target_sr: Target sample rate (default 16kHz).

    Returns:
        Resampled numpy array.
    """
    if original_sr == target_sr:
        return audio_data

    logger.debug(f"Resampling from {original_sr}Hz to {target_sr}Hz")
    resampled = librosa.resample(
        audio_data,
        orig_sr=original_sr,
        target_sr=target_sr,
        res_type='kaiser_best'
    )
    return resampled

def process_sample(
    sample_path: Path,
    domain: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[Optional[AudioSample], bool]:
    """
    Processes a single audio file: resamples and checks duration.

    Args:
        sample_path: Path to the audio file.
        domain: Domain label (e.g., 'speech', 'music', 'env').
        metadata: Optional metadata dict from the dataset.

    Returns:
        Tuple of (AudioSample object if valid, or None if discarded;
                 boolean indicating if the sample was discarded).
    """
    try:
        # Load audio with librosa (returns mono by default)
        audio_data, sr = librosa.load(str(sample_path), sr=None, mono=True)

        # Check duration before processing
        duration = len(audio_data) / sr

        if duration > MAX_DURATION_SECONDS:
            logger.warning(
                f"Discarding sample '{sample_path.name}' "
                f"(Duration: {duration:.2f}s > {MAX_DURATION_SECONDS}s). "
                f"Domain: {domain}"
            )
            return None, True

        # Resample if necessary
        processed_audio = resample_audio(audio_data, sr, TARGET_SAMPLE_RATE)

        # Re-calculate duration after resampling (should be same, but safe check)
        final_duration = len(processed_audio) / TARGET_SAMPLE_RATE

        # Create AudioSample object
        sample_obj = AudioSample(
            path=str(sample_path),
            domain=domain,
            audio_data=processed_audio,
            sample_rate=TARGET_SAMPLE_RATE,
            duration=final_duration,
            metadata=metadata or {}
        )

        return sample_obj, False

    except Exception as e:
        logger.error(f"Failed to process sample '{sample_path}': {e}", exc_info=True)
        return None, True

def preprocess_dataset(
    dataset_path: Path,
    domain: str,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Preprocesses a list of audio samples from a dataset.

    Args:
        dataset_path: Path to the dataset JSON file (containing list of sample paths/metadata).
        domain: Domain label for the dataset.
        output_dir: Optional directory to save processed audio files (not implemented for memory efficiency,
                    returns objects in memory for pipeline flow).

    Returns:
        Dictionary with statistics: total, processed, discarded, stats per reason.
    """
    if not dataset_path.exists():
        logger.error(f"Dataset path not found: {dataset_path}")
        return {"error": f"Path not found: {dataset_path}"}

    # Load dataset metadata
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset_items = json.load(f)

    if not isinstance(dataset_items, list):
        logger.error(f"Dataset file {dataset_path} does not contain a list of items.")
        return {"error": "Invalid dataset format"}

    processed_samples: List[AudioSample] = []
    discarded_count = 0
    total_count = len(dataset_items)

    logger.info(f"Starting preprocessing for domain '{domain}' from {dataset_path}")
    logger.info(f"Total samples to process: {total_count}")

    for i, item in enumerate(dataset_items):
        # Extract path and metadata
        # Assuming item structure: {"path": "...", "duration": ..., "label": ...} or similar
        # We need to handle the actual structure from T011b output
        file_path = item.get("path") or item.get("file_path") or item.get("audio_path")
        
        if not file_path:
            logger.warning(f"Item {i} in {dataset_path} missing 'path' key. Skipping.")
            discarded_count += 1
            continue

        full_path = Path(file_path)
        
        # If the path is relative and the dataset is in a subfolder, resolve relative to dataset dir
        if not full_path.is_absolute():
            full_path = dataset_path.parent / file_path

        if not full_path.exists():
            logger.warning(f"Audio file not found: {full_path}. Skipping.")
            discarded_count += 1
            continue

        sample_obj, was_discarded = process_sample(full_path, domain, item)

        if was_discarded:
            discarded_count += 1
        elif sample_obj:
            processed_samples.append(sample_obj)

        if (i + 1) % 100 == 0:
            logger.debug(f"Processed {i+1}/{total_count} samples for {domain}")

    stats = {
        "domain": domain,
        "source_file": str(dataset_path),
        "total": total_count,
        "processed": len(processed_samples),
        "discarded": discarded_count,
        "discard_rate": discarded_count / total_count if total_count > 0 else 0.0
    }

    logger.info(f"Preprocessing complete for {domain}: {stats}")
    
    # Note: In a real pipeline, we might return the list of AudioSample objects.
    # However, for large datasets, we might want to save them to disk or stream them.
    # For this task, we return the stats and the list of processed samples.
    return {
        "stats": stats,
        "samples": processed_samples
    }

def main():
    """
    Entry point for running preprocessing on configured datasets.
    """
    init_logging()
    logger.info("Starting Audio Preprocessing Pipeline (T013)")

    # Get configuration
    audio_config = get_audio_config()
    dataset_paths = get_dataset_paths()
    sample_limits = get_sample_limits()

    # Define target domain mappings (based on task description)
    # T011b produces specific JSON files for specific domains
    domain_map = {
        "librispeech": ("speech", dataset_paths.get("librispeech")),
        "fma_small": ("music", dataset_paths.get("fma_small")),
        "esc50": ("env", dataset_paths.get("esc50"))
    }

    all_processed_samples = []
    all_stats = []

    for dataset_name, (domain, path_str) in domain_map.items():
        if not path_str:
            logger.warning(f"No path configured for {dataset_name}, skipping.")
            continue

        path = Path(path_str)
        if not path.exists():
            logger.error(f"Configured path for {dataset_name} does not exist: {path}")
            continue

        logger.info(f"Processing dataset: {dataset_name} (Domain: {domain})")
        
        result = preprocess_dataset(path, domain)
        
        if "error" in result:
            logger.error(f"Failed to process {dataset_name}: {result['error']}")
            continue

        all_stats.append(result["stats"])
        all_processed_samples.extend(result.get("samples", []))

    # Log summary
    total_processed = sum(s["processed"] for s in all_stats)
    total_discarded = sum(s["discarded"] for s in all_stats)
    total_all = sum(s["total"] for s in all_stats)

    logger.info(f"Pipeline Summary:")
    logger.info(f"  Total input samples: {total_all}")
    logger.info(f"  Successfully processed: {total_processed}")
    logger.info(f"  Discarded (>10s or error): {total_discarded}")
    logger.info(f"  Overall discard rate: {total_discarded/total_all if total_all > 0 else 0:.2%}")

    # Save stats to a log file for reproducibility
    stats_output_path = Path("data/preprocessing_stats.json")
    stats_output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_output_path, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, indent=2)
    
    logger.info(f"Preprocessing statistics saved to {stats_output_path}")
    
    # Note: The actual AudioSample objects are in memory here.
    # In a full pipeline, they would be passed to the next stage (Inference).
    # For this task, we verify the logic works by logging and saving stats.

    return all_stats

if __name__ == "__main__":
    main()
