"""
Unit tests for XAIOverlayGenerator.
"""

import pytest
import math
import sys
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from simulator.xai_generator import XAIOverlayGenerator
from simulator.interfaces.explainable import XAIOverlay


class TestXAIOverlayGenerator:
    """Tests for deterministic rule-based mapping."""

    def test_init_default_seed(self):
        """Test initialization with default seed."""
        gen = XAIOverlayGenerator()
        assert gen.seed == 42
        assert gen.rng is not None

    def test_init_custom_seed(self):
        """Test initialization with custom seed."""
        gen = XAIOverlayGenerator(seed=99)
        assert gen.seed == 99

    def test_invalid_difficulty_raises_error(self):
        """Test that difficulty outside 1-5 raises ValueError."""
        gen = XAIOverlayGenerator()
        with pytest.raises(ValueError):
            gen.generate_overlay(task_difficulty=0)
        with pytest.raises(ValueError):
            gen.generate_overlay(task_difficulty=6)

    @pytest.mark.parametrize("difficulty, expected_opacity", [
        (1, 0.15),
        (2, 0.30),
        (3, 0.50),
        (4, 0.70),
        (5, 0.90)
    ])
    def test_difficulty_to_opacity_mapping(self, difficulty, expected_opacity):
        """Test that difficulty maps to correct opacity."""
        gen = XAIOverlayGenerator()
        overlay = gen.generate_overlay(task_difficulty=difficulty)
        assert overlay.opacity == expected_opacity, \
            f"Expected opacity {expected_opacity} for difficulty {difficulty}, got {overlay.opacity}"

    @pytest.mark.parametrize("difficulty, expected_coverage", [
        (1, "small"),
        (2, "small"),
        (3, "medium"),
        (4, "medium"),
        (5, "large")
    ])
    def test_difficulty_to_coverage_mapping(self, difficulty, expected_coverage):
        """Test that difficulty maps to correct coverage area."""
        gen = XAIOverlayGenerator()
        overlay = gen.generate_overlay(task_difficulty=difficulty)
        assert overlay.coverage_area == expected_coverage, \
            f"Expected coverage {expected_coverage} for difficulty {difficulty}, got {overlay.coverage_area}"

    def test_bounding_box_valid_range(self):
        """Test that bounding box coordinates are within [0, 1]."""
        gen = XAIOverlayGenerator()
        overlay = gen.generate_overlay(task_difficulty=3)
        box = overlay.bounding_box
        assert 0.0 <= box["x"] <= 1.0
        assert 0.0 <= box["y"] <= 1.0
        assert 0.0 < box["width"] <= 1.0
        assert 0.0 < box["height"] <= 1.0
        # Ensure box stays within bounds
        assert box["x"] + box["width"] <= 1.0
        assert box["y"] + box["height"] <= 1.0

    def test_explanation_content(self):
        """Test that explanation text matches difficulty level."""
        gen = XAIOverlayGenerator()
        low = gen.generate_overlay(task_difficulty=1)
        high = gen.generate_overlay(task_difficulty=5)
        assert "Low complexity" in low.explanation
        assert "High complexity" in high.explanation

    def test_confidence_score_trend(self):
        """Test that confidence score decreases as difficulty increases."""
        gen = XAIOverlayGenerator()
        low = gen.generate_overlay(task_difficulty=1)
        high = gen.generate_overlay(task_difficulty=5)
        assert low.confidence_score > high.confidence_score

    def test_batch_generation(self):
        """Test generating a batch of overlays."""
        gen = XAIOverlayGenerator()
        difficulties = [1, 3, 5]
        overlays = gen.generate_batch(difficulties)
        assert len(overlays) == 3
        for i, overlay in enumerate(overlays):
            assert isinstance(overlay, XAIOverlay)
            # Verify specific difficulty mapping for this overlay
            expected_diff = difficulties[i]
            assert overlay.metadata["difficulty"] == expected_diff

    def test_serialization(self):
        """Test that overlay can be serialized to dict and JSON."""
        gen = XAIOverlayGenerator()
        overlay = gen.generate_overlay(task_difficulty=3)
        d = gen.to_dict(overlay)
        assert "overlay_id" in d
        assert "bounding_box" in d
        assert "opacity" in d

        json_str = gen.to_json(overlay)
        assert "overlay_id" in json_str
        assert "bounding_box" in json_str

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        gen1 = XAIOverlayGenerator(seed=123)
        gen2 = XAIOverlayGenerator(seed=123)

        o1 = gen1.generate_overlay(task_difficulty=3, task_id="test")
        o2 = gen2.generate_overlay(task_difficulty=3, task_id="test")

        # Bounding boxes should be identical due to seeded RNG
        assert o1.bounding_box["x"] == o2.bounding_box["x"]
        assert o1.bounding_box["y"] == o2.bounding_box["y"]
        assert o1.bounding_box["width"] == o2.bounding_box["width"]
        assert o1.bounding_box["height"] == o2.bounding_box["height"]

        # But different seed should produce different results
        gen3 = XAIOverlayGenerator(seed=456)
        o3 = gen3.generate_overlay(task_difficulty=3, task_id="test")
        assert o1.bounding_box["x"] != o3.bounding_box["x"] or \
               o1.bounding_box["y"] != o3.bounding_box["y"]