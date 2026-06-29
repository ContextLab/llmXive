"""
Unit tests for experience classification module.

Tests the version-controlled experience thresholds and classification logic.
"""

import pytest
import sys
from pathlib import Path

# Add code directory to path for imports
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from analysis.experience import (
    classify_experience,
    get_thresholds,
    ExperienceThresholds,
    EXPERIENCE_THRESHOLD_VERSION,
    NOVICE_MAX,
    INTERMEDIATE_MAX
)


class TestExperienceClassification:
    """Test suite for experience classification functions."""
    
    def test_novice_classifications(self):
        """Test that values < 2 years are classified as novice."""
        test_values = [0, 0.5, 1, 1.5, 1.9, 1.99]
        for years in test_values:
            assert classify_experience(years) == "novice"
    
    def test_intermediate_classifications(self):
        """Test that values 2-5 years are classified as intermediate."""
        test_values = [2, 2.5, 3, 3.5, 4, 4.5, 4.99]
        for years in test_values:
            assert classify_experience(years) == "intermediate"
    
    def test_expert_classifications(self):
        """Test that values > 5 years are classified as expert."""
        test_values = [5, 5.01, 6, 7, 10, 20]
        for years in test_values:
            assert classify_experience(years) == "expert"
    
    def test_boundary_conditions(self):
        """Test exact boundary values."""
        assert classify_experience(NOVICE_MAX) == "intermediate"
        assert classify_experience(INTERMEDIATE_MAX) == "expert"
    
    def test_negative_years_raises_error(self):
        """Test that negative years raise ValueError."""
        with pytest.raises(ValueError):
            classify_experience(-1)
        with pytest.raises(ValueError):
            classify_experience(-0.5)
    
    def test_invalid_type_raises_error(self):
        """Test that non-numeric types raise TypeError."""
        with pytest.raises(TypeError):
            classify_experience("5")
        with pytest.raises(TypeError):
            classify_experience(None)
        with pytest.raises(TypeError):
            classify_experience([2])
    
    def test_thresholds_version(self):
        """Test that version is properly set."""
        assert EXPERIENCE_THRESHOLD_VERSION == "1.0"
    
    def test_get_thresholds_returns_correct_structure(self):
        """Test that get_thresholds returns expected dict structure."""
        thresholds = get_thresholds()
        assert "version" in thresholds
        assert "novice_max" in thresholds
        assert "intermediate_max" in thresholds
        assert "expert_min" in thresholds
        assert thresholds["version"] == EXPERIENCE_THRESHOLD_VERSION
        assert thresholds["novice_max"] == NOVICE_MAX
        assert thresholds["intermediate_max"] == INTERMEDIATE_MAX
        assert thresholds["expert_min"] == INTERMEDIATE_MAX
    
    def test_experience_thresholds_dataclass(self):
        """Test ExperienceThresholds dataclass instantiation and classification."""
        thresholds = ExperienceThresholds()
        assert thresholds.version == EXPERIENCE_THRESHOLD_VERSION
        assert thresholds.novice_max == NOVICE_MAX
        assert thresholds.intermediate_max == INTERMEDIATE_MAX
        
        # Test classify method
        assert thresholds.classify(1) == "novice"
        assert thresholds.classify(3) == "intermediate"
        assert thresholds.classify(7) == "expert"
    
    def test_float_input(self):
        """Test that float inputs are handled correctly."""
        assert classify_experience(1.5) == "novice"
        assert classify_experience(2.5) == "intermediate"
        assert classify_experience(5.5) == "expert"
    
    def test_zero_years(self):
        """Test that zero years is classified as novice."""
        assert classify_experience(0) == "novice"