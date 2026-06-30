"""
Dataset loading logic for LibriSpeech (Speech), FMA Small (Music), and ESC-50 (Env).

This module implements the data loading functionality required for User Story 1.
It loads pre-converted JSON artifacts (produced by T011b) and returns structured
AudioSample objects.

Dependencies:
- config.py: For dataset paths and sample limits.
- utils.py: For AudioSample dataclass.
- setup_logging.py: For logging.
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_dataset_paths, get_sample_limits, get_audio_config
from utils import AudioSample
from setup_logging import get_logger, log_error

# Initialize logger for this module
logger = get_logger(__name__)


def load_json_dataset(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load a dataset from a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        List of dictionaries representing the dataset records.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not file_path.exists():
        error_msg = f"Dataset file not found: {file_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                error_msg = f"Expected JSON list in {file_path}, got {type(data)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            return data
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in {file_path}: {e}"
        logger.error(error_msg)
        raise


def _normalize_audio_path(record: Dict[str, Any], base_dir: Path) -> Optional[Path]:
    """
    Normalize the audio file path from a dataset record.

    Handles both absolute and relative paths, and common key variations.
    """
    path_keys = ['audio_path', 'path', 'file', 'audio_file', 'filename']
    raw_path = None
    for key in path_keys:
        if key in record:
            raw_path = record[key]
            break

    if not raw_path:
        return None

    # Handle absolute paths or paths that are already valid relative to base_dir
    candidate = Path(raw_path)
    if candidate.is_absolute():
        if candidate.exists():
            return candidate
        # If absolute path doesn't exist, try treating it as relative to base_dir
        candidate = base_dir / raw_path

    if not candidate.is_absolute():
        candidate = base_dir / raw_path

    if candidate.exists():
        return candidate

    # If still not found, log warning and return None (caller handles missing)
    logger.warning(f"Audio file not found for record: {raw_path} (resolved to {candidate})")
    return None


def load_librispeech_samples(limit: Optional[int] = None) -> List[AudioSample]:
    """
    Load LibriSpeech samples (Speech domain).

    Expects data/raw/librispeech/dev-clean.json to exist (produced by T011b).
    """
    dataset_paths = get_dataset_paths()
    limits = get_sample_limits()

    file_path = dataset_paths.get('librispeech')
    if not file_path:
        # Fallback to standard path if config is missing
        base = Path("data/raw/librispeech")
        file_path = base / "dev-clean.json"

    logger.info(f"Loading LibriSpeech dataset from {file_path}")
    raw_data = load_json_dataset(file_path)

    # Apply limit if specified (global or domain-specific)
    domain_limit = limits.get('speech', limits.get('all'))
    if limit is not None:
        domain_limit = limit
    elif domain_limit is not None:
        raw_data = raw_data[:domain_limit]

    samples = []
    base_dir = file_path.parent.parent  # data/raw/librispeech
    for record in raw_data:
        audio_path = _normalize_audio_path(record, base_dir)
        if audio_path is None:
            continue

        # Extract text/transcription
        text_keys = ['transcription', 'text', 'label', 'sentence']
        text = None
        for key in text_keys:
            if key in record:
                text = record[key]
                break

        # Extract metadata
        sample_id = record.get('id', record.get('sample_id', str(len(samples))))
        duration = record.get('duration', 0.0)

        samples.append(AudioSample(
            id=sample_id,
            domain="speech",
            audio_path=str(audio_path),
            ground_truth=text,
            duration=duration,
            raw_metadata=record
        ))

    logger.info(f"Loaded {len(samples)} LibriSpeech samples.")
    return samples


def load_fma_samples(limit: Optional[int] = None) -> List[AudioSample]:
    """
    Load FMA Small samples (Music domain).

    Expects data/raw/fma_small/metadata.json to exist (produced by T011b).
    """
    dataset_paths = get_dataset_paths()
    limits = get_sample_limits()

    file_path = dataset_paths.get('fma_small')
    if not file_path:
        base = Path("data/raw/fma_small")
        file_path = base / "metadata.json"

    logger.info(f"Loading FMA Small dataset from {file_path}")
    raw_data = load_json_dataset(file_path)

    domain_limit = limits.get('music', limits.get('all'))
    if limit is not None:
        domain_limit = limit
    elif domain_limit is not None:
        raw_data = raw_data[:domain_limit]

    samples = []
    base_dir = file_path.parent  # data/raw/fma_small
    for record in raw_data:
        audio_path = _normalize_audio_path(record, base_dir)
        if audio_path is None:
            continue

        # Extract genre or tags as ground truth for music
        text_keys = ['genre', 'tags', 'title', 'label']
        text = None
        for key in text_keys:
            if key in record:
                text = record[key]
                if isinstance(text, list):
                    text = ", ".join(text)
                break

        sample_id = record.get('id', record.get('track_id', str(len(samples))))
        duration = record.get('duration', 0.0)

        samples.append(AudioSample(
            id=sample_id,
            domain="music",
            audio_path=str(audio_path),
            ground_truth=text,
            duration=duration,
            raw_metadata=record
        ))

    logger.info(f"Loaded {len(samples)} FMA Small samples.")
    return samples


def load_esc50_samples(limit: Optional[int] = None) -> List[AudioSample]:
    """
    Load ESC-50 samples (Environment domain).

    Expects data/raw/esc50/esc50.json to exist (produced by T011b).
    """
    dataset_paths = get_dataset_paths()
    limits = get_sample_limits()

    file_path = dataset_paths.get('esc50')
    if not file_path:
        base = Path("data/raw/esc50")
        file_path = base / "esc50.json"

    logger.info(f"Loading ESC-50 dataset from {file_path}")
    raw_data = load_json_dataset(file_path)

    domain_limit = limits.get('env', limits.get('all'))
    if limit is not None:
        domain_limit = limit
    elif domain_limit is not None:
        raw_data = raw_data[:domain_limit]

    samples = []
    base_dir = file_path.parent  # data/raw/esc50
    for record in raw_data:
        audio_path = _normalize_audio_path(record, base_dir)
        if audio_path is None:
            continue

        # Extract category/label as ground truth
        text_keys = ['category', 'label', 'description', 'text']
        text = None
        for key in text_keys:
            if key in record:
                text = record[key]
                break

        sample_id = record.get('id', record.get('filename', str(len(samples))))
        # ESC-50 usually has 5s clips
        duration = record.get('duration', 5.0)

        samples.append(AudioSample(
            id=sample_id,
            domain="env",
            audio_path=str(audio_path),
            ground_truth=text,
            duration=duration,
            raw_metadata=record
        ))

    logger.info(f"Loaded {len(samples)} ESC-50 samples.")
    return samples


def load_all_datasets(limit_per_domain: Optional[int] = None) -> Dict[str, List[AudioSample]]:
    """
    Load all datasets (Speech, Music, Env) and return them in a dictionary.

    Args:
        limit_per_domain: Optional limit for each domain. If None, uses config limits.

    Returns:
        Dictionary with keys 'speech', 'music', 'env' mapping to lists of AudioSample.
    """
    logger.info("Starting to load all datasets.")

    speech_samples = load_librispeech_samples(limit=limit_per_domain)
    music_samples = load_fma_samples(limit=limit_per_domain)
    env_samples = load_esc50_samples(limit=limit_per_domain)

    result = {
        "speech": speech_samples,
        "music": music_samples,
        "env": env_samples
    }

    total = sum(len(v) for v in result.values())
    logger.info(f"Total samples loaded: {total} (Speech: {len(speech_samples)}, Music: {len(music_samples)}, Env: {len(env_samples)})")
    return result


def main():
    """
    Main entry point for testing dataset loading.
    """
    init_logging()
    logger.info("Running dataset loading test.")

    try:
        data = load_all_datasets()
        logger.info("Dataset loading completed successfully.")

        # Print summary
        for domain, samples in data.items():
            logger.info(f"{domain.upper()}: {len(samples)} samples")
            if samples:
                logger.info(f"  Example: {samples[0].id} -> {samples[0].ground_truth[:50]}...")

    except Exception as e:
        log_error(e)
        raise


if __name__ == "__main__":
    main()