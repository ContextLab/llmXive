import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Ensure project root is in path for imports if running from root
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.schema import MoralStory, MoralStoriesDataset, SalienceLevel
from code.utils.norms import validate_psychometric_norms, load_gervais_norms
from code.config import ensure_directories

class TestPsychometricNormValidation:
    """
    Unit tests for psychometric norm validation logic in T012.
    This test suite defines the interface for T017 (implementation of validation logic).
    It ensures that the simulation and ingestion pipeline correctly validates
    synthetic data against Gervais et al. (2011) norms.
    """

    @pytest.fixture
    def sample_moral_stories(self):
        """Create a sample dataset of MoralStories for testing."""
        # Simulate a dataset where the mean foundation scores are intentionally
        # shifted to test the validation boundaries.
        # Gervais norms (approx): Care ~3.0, Fairness ~2.8, Loyalty ~2.5, Authority ~2.4, Purity ~2.3
        # We create a dataset that is WITHIN 1 SD of these norms to expect PASS.
        
        stories = []
        for i in range(100):
            # Generate synthetic scores close to Gervais means
            scores = {
                "care": np.random.normal(3.0, 0.5),
                "fairness": np.random.normal(2.8, 0.5),
                "loyalty": np.random.normal(2.5, 0.5),
                "authority": np.random.normal(2.4, 0.5),
                "purity": np.random.normal(2.3, 0.5)
            }
            story = MoralStory(
                id=f"story_{i}",
                text="A sample moral dilemma story for testing purposes.",
                foundation_scores=scores,
                salience_level=SalienceLevel.HIGH
            )
            stories.append(story)
        
        return MoralStoriesDataset(stories=stories)

    @pytest.fixture
    def sample_moral_stories_outlier(self):
        """Create a dataset intentionally violating norms (mean > 1 SD away)."""
        stories = []
        for i in range(100):
            # Shift Care mean significantly (3.0 + 2.0 = 5.0, assuming SD ~0.8 in real data)
            scores = {
                "care": np.random.normal(5.0, 0.5), # Intentionally far from 3.0
                "fairness": np.random.normal(2.8, 0.5),
                "loyalty": np.random.normal(2.5, 0.5),
                "authority": np.random.normal(2.4, 0.5),
                "purity": np.random.normal(2.3, 0.5)
            }
            story = MoralStory(
                id=f"outlier_story_{i}",
                text="A sample story with outlier foundation scores.",
                foundation_scores=scores,
                salience_level=SalienceLevel.LOW
            )
            stories.append(story)
        
        return MoralStoriesDataset(stories=stories)

    def test_validation_interface_exists(self):
        """Verify that the validation function exists and has the correct signature."""
        # This test ensures T017 will implement a function matching this interface
        assert callable(validate_psychometric_norms)
        assert callable(load_gervais_norms)

    def test_validation_passes_within_tolerance(self, sample_moral_stories):
        """
        Test that validation passes when synthetic data is within 1 SD of Gervais norms.
        This defines the expected behavior for T017.
        """
        # Load real norms (or fallback to defined constants in norms.py if file missing)
        norms = load_gervais_norms()
        
        # Perform validation
        # Expected: Returns a dict with 'passed': True and details
        result = validate_psychometric_norms(sample_moral_stories, norms, tolerance_std=1.0)
        
        assert result["passed"] is True
        assert "care" in result["details"]
        # Assert that the mean difference is within tolerance
        for dim, details in result["details"].items():
            if details.get("mean_diff"):
                assert abs(details["mean_diff"]) <= details["tolerance"]

    def test_validation_fails_outside_tolerance(self, sample_moral_stories_outlier):
        """
        Test that validation fails when synthetic data deviates > 1 SD from Gervais norms.
        This defines the expected behavior for T017.
        """
        norms = load_gervais_norms()
        
        result = validate_psychometric_norms(sample_moral_stories_outlier, norms, tolerance_std=1.0)
        
        assert result["passed"] is False
        assert "care" in result["failed_dimensions"]
        assert result["details"]["care"]["mean_diff"] > result["details"]["care"]["tolerance"]

    def test_validation_handles_missing_dimensions(self):
        """Test that validation handles cases where a dimension is missing from the data."""
        stories = [
            MoralStory(
                id="missing_dim_story",
                text="Test story",
                foundation_scores={
                    "care": 3.0,
                    "fairness": 2.8,
                    "loyalty": 2.5,
                    "authority": 2.4,
                    # "purity" intentionally missing
                },
                salience_level=SalienceLevel.HIGH
            )
        ]
        dataset = MoralStoriesDataset(stories=stories)
        norms = load_gervais_norms()
        
        # Should not crash, but report failure or warning for missing dimension
        # For this test, we expect it to handle it gracefully (e.g., treat as 0 or NaN)
        # The specific behavior is defined by T017 implementation, but it must not raise an exception
        try:
            result = validate_psychometric_norms(dataset, norms, tolerance_std=1.0)
            # If it returns, check structure
            assert "passed" in result
        except KeyError as e:
            pytest.fail(f"Validation crashed on missing dimension: {e}")

    def test_load_gervais_norms_returns_expected_keys(self):
        """Verify that the loaded norms contain all 5 moral foundations."""
        norms = load_gervais_norms()
        expected_keys = ["care", "fairness", "loyalty", "authority", "purity"]
        for key in expected_keys:
            assert key in norms, f"Missing norm key: {key}"
            assert "mean" in norms[key], f"Missing 'mean' in norm for {key}"
            assert "std" in norms[key], f"Missing 'std' in norm for {key}"