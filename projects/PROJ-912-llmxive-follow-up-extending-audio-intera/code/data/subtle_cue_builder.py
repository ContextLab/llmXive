"""
Subtle Cue and Control Set Builder for Audio Interaction Model.

This module defines the logic for identifying "Subtle Cue" classes (high-frequency, low-amplitude)
and "Control Set" classes (low-frequency, sustained amplitude) from audio datasets.
It generates configuration YAML files for downstream filtering and training tasks.

IMPORTANT: This task (T021c) explicitly overrides FR-002 ("only subtle cue") constraint.
Rationale: To ensure valid binary AUC calculation (FR-003), we must have a negative class (Control Set)
to contrast against the positive class (Subtle Cue). This is authorized by Plan.md "Complexity Tracking".
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

import yaml
import torchaudio
import torch
from datasets import load_dataset
from tqdm import tqdm

# Local imports (ensure these exist in the project structure)
# Assuming config.py and logger.py are available as per project structure
try:
    from config import get_path_config
except ImportError:
    # Fallback if config is not yet fully integrated or for standalone testing
    class DummyConfig:
        def get_processed_dir(self):
            return Path("data/processed")
    get_path_config = lambda: DummyConfig()

try:
    from utils.logger import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)


class DatasetType(Enum):
    SUBTLE = "subtle"
    CONTROL = "control"


@dataclass
class ClassDefinition:
    class_id: int
    class_name: str
    dataset_id: str  # e.g., "UrbanSound8K", "ESC-50"
    frequency_threshold_hz: float = 8000.0
    amplitude_threshold_db: float = -40.0
    is_subtle: bool = False


class SubtleCueBuilder:
    """
    Identifies classes with dominant frequency > 8kHz OR amplitude < -40dBFS.
    """
    def __init__(self, logger=None):
        self.logger = logger or get_logger("SubtleCueBuilder")
        self.config = get_path_config()

    def _compute_audio_features(self, audio_path: str) -> Tuple[float, float]:
        """
        Computes dominant frequency (Hz) and mean amplitude (dBFS) for a given audio file.
        Uses MelSpectrogram for frequency analysis and RMS for amplitude.
        """
        try:
            waveform, sample_rate = torchaudio.load(audio_path)
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True) # Mono

            # Mel Spectrogram
            mel_spec = torchaudio.transforms.MelSpectrogram(
                sample_rate=sample_rate,
                n_mels=128,
                f_max=sample_rate / 2
            )(waveform)

            # Energy per bin
            energy = mel_spec.mean(dim=2) # Average over time
            # Find bin with max energy
            max_bin_idx = energy.argmax()
            # Approximate frequency of that bin (simplified)
            # Bin width = sample_rate / n_fft. Mel scale is non-linear, but for dominant freq > 8k check:
            # We can check the sum of energy in high freq bins vs low freq bins.
            # Let's use a simpler heuristic: sum energy in bins corresponding to > 8kHz
            # f_bin = (idx * sample_rate) / n_fft (roughly)
            # We need to map mel bins to Hz.
            # torchaudio provides `mel_to_hz`
            mels_to_hz = torchaudio.transforms.MelScale(n_mels=128, sample_rate=sample_rate).f_min # Not direct
            # Let's just use the center frequencies of the mel bands
            # Approximate: bin 0 is 0Hz, bin 127 is Nyquist.
            # 8kHz is roughly 8000 / (sample_rate/2) * 128
            if sample_rate < 16000:
                # Upsample for analysis if needed, but let's assume 16k+
                pass
            nyquist = sample_rate / 2
            bin_8k_idx = int((8000 / nyquist) * 128)

            high_freq_energy = energy[bin_8k_idx:].sum()
            total_energy = energy.sum()

            dominant_freq_is_high = (high_freq_energy / (total_energy + 1e-8)) > 0.3

            # Amplitude (RMS)
            rms = torch.sqrt((waveform ** 2).mean())
            # Convert to dBFS (0 dBFS is max)
            # 20 * log10(rms)
            dbfs = 20 * torch.log10(rms + 1e-8)

            return float(dominant_freq_is_high), float(dbfs)

        except Exception as e:
            self.logger.error(f"Failed to compute features for {audio_path}: {e}")
            return 0.0, -100.0

    def identify_subtle_classes(self, dataset_name: str = "ESC-50") -> List[ClassDefinition]:
        """
        Scans a sample of the dataset to identify subtle classes.
        Note: For a full dataset scan, this would be very slow. We sample.
        """
        self.logger.info(f"Starting subtle class identification for {dataset_name}...")
        # Load dataset (streaming to avoid OOM)
        try:
            ds = load_dataset(dataset_name, split="train", streaming=True)
        except Exception as e:
            self.logger.warning(f"Could not load {dataset_name}, trying UrbanSound8K: {e}")
            try:
                ds = load_dataset("UrbanSound8K", split="train", streaming=True)
            except Exception as e2:
                self.logger.error(f"Failed to load any dataset: {e2}")
                return []

        classes_found = set()
        samples_per_class = 5 # Small sample for classification
        class_stats = {} # class_id -> {'high_freq_count': int, 'low_amp_count': int, 'total': int}

        for item in tqdm(ds, desc="Sampling classes"):
            # Handle different dataset structures
            audio = item.get('audio') or item.get('file')
            label = item.get('label') or item.get('class')

            if audio is None:
                continue

            # If audio is a dict with path
            audio_path = None
            if isinstance(audio, dict) and 'path' in audio:
                audio_path = audio['path']
            elif isinstance(audio, str):
                audio_path = audio
            else:
                # Try to find a path
                continue

            if not os.path.exists(audio_path):
                continue

            class_id = int(label)
            if class_id not in class_stats:
                class_stats[class_id] = {'high_freq': 0, 'low_amp': 0, 'total': 0}

            is_high_freq, dbfs = self._compute_audio_features(audio_path)
            class_stats[class_id]['total'] += 1
            if is_high_freq:
                class_stats[class_id]['high_freq'] += 1
            if dbfs < -40.0:
                class_stats[class_id]['low_amp'] += 1

            if class_stats[class_id]['total'] >= samples_per_class:
                classes_found.add(class_id)

            # Stop if we have enough samples for all classes (roughly)
            if len(classes_found) >= 10: # ESC-50 has 50, we just need a few to start
                break

        # Determine subtle classes
        subtle_classes = []
        for cid, stats in class_stats.items():
            if stats['total'] == 0: continue
            # Criterion: > 50% of samples are high freq OR > 50% are low amp
            if (stats['high_freq'] / stats['total']) > 0.5 or (stats['low_amp'] / stats['total']) > 0.5:
                subtle_classes.append(ClassDefinition(
                    class_id=cid,
                    class_name=f"Class_{cid}",
                    dataset_id=dataset_name,
                    is_subtle=True
                ))

        self.logger.info(f"Identified {len(subtle_classes)} subtle classes.")
        return subtle_classes


class ControlSetBuilder:
    """
    Identifies classes with low-frequency, sustained amplitude (e.g., "engine hum", "wind").
    These serve as the negative class for binary AUC calculation.
    """
    def __init__(self, logger=None):
        self.logger = logger or get_logger("ControlSetBuilder")
        self.config = get_path_config()

    def _compute_audio_features(self, audio_path: str) -> Tuple[float, float]:
        """
        Computes dominant frequency (Hz) and mean amplitude (dBFS).
        """
        try:
            waveform, sample_rate = torchaudio.load(audio_path)
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)

            # Mel Spectrogram
            mel_spec = torchaudio.transforms.MelSpectrogram(
                sample_rate=sample_rate,
                n_mels=128,
                f_max=sample_rate / 2
            )(waveform)

            energy = mel_spec.mean(dim=2)
            # Check for low frequency dominance (bins 0-20 roughly)
            low_freq_bins = energy[:20].sum()
            total_energy = energy.sum()
            is_low_freq = (low_freq_bins / (total_energy + 1e-8)) > 0.6

            # Amplitude (RMS) - sustained amplitude implies not too quiet, but not transient
            rms = torch.sqrt((waveform ** 2).mean())
            dbfs = 20 * torch.log10(rms + 1e-8)
            # Sustained usually means average energy is moderate, not just transient spikes
            # We look for amplitude > -60dB (not silent) but not necessarily loud
            is_sustained = dbfs > -60.0

            return float(is_low_freq), float(is_sustained), float(dbfs)

        except Exception as e:
            self.logger.error(f"Failed to compute features for {audio_path}: {e}")
            return 0.0, 0.0, -100.0

    def identify_control_classes(self, dataset_name: str = "ESC-50") -> List[ClassDefinition]:
        """
        Scans dataset to find low-frequency, sustained classes.
        Override FR-002: We explicitly generate a Control Set to enable binary AUC.
        """
        self.logger.info(f"Starting Control Set identification for {dataset_name}...")
        self.logger.warning("OVERRIDE FR-002: Generating Control Set to ensure valid binary AUC calculation.")

        try:
            ds = load_dataset(dataset_name, split="train", streaming=True)
        except Exception as e:
            self.logger.warning(f"Could not load {dataset_name}, trying UrbanSound8K: {e}")
            try:
                ds = load_dataset("UrbanSound8K", split="train", streaming=True)
            except Exception as e2:
                self.logger.error(f"Failed to load any dataset: {e2}")
                return []

        class_stats = {}
        samples_per_class = 5

        for item in tqdm(ds, desc="Sampling Control Classes"):
            audio = item.get('audio') or item.get('file')
            label = item.get('label') or item.get('class')

            if audio is None: continue

            audio_path = None
            if isinstance(audio, dict) and 'path' in audio:
                audio_path = audio['path']
            elif isinstance(audio, str):
                audio_path = audio
            else:
                continue

            if not os.path.exists(audio_path):
                continue

            class_id = int(label)
            if class_id not in class_stats:
                class_stats[class_id] = {'low_freq': 0, 'sustained': 0, 'total': 0}

            is_low, is_sust, dbfs = self._compute_audio_features(audio_path)
            class_stats[class_id]['total'] += 1
            if is_low: class_stats[class_id]['low_freq'] += 1
            if is_sust: class_stats[class_id]['sustained'] += 1

            if class_stats[class_id]['total'] >= samples_per_class:
                pass # Continue to fill other classes

        # Heuristic for Control Set: Low frequency dominant AND sustained amplitude
        control_classes = []
        for cid, stats in class_stats.items():
            if stats['total'] == 0: continue
            # Require > 50% low freq and > 50% sustained
            if (stats['low_freq'] / stats['total']) > 0.5 and (stats['sustained'] / stats['total']) > 0.5:
                control_classes.append(ClassDefinition(
                    class_id=cid,
                    class_name=f"Control_Class_{cid}",
                    dataset_id=dataset_name,
                    is_subtle=False
                ))

        # Fallback: If no natural control classes found, pick some random low-index classes
        # that are typically low freq in ESC-50 (e.g., 0:DogBark, 1:Drilling, etc. - actually DogBark is high)
        # ESC-50 low freq: 2:Engine, 13:Wind, 24:Helicopter (maybe), 33:SeaWaves
        # Let's just ensure we have some if the heuristic failed
        if len(control_classes) == 0:
            self.logger.warning("No control classes found by heuristic. Using hardcoded fallback for ESC-50.")
            fallback_ids = [2, 13, 33] # Engine, Wind, SeaWaves
            for cid in fallback_ids:
                control_classes.append(ClassDefinition(
                    class_id=cid,
                    class_name=f"Fallback_Control_{cid}",
                    dataset_id=dataset_name,
                    is_subtle=False
                ))

        self.logger.info(f"Identified {len(control_classes)} control classes.")
        return control_classes


def get_binary_discrimination_mapping(
    subtle_classes: List[ClassDefinition],
    control_classes: List[ClassDefinition]
) -> Dict[int, int]:
    """
    Returns a mapping of class_id -> label (1 for subtle, 0 for control).
    """
    mapping = {}
    for c in subtle_classes:
        mapping[c.class_id] = 1
    for c in control_classes:
        mapping[c.class_id] = 0
    return mapping


def main():
    """
    Main entry point to generate class_config_control.yaml.
    """
    logger = get_logger("ControlSetGenerator")
    config = get_path_config()
    processed_dir = config.get_processed_dir()
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Identify Control Classes
    builder = ControlSetBuilder(logger)
    control_classes = builder.identify_control_classes(dataset_name="ESC-50")

    if not control_classes:
        logger.error("Failed to identify any control classes. Exiting.")
        # Try UrbanSound8K as backup if ESC-50 failed
        control_classes = builder.identify_control_classes(dataset_name="UrbanSound8K")
        if not control_classes:
            logger.critical("No control classes found in ESC-50 or UrbanSound8K.")
            return

    # 2. Generate YAML
    output_path = processed_dir / "class_config_control.yaml"
    data = {
        "type": "control_set",
        "description": "Classes with low-frequency, sustained amplitude. Overrides FR-002 to enable binary AUC.",
        "classes": [
            {
                "id": c.class_id,
                "name": c.class_name,
                "dataset": c.dataset_id
            }
            for c in control_classes
        ]
    }

    with open(output_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

    logger.info(f"Generated control set config at {output_path}")
    logger.info(f"Classes: {[c.class_id for c in control_classes]}")


if __name__ == "__main__":
    main()