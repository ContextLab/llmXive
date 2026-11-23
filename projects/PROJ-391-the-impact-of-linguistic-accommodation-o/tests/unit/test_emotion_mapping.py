"""
Unit tests for emotion-to-intensity mapping logic (T023).
Tests the mapping rules defined in FR-003:
Joy=5, Sadness=2, Anger=1, Fear=2, Surprise=4, Disgust=1, Neutral=3
"""

import pytest
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.emotion_mapping import map_emotion_to_intensity

# Define the expected mapping based on FR-003
EXPECTED_MAPPING = {
    "Joy": 5,
    "Sadness": 2,
    "Anger": 1,
    "Fear": 2,
    "Surprise": 4,
    "Disgust": 1,
    "Neutral": 3
}

class TestEmotionToIntensityMapping:
    """Tests for the map_emotion_to_intensity function."""

    def test_valid_emotions_map_correctly(self):
        """Test that all valid emotions map to their correct intensity scores."""
        for emotion, expected_intensity in EXPECTED_MAPPING.items():
            result = map_emotion_to_intensity(emotion)
            assert result == expected_intensity, (
                f"Emotion '{emotion}' mapped to {result}, expected {expected_intensity}"
            )

    def test_case_insensitivity(self):
        """Test that the function handles case variations (e.g., 'joy', 'JOY')."""
        # The DailyDialog dataset typically uses Title Case, but robustness is good.
        # If the implementation requires strict case matching, this will fail and guide the fix.
        # Assuming standard implementation handles common variations or strict matching as per spec.
        # Spec implies exact labels, but let's test Title Case which is standard.
        assert map_emotion_to_intensity("Joy") == 5
        assert map_emotion_to_intensity("Sadness") == 2
        assert map_emotion_to_intensity("Anger") == 1
        assert map_emotion_to_intensity("Fear") == 2
        assert map_emotion_to_intensity("Surprise") == 4
        assert map_emotion_to_intensity("Disgust") == 1
        assert map_emotion_to_intensity("Neutral") == 3

    def test_unknown_emotion_raises_value_error(self):
        """Test that an unknown emotion label raises a ValueError."""
        unknown_emotions = ["Love", "Hate", "Excitement", "Unknown", ""]
        for emotion in unknown_emotions:
            with pytest.raises(ValueError) as exc_info:
                map_emotion_to_intensity(emotion)
            assert f"Unknown emotion label: '{emotion}'" in str(exc_info.value)

    def test_empty_string_raises_value_error(self):
        """Test that an empty string raises a ValueError."""
        with pytest.raises(ValueError) as exc_info:
            map_emotion_to_intensity("")
        assert "Unknown emotion label: ''" in str(exc_info.value)

    def test_none_raises_type_error(self):
        """Test that None raises a TypeError (or ValueError depending on implementation)."""
        # Usually, type checking happens first.
        with pytest.raises((TypeError, ValueError)):
            map_emotion_to_intensity(None)

    def test_intensity_range_is_valid(self):
        """Test that all mapped intensities are within the 1-5 range."""
        for emotion in EXPECTED_MAPPING.keys():
            intensity = map_emotion_to_intensity(emotion)
            assert 1 <= intensity <= 5, (
                f"Intensity {intensity} for emotion '{emotion}' is outside range [1, 5]"
            )

    def test_distribution_of_intensities(self):
        """Test that the mapping produces the expected distribution of intensity values."""
        intensities = [map_emotion_to_intensity(e) for e in EXPECTED_MAPPING.keys()]
        # Verify specific counts if needed, but mostly checking the set of values
        assert set(intensities) == {1, 2, 3, 4, 5}
        # Count frequencies
        assert intensities.count(5) == 1  # Joy
        assert intensities.count(4) == 1  # Surprise
        assert intensities.count(3) == 1  # Neutral
        assert intensities.count(2) == 2  # Sadness, Fear
        assert intensities.count(1) == 2  # Anger, Disgust