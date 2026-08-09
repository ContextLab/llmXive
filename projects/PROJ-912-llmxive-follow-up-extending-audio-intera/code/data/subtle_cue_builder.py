"""
Audio Feature Extraction and Class Configuration Builder for Subtle Cue Detection.

This module implements:
1. Loading raw audio from ESC-50 and UrbanSound8K datasets.
2. Computing dominant frequency (STFT peak) and amplitude (RMS) for each file.
3. Generating a lightweight class-configuration YAML defining "Subtle Cue" and "Control Set"
   class IDs based on frequency and amplitude criteria.
4. Outputting `data/processed/class_config.yaml`.

Real Data Source:
- ESC-50: https://github.com/karolden/esc50 (via Hugging Face `esc50` dataset)
- UrbanSound8K: https://github.com/peterstern/UrbanSound8K (via Hugging Face `urbansound8k` dataset)
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import os
import json
import hashlib
import time
from pathlib import Path
import yaml
import numpy as np
import librosa
import torchaudio
from datasets import load_dataset

from utils.logger import get_logger, DataLoadError

logger = get_logger(__name__)


class DatasetType(Enum):
    ESC50 = "esc50"
    URBANSOUND8K = "urbansound8k"


@dataclass
class ClassDefinition:
    """Definition of a class with its acoustic properties."""
    class_id: int
    name: str
    dominant_freq_hz: float
    rms_dbfs: float
    is_subtle: bool
    is_control: bool
    dataset: DatasetType


class SubtleCueBuilder:
    """
    Builder for identifying Subtle Cue classes based on acoustic features.

    Criteria for Subtle Cue (from T021):
    - Dominant frequency > 8000 Hz OR
    - RMS amplitude < -40 dBFS
    """
    FREQ_THRESHOLD_HZ = 8000.0
    AMPLITUDE_THRESHOLD_DBFS = -40.0

    def __init__(self, dataset_type: DatasetType):
        self.dataset_type = dataset_type
        self.classes: Dict[int, ClassDefinition] = {}
        self.logger = get_logger(__name__)

    def load_and_analyze(self, subset: str = "default", max_files: Optional[int] = None) -> Dict[int, ClassDefinition]:
        """
        Load raw audio from the dataset, compute features, and classify classes.

        Args:
            subset: Dataset subset (e.g., "default" for ESC-50, "train" for UrbanSound8K).
            max_files: Maximum number of files to process (for testing/sampling).

        Returns:
            Dictionary mapping class_id to ClassDefinition.
        """
        self.logger.info(f"Starting feature extraction for {self.dataset_type.value}...")

        # Load dataset
        try:
            if self.dataset_type == DatasetType.ESC50:
                ds = load_dataset("esc50", split="train")
            elif self.dataset_type == DatasetType.URBANSOUND8K:
                ds = load_dataset("urbansold8k", split="train") # Note: HuggingFace ID might vary
            else:
                raise ValueError(f"Unsupported dataset type: {self.dataset_type}")
        except Exception as e:
            raise DataLoadError(f"Failed to load dataset {self.dataset_type.value}: {e}")

        # Process files
        file_count = 0
        class_samples: Dict[int, List[Tuple[np.ndarray, float]]] = {} # class_id -> list of (audio, sample_rate)

        for item in ds:
            if max_files and file_count >= max_files:
                break

            # Extract audio and metadata
            # HuggingFace 'esc50' and 'urbansound8k' usually provide 'audio' key with waveform and 'label'
            audio_data = item['audio']
            if audio_data is None:
                continue
            
            waveform = audio_data['array']
            sample_rate = audio_data['sampling_rate']
            class_id = int(item['label'])
            file_name = item.get('file', f"class_{class_id}_{file_count}")

            # Compute features
            freq_peak, rms_dbfs = self._compute_features(waveform, sample_rate)

            if class_id not in class_samples:
                class_samples[class_id] = []
            class_samples[class_id].append((freq_peak, rms_dbfs))

            file_count += 1

        # Aggregate per class
        for class_id, samples in class_samples.items():
            # Use median to be robust against outliers
            freqs = [s[0] for s in samples]
            rms_vals = [s[1] for s in samples]
            
            median_freq = float(np.median(freqs))
            median_rms = float(np.median(rms_vals))

            # Determine if subtle
            is_subtle = (median_freq > self.FREQ_THRESHOLD_HZ) or (median_rms < self.AMPLITUDE_THRESHOLD_DBFS)
            is_control = not is_subtle # Control set is the complement for this builder's scope

            # Get class name if available
            # ESC-50 has 'category' in metadata, UrbanSound8K has 'class' or similar
            class_name = self._get_class_name(class_id)

            self.classes[class_id] = ClassDefinition(
                class_id=class_id,
                name=class_name,
                dominant_freq_hz=median_freq,
                rms_dbfs=median_rms,
                is_subtle=is_subtle,
                is_control=is_control,
                dataset=self.dataset_type
            )
            self.logger.debug(f"Class {class_id} ({class_name}): Freq={median_freq:.1f}Hz, RMS={median_rms:.2f}dBFS, Subtle={is_subtle}")

        self.logger.info(f"Processed {file_count} files. Found {len(self.classes)} unique classes.")
        return self.classes

    def _compute_features(self, waveform: np.ndarray, sample_rate: int) -> Tuple[float, float]:
        """
        Compute dominant frequency (STFT peak) and amplitude (RMS) in dBFS.

        Args:
            waveform: 1D numpy array of audio samples.
            sample_rate: Sampling rate in Hz.

        Returns:
            Tuple of (dominant_freq_hz, rms_dbfs).
        """
        # Convert to mono if stereo
        if len(waveform.shape) > 1:
            waveform = np.mean(waveform, axis=1)

        # Compute RMS
        # RMS in dBFS: 20 * log10(rms / max_possible_amplitude)
        # Assuming normalized [-1, 1], max amplitude is 1.0
        rms = np.sqrt(np.mean(waveform ** 2))
        if rms == 0:
            rms_dbfs = -np.inf
        else:
            rms_dbfs = 20 * np.log10(rms)

        # Compute Dominant Frequency via STFT
        # Use a short window for transient detection
        n_fft = 2048
        hop_length = 512
        stft = librosa.stft(waveform, n_fft=n_fft, hop_length=hop_length)
        magnitude = np.abs(stft)

        # Find the bin with the maximum magnitude across all frames
        # This is a simple heuristic for "dominant" frequency in the file
        max_bin_idx = np.argmax(magnitude)
        # Convert bin index to frequency
        freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=n_fft)
        dominant_freq = freqs[max_bin_idx]

        return dominant_freq, rms_dbfs

    def _get_class_name(self, class_id: int) -> str:
        """Get human-readable class name."""
        if self.dataset_type == DatasetType.ESC50:
            esc50_categories = [
                "rain", "seagull", "cat", "frog", "cricket", "dog", "chicken", "rooster", "pig", "cow",
                "crow", "quacking", "airplane", "helicopter", "siren", "clock alarm", "clock bell",
                "baby cry", "cry", "scream", "sneeze", "snore", "wind", "thunder", "whale", "horse",
                "elephant", "bird chirping", "dog bark", "cat meow", "cough", "gunshot", "drill",
                "chainsaw", "vacuum cleaner", "electric shaver", "blender", "siren", "siren", "siren"
            ]
            # ESC-50 has 50 classes, indexed 0-49. The list above might be approximate.
            # Better to rely on the dataset's metadata if available, but here we use a fallback.
            # In a real implementation, we'd map from the dataset's label map.
            # For now, return a generic name.
            return f"esc50_class_{class_id}"
        elif self.dataset_type == DatasetType.URBANSOUND8K:
            urbansound_categories = [
                "air_conditioner", "car_horn", "children_playing", "dog_bark", "drilling",
                "engine_idling", "gun_shot", "jackhammer", "siren", "street_music"
            ]
            if 0 <= class_id < len(urbansound_categories):
                return urbansound_categories[class_id]
            return f"urbansound_class_{class_id}"
        return f"unknown_class_{class_id}"


class ControlSetBuilder:
    """
    Builder for identifying Control Set classes (low-frequency, sustained amplitude).

    Criteria (from T021b):
    - Low frequency (e.g., < 500 Hz)
    - Sustained amplitude (non-transient, high RMS, low variance in RMS)
    """
    FREQ_UPPER_LIMIT_HZ = 500.0
    RMS_LOWER_LIMIT_DBFS = -30.0 # Relatively loud
    # Transient detection: if the variance of RMS across frames is low, it's sustained.

    def __init__(self, dataset_type: DatasetType):
        self.dataset_type = dataset_type
        self.classes: Dict[int, ClassDefinition] = {}
        self.logger = get_logger(__name__)

    def load_and_analyze(self, subset: str = "default", max_files: Optional[int] = None) -> Dict[int, ClassDefinition]:
        """
        Load raw audio, compute features, and identify Control Set classes.
        """
        self.logger.info(f"Starting Control Set identification for {self.dataset_type.value}...")

        # Reuse logic from SubtleCueBuilder for loading, but apply different classification logic
        # For simplicity, we can reuse the same loading mechanism or call SubtleCueBuilder's load_and_analyze
        # and then filter. However, to avoid circularity or duplication, we'll implement a streamlined version.
        
        try:
            if self.dataset_type == DatasetType.ESC50:
                ds = load_dataset("esc50", split="train")
            elif self.dataset_type == DatasetType.URBANSOUND8K:
                ds = load_dataset("urbansound8k", split="train")
            else:
                raise ValueError(f"Unsupported dataset type: {self.dataset_type}")
        except Exception as e:
            raise DataLoadError(f"Failed to load dataset {self.dataset_type.value}: {e}")

        file_count = 0
        class_samples: Dict[int, List[Tuple[float, float, float]]] = {} # class_id -> list of (freq, rms, rms_var)

        for item in ds:
            if max_files and file_count >= max_files:
                break

            audio_data = item['audio']
            if audio_data is None:
                continue
            
            waveform = audio_data['array']
            sample_rate = audio_data['sampling_rate']
            class_id = int(item['label'])

            # Compute features with more detail for control set
            freq_peak, rms_dbfs, rms_variance = self._compute_control_features(waveform, sample_rate)

            if class_id not in class_samples:
                class_samples[class_id] = []
            class_samples[class_id].append((freq_peak, rms_dbfs, rms_variance))

            file_count += 1

        for class_id, samples in class_samples.items():
            freqs = [s[0] for s in samples]
            rms_vals = [s[1] for s in samples]
            rms_vars = [s[2] for s in samples]

            median_freq = float(np.median(freqs))
            median_rms = float(np.median(rms_vals))
            median_rms_var = float(np.median(rms_vars))

            # Control Set Criteria
            is_control = (
                median_freq < self.FREQ_UPPER_LIMIT_HZ and
                median_rms > self.RMS_LOWER_LIMIT_DBFS and
                median_rms_var < 1.0 # Low variance implies sustained
            )
            is_subtle = False # Control set is by definition not subtle in this context

            class_name = self._get_class_name(class_id)

            self.classes[class_id] = ClassDefinition(
                class_id=class_id,
                name=class_name,
                dominant_freq_hz=median_freq,
                rms_dbfs=median_rms,
                is_subtle=is_subtle,
                is_control=is_control,
                dataset=self.dataset_type
            )
            self.logger.debug(f"Control Class {class_id} ({class_name}): Freq={median_freq:.1f}Hz, RMS={median_rms:.2f}dBFS, Var={median_rms_var:.2f}, Control={is_control}")

        self.logger.info(f"Processed {file_count} files. Found {len(self.classes)} unique classes. Control classes: {sum(1 for c in self.classes.values() if c.is_control)}")
        return self.classes

    def _compute_control_features(self, waveform: np.ndarray, sample_rate: int) -> Tuple[float, float, float]:
        """
        Compute features specifically for control set detection.
        Returns: (dominant_freq, rms_dbfs, rms_variance)
        """
        if len(waveform.shape) > 1:
            waveform = np.mean(waveform, axis=1)

        # RMS
        rms = np.sqrt(np.mean(waveform ** 2))
        if rms == 0:
            rms_dbfs = -np.inf
        else:
            rms_dbfs = 20 * np.log10(rms)

        # STFT for frequency
        n_fft = 2048
        hop_length = 512
        stft = librosa.stft(waveform, n_fft=n_fft, hop_length=hop_length)
        magnitude = np.abs(stft)
        max_bin_idx = np.argmax(magnitude)
        freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=n_fft)
        dominant_freq = freqs[max_bin_idx]

        # RMS Variance (simplified: variance of frame-wise RMS)
        # Compute frame-wise RMS
        frame_length = int(0.05 * sample_rate) # 50ms frames
        hop = int(0.025 * sample_rate)
        frame_rms = librosa.feature.rms(y=waveform, frame_length=frame_length, hop_length=hop)[0]
        rms_variance = float(np.var(frame_rms))

        return dominant_freq, rms_dbfs, rms_variance

    def _get_class_name(self, class_id: int) -> str:
        if self.dataset_type == DatasetType.URBANSOUND8K:
            urbansound_categories = [
                "air_conditioner", "car_horn", "children_playing", "dog_bark", "drilling",
                "engine_idling", "gun_shot", "jackhammer", "siren", "street_music"
            ]
            if 0 <= class_id < len(urbansound_categories):
                return urbansound_categories[class_id]
        return f"unknown_class_{class_id}"


def get_binary_discrimination_mapping(
    subtle_classes: Set[int],
    control_classes: Set[int]
) -> Dict[str, List[int]]:
    """
    Generate the final mapping for class_config.yaml.
    """
    return {
        "subtle_classes": sorted(list(subtle_classes)),
        "control_classes": sorted(list(control_classes))
    }


def main():
    """
    Main entry point to generate class_config.yaml.
    """
    logger.info("Starting Subtle Cue Builder pipeline...")

    # Define output path
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "class_config.yaml"

    subtle_classes: Set[int] = set()
    control_classes: Set[int] = set()

    # Process ESC-50
    try:
        esc_builder = SubtleCueBuilder(DatasetType.ESC50)
        esc_classes = esc_builder.load_and_analyze()
        for cls in esc_classes.values():
            if cls.is_subtle:
                subtle_classes.add(cls.class_id)
            # Control set for ESC-50 is not explicitly defined in T021b, 
            # but T021b focuses on UrbanSound. We'll leave control_classes empty for ESC-50 
            # unless specified otherwise.
    except Exception as e:
        logger.error(f"Failed to process ESC-50: {e}")
        # Continue with other datasets

    # Process UrbanSound8K
    try:
        # Subtle Cue builder for UrbanSound
        us_subtle_builder = SubtleCueBuilder(DatasetType.URBANSOUND8K)
        us_subtle_classes = us_subtle_builder.load_and_analyze()
        for cls in us_subtle_classes.values():
            if cls.is_subtle:
                subtle_classes.add(cls.class_id)

        # Control Set builder for UrbanSound (T021b)
        us_control_builder = ControlSetBuilder(DatasetType.URBANSOUND8K)
        us_control_classes = us_control_builder.load_and_analyze()
        for cls in us_control_classes.values():
            if cls.is_control:
                control_classes.add(cls.class_id)
    except Exception as e:
        logger.error(f"Failed to process UrbanSound8K: {e}")

    # Generate mapping
    config_mapping = get_binary_discrimination_mapping(subtle_classes, control_classes)

    # Add metadata
    full_config = {
        "description": "Class configuration for Subtle Cue and Control Set detection.",
        "criteria": {
            "subtle": "Dominant freq > 8000 Hz OR RMS < -40 dBFS",
            "control": "Freq < 500 Hz AND RMS > -30 dBFS AND Low RMS variance"
        },
        "mapping": config_mapping
    }

    # Write YAML
    try:
        with open(output_file, 'w') as f:
            yaml.dump(full_config, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Successfully wrote class configuration to {output_file}")
        
        # Compute checksum for lineage
        with open(output_file, 'rb') as f:
            checksum = hashlib.sha256(f.read()).hexdigest()
        logger.info(f"Checksum for {output_file}: {checksum}")
        
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        raise

    return full_config


if __name__ == "__main__":
    main()
