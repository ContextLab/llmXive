"""
Preprocess audio files for embedding extraction.

This module loads audio files using librosa, normalizes them to a standard
sample rate and amplitude, and handles corrupted files gracefully by
logging errors and skipping them.
"""

import os
import logging
import librosa
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import PROJECT_ROOT, set_seed, ensure_directories
from utils.logging import setup_logging, get_logger
from utils.memory_monitor import update_peak_memory, check_memory_limit

# Constants
TARGET_SAMPLE_RATE: int = 16000
NORMALIZE_DB: int = -20  # Target loudness in dB
CHUNK_SIZE: int = 100  # Number of files to process before checking memory

def load_audio_file(
    file_path: Path,
    target_sr: int = TARGET_SAMPLE_RATE,
    normalize: bool = True
) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """
    Load a single audio file using librosa.

    Args:
        file_path: Path to the audio file.
        target_sr: Target sample rate for resampling.
        normalize: Whether to normalize amplitude.

    Returns:
        Tuple of (audio_data, error_message).
        If successful, error_message is None.
        If failed, audio_data is None and error_message describes the issue.
    """
    try:
        # Load audio with librosa
        # mono=True ensures we get a 1D array
        # sr=target_sr resamples on the fly if needed
        audio_data, sr = librosa.load(
            str(file_path),
            sr=target_sr,
            mono=True,
            res_type='kaiser_fast'
        )

        if audio_data is None or len(audio_data) == 0:
            return None, f"Empty audio loaded from {file_path}"

        if normalize:
            # Normalize to target loudness
            # librosa.util.normalize normalizes to unit norm by default,
            # but we want specific dB target.
            # Calculate current RMS and adjust
            rms = np.sqrt(np.mean(audio_data**2))
            if rms > 0:
                # Convert to dB
                current_db = 20 * np.log10(rms)
                target_linear = 10 ** (NORMALIZE_DB / 20)
                # Scale factor
                scale = target_linear / rms
                audio_data = audio_data * scale

        update_peak_memory()
        return audio_data, None

    except librosa.LibrosaError as e:
        return None, f"Librosa error loading {file_path}: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error loading {file_path}: {str(e)}"

def preprocess_audio_batch(
    input_files: List[Path],
    output_dir: Path,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Process a batch of audio files.

    Args:
        input_files: List of paths to audio files.
        output_dir: Directory to save processed audio (optional, currently just logs).
        logger: Logger instance.

    Returns:
        Dictionary with processing statistics.
    """
    if logger is None:
        logger = get_logger(__name__)

    stats = {
        'total': len(input_files),
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }

    processed_data = []

    for i, file_path in enumerate(input_files):
        # Check memory periodically
        if i % CHUNK_SIZE == 0 and i > 0:
            if not check_memory_limit():
                logger.warning("Memory limit reached during batch processing. Stopping.")
                break

        # Check if file exists
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            stats['skipped'] += 1
            continue

        # Load and process
        audio_data, error = load_audio_file(file_path)

        if error:
            logger.error(error)
            stats['failed'] += 1
            stats['errors'].append({
                'file': str(file_path),
                'error': error
            })
        else:
            logger.debug(f"Successfully processed: {file_path.name} (length: {len(audio_data)} samples)")
            stats['success'] += 1
            processed_data.append({
                'file': str(file_path),
                'data': audio_data,
                'sr': TARGET_SAMPLE_RATE
            })

    logger.info(f"Preprocessing complete: {stats['success']} success, {stats['failed']} failed, {stats['skipped']} skipped")
    return stats

def main():
    """Main entry point for preprocessing."""
    # Setup logging
    logger = setup_logging()
    logger.info("Starting audio preprocessing pipeline")

    # Set seed for reproducibility
    set_seed(42)

    # Define paths
    raw_data_dir = PROJECT_ROOT / "data" / "raw"
    processed_dir = PROJECT_ROOT / "data" / "processed"
    ensure_directories([processed_dir])

    # Check if raw data exists
    if not raw_data_dir.exists():
        logger.error(f"Raw data directory not found: {raw_data_dir}")
        logger.error("Please run data/download.py first to download the dataset.")
        return

    # Collect audio files
    audio_extensions = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aiff'}
    audio_files = []

    for ext in audio_extensions:
        audio_files.extend(raw_data_dir.glob(f"**/*{ext}"))
        audio_files.extend(raw_data_dir.glob(f"**/*{ext.upper()}"))

    # Remove duplicates (in case of case-insensitive matching)
    audio_files = list(set(audio_files))

    if not audio_files:
        logger.warning(f"No audio files found in {raw_data_dir}")
        logger.warning("Skipping preprocessing.")
        return

    logger.info(f"Found {len(audio_files)} audio files to process")

    # Process in batches to manage memory
    batch_size = 50
    all_stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0, 'errors': []}

    for i in range(0, len(audio_files), batch_size):
        batch = audio_files[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} files)")

        batch_stats = preprocess_audio_batch(batch, processed_dir, logger)

        # Aggregate stats
        all_stats['total'] += batch_stats['total']
        all_stats['success'] += batch_stats['success']
        all_stats['failed'] += batch_stats['failed']
        all_stats['skipped'] += batch_stats['skipped']
        all_stats['errors'].extend(batch_stats['errors'])

        # Force garbage collection between batches
        import gc
        gc.collect()

    # Write summary report
    report_path = processed_dir / "preprocessing_report.json"
    with open(report_path, 'w') as f:
        import json
        json.dump(all_stats, f, indent=2, default=str)

    logger.info(f"Preprocessing report saved to {report_path}")
    logger.info(f"Final stats: {all_stats['success']} processed, {all_stats['failed']} failed, {all_stats['skipped']} skipped")

if __name__ == "__main__":
    main()