"""
Subtle Cue and Control Set Builders for Audio Interaction Model.

This module defines the criteria for "Subtle Cue" (high frequency, low amplitude)
and "Control Set" (low frequency, high amplitude) classes. It provides builders
to generate these datasets and maps class names to dataset IDs for binary discrimination.

The Control Set specifically uses UrbanSound8K classes as per FR-002.
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from utils.logger import get_logger

logger = get_logger(__name__)


class DatasetType(Enum):
    """Enum representing the source dataset for a class definition."""
    ESC_50 = "esc_50"
    AUDIOSET = "audioset"
    URBANSOUND8K = "urbansound8k"


@dataclass
class ClassDefinition:
    """
    Definition of a single audio class for the purpose of filtering.

    Attributes:
        name: Human-readable class name (e.g., "glass breaking").
        dataset_id: The integer ID of the class in the source dataset.
        dataset_type: The source dataset (ESC-50, UrbanSound8K, etc.).
        description: Brief description of the acoustic properties.
        is_subtle: True if this class belongs to the Subtle Cue set.
        is_control: True if this class belongs to the Control Set.
    """
    name: str
    dataset_id: int
    dataset_type: DatasetType
    description: str
    is_subtle: bool = False
    is_control: bool = False


class SubtleCueBuilder:
    """
    Builder for the 'Subtle Cue' dataset.
    Defines classes with high-frequency transients (>8kHz) or low amplitude (<-40dBFS).
    """

    # ESC-50 Class IDs for Subtle Cues (Approximate based on acoustic properties)
    # Source: https://github.com/karolden/esc50
    SUBTLE_CLASSES = [
        ClassDefinition(
            name="glass breaking",
            dataset_id=14,
            dataset_type=DatasetType.ESC_50,
            description="High-frequency transient, sharp sound.",
            is_subtle=True
        ),
        ClassDefinition(
            name="alarm",
            dataset_id=2,
            dataset_type=DatasetType.ESC_50,
            description="High-pitched, repetitive, often high frequency.",
            is_subtle=True
        ),
        ClassDefinition(
            name="whistle",
            dataset_id=44,
            dataset_type=DatasetType.ESC_50,
            description="Pure high-frequency tone.",
            is_subtle=True
        ),
        ClassDefinition(
            name="cricket",
            dataset_id=11,
            dataset_type=DatasetType.ESC_50,
            description="High-frequency chirping, often low amplitude in distance.",
            is_subtle=True
        ),
        ClassDefinition(
            name="chainsaw",
            dataset_id=7,
            dataset_type=DatasetType.ESC_50,
            description="High frequency mechanical noise.",
            is_subtle=True
        ),
        ClassDefinition(
            name="siren",
            dataset_id=38,
            dataset_type=DatasetType.ESC_50,
            description="High frequency sweeping tone.",
            is_subtle=True
        ),
    ]

    def __init__(self):
        self.classes = self.SUBTLE_CLASSES
        logger.info(f"Initialized SubtleCueBuilder with {len(self.classes)} classes.")

    def get_class_ids(self) -> Set[int]:
        """Return the set of dataset IDs for subtle cue classes."""
        return {c.dataset_id for c in self.classes}

    def get_class_names(self) -> List[str]:
        """Return the list of class names for subtle cue classes."""
        return [c.name for c in self.classes]

    def get_filter_criteria(self) -> Dict[str, any]:
        """
        Returns the filtering criteria used to define this set.
        Useful for logging or documentation.
        """
        return {
            "frequency_threshold_hz": 8000,
            "amplitude_threshold_dbfs": -40,
            "description": "High-frequency transients or low-amplitude events."
        }


class ControlSetBuilder:
    """
    Builder for the 'Control Set' dataset.
    Uses UrbanSound8K classes to define low-frequency, high-amplitude events.
    These serve as the binary discrimination counterpart to Subtle Cues.

    FR-002 Scope Extension: Explicitly maps UrbanSound8K class names to IDs.
    """

    # UrbanSound8K Class IDs (0-9)
    # Source: https://urbansounddataset.weebly.com/urbansound8k.html
    # Mapping: 0:Air_conditioner, 1:Car_horn, 2:Children_playing, 3:Dog_bark,
    #          4:Drilling, 5:Engine_idling, 6:Gun_shot, 7:Jackhammer,
    #          8:Siren, 9:Street_music
    #
    # Selection Criteria: Low frequency (rumble, hum) and High amplitude (loud, mechanical).
    # "Engine idling" (5) is a classic low-freq, high-amplitude hum.
    # "Drilling" (4) and "Jackhammer" (7) are loud, low-freq mechanical impacts.
    # "Car_horn" (1) is loud but often mid/high freq, but can be included for amplitude.
    # "Street_music" (9) is variable, often excluded for purity, but can be low freq bass.
    #
    # Primary Selection for "Low Freq, High Amp":
    CONTROL_CLASSES = [
        ClassDefinition(
            name="engine_idling",
            dataset_id=5,
            dataset_type=DatasetType.URBANSOUND8K,
            description="Low-frequency hum of a running car engine.",
            is_control=True
        ),
        ClassDefinition(
            name="drilling",
            dataset_id=4,
            dataset_type=DatasetType.URBANSOUND8K,
            description="Loud, low-frequency mechanical drilling sound.",
            is_control=True
        ),
        ClassDefinition(
            name="jackhammer",
            dataset_id=7,
            dataset_type=DatasetType.URBANSOUND8K,
            description="High-amplitude, low-frequency percussive noise.",
            is_control=True
        ),
        ClassDefinition(
            name="car_horn",
            dataset_id=1,
            dataset_type=DatasetType.URBANSOUND8K,
            description="High-amplitude, mid-to-low frequency warning sound.",
            is_control=True
        ),
    ]

    def __init__(self):
        self.classes = self.CONTROL_CLASSES
        logger.info(f"Initialized ControlSetBuilder with {len(self.classes)} classes from UrbanSound8K.")

    def get_class_ids(self) -> Set[int]:
        """Return the set of dataset IDs for control set classes."""
        return {c.dataset_id for c in self.classes}

    def get_class_names(self) -> List[str]:
        """Return the list of class names for control set classes."""
        return [c.name for c in self.classes]

    def get_filter_criteria(self) -> Dict[str, any]:
        """
        Returns the filtering criteria used to define this set.
        """
        return {
            "frequency_characteristic": "low",
            "amplitude_characteristic": "high",
            "source_dataset": "UrbanSound8K",
            "description": "Low-frequency, high-amplitude events for binary discrimination."
        }


def get_binary_discrimination_mapping() -> Dict[str, Dict[str, any]]:
    """
    Generates the explicit mapping of class names to dataset IDs for binary discrimination.

    Returns:
        A dictionary containing:
        - 'subtle': List of {name, id, dataset} for subtle cues.
        - 'control': List of {name, id, dataset} for control set.
        - 'ids_only': Dict with sets of IDs for filtering logic.
    """
    subtle_builder = SubtleCueBuilder()
    control_builder = ControlSetBuilder()

    subtle_list = [
        {"name": c.name, "id": c.dataset_id, "dataset": c.dataset_type.value}
        for c in subtle_builder.classes
    ]

    control_list = [
        {"name": c.name, "id": c.dataset_id, "dataset": c.dataset_type.value}
        for c in control_builder.classes
    ]

    mapping = {
        "subtle": subtle_list,
        "control": control_list,
        "ids_only": {
            "subtle_ids": subtle_builder.get_class_ids(),
            "control_ids": control_builder.get_class_ids()
        }
    }

    logger.info("Generated binary discrimination mapping.")
    return mapping


def main():
    """
    Entry point to print the configuration for the Subtle Cue and Control sets.
    Useful for verification before running the data loader.
    """
    print("=== Subtle Cue & Control Set Configuration ===\n")

    mapping = get_binary_discrimination_mapping()

    print("SUBTLE CUE CLASSES (High Freq / Low Amp):")
    for item in mapping["subtle"]:
        print(f"  - {item['name']} (ID: {item['id']}, Dataset: {item['dataset']})")

    print("\nCONTROL SET CLASSES (Low Freq / High Amp - UrbanSound8K):")
    for item in mapping["control"]:
        print(f"  - {item['name']} (ID: {item['id']}, Dataset: {item['dataset']})")

    print("\nID SETS:")
    print(f"  Subtle IDs: {mapping['ids_only']['subtle_ids']}")
    print(f"  Control IDs: {mapping['ids_only']['control_ids']}")

    return mapping


if __name__ == "__main__":
    main()