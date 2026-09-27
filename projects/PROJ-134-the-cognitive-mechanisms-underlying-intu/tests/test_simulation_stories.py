"""
Tests for T014: Simulation Stories Generation.
"""
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from code.data.simulation_stories import (
    set_seed,
    load_mdes_report,
    validate_ground_truth_effect,
    load_blend_shape_config,
    generate_story_text,
    determine_salience_level,
    generate_moral_stories_dataset,
    generate_vr_logs_dataset,
    GROUND_TRUTH_EFFECT
)
from code.config import get_path

class TestSimulationStories:
    def test_set_seed(self):
        """Test that set_seed sets the random seed correctly."""
        set_seed(42)
        val1 = np.random.random()
        set_seed(42)
        val2 = np.random.random()
        assert val1 == val2, "Seed not set correctly"

    def test_validate_ground_truth_effect_valid(self):
        """Test validation with valid effect sizes."""
        # Should not raise
        validate_ground_truth_effect(0.0)
        validate_ground_truth_effect(0.8)
        validate_ground_truth_effect(2.0)

    def test_validate_ground_truth_effect_invalid(self):
        """Test validation with invalid effect sizes."""
        with pytest.raises(ValueError):
            validate_ground_truth_effect(-0.1)
        with pytest.raises(ValueError):
            validate_ground_truth_effect(2.1)

    def test_determine_salience_level(self):
        """Test salience level determination."""
        assert determine_salience_level(0) == "high"
        assert determine_salience_level(1) == "low"
        assert determine_salience_level(2) == "high"
        assert determine_salience_level(3) == "low"

    def test_generate_story_text(self):
        """Test story text generation."""
        text = generate_story_text(0, "high")
        assert "returns it immediately" in text or "finds a wallet" in text
        
        text = generate_story_text(1, "low")
        assert "remains silent" in text or "meeting" in text

    def test_generate_moral_stories_dataset_structure(self):
        """Test that the stories dataset has the correct structure."""
        df = generate_moral_stories_dataset(5)
        assert "participant_id" in df.columns
        assert "story_id" in df.columns
        assert "salience_level" in df.columns
        assert "story_text" in df.columns
        assert len(df) == 5 * 10  # 5 participants * 10 stories

    def test_generate_vr_logs_dataset_structure(self):
        """Test that the VR logs dataset has the correct structure."""
        stories_df = generate_moral_stories_dataset(2)
        logs_df = generate_vr_logs_dataset(stories_df)
        
        expected_cols = ["participant_id", "story_id", "salience_level", "response_time", "gaze_metrics", "judgment_rating", "ground_truth_effect"]
        assert all(col in logs_df.columns for col in expected_cols)
        assert len(logs_df) == len(stories_df)

    def test_ground_truth_effect_injection(self):
        """Test that the ground truth effect is correctly injected."""
        stories_df = generate_moral_stories_dataset(2)
        logs_df = generate_vr_logs_dataset(stories_df)
        
        assert all(logs_df["ground_truth_effect"] == GROUND_TRUTH_EFFECT)

    def test_response_time_distribution(self):
        """Test that response times follow the expected distribution."""
        stories_df = generate_moral_stories_dataset(50)
        logs_df = generate_vr_logs_dataset(stories_df)
        
        # Check that response times are positive
        assert (logs_df["response_time"] > 0).all()
        
        # Check that they are roughly in the expected range (LogNormal(3.5, 0.5))
        # Mean of lognormal is exp(mu + sigma^2/2) = exp(3.5 + 0.125) ≈ 35.5
        # We just check they are positive and not extreme outliers
        assert (logs_df["response_time"] < 200).all(), "Some response times are too large"

    def test_gaze_metrics_range(self):
        """Test that gaze metrics are in the expected range [0, 1]."""
        stories_df = generate_moral_stories_dataset(50)
        logs_df = generate_vr_logs_dataset(stories_df)
        
        assert (logs_df["gaze_metrics"] >= 0).all()
        assert (logs_df["gaze_metrics"] <= 1).all()

    def test_judgment_rating_range(self):
        """Test that judgment ratings are in the expected range [1, 5]."""
        stories_df = generate_moral_stories_dataset(50)
        logs_df = generate_vr_logs_dataset(stories_df)
        
        assert (logs_df["judgment_rating"] >= 1.0).all()
        assert (logs_df["judgment_rating"] <= 5.0).all()

    def test_salience_level_distribution(self):
        """Test that salience levels are balanced."""
        stories_df = generate_moral_stories_dataset(50)
        logs_df = generate_vr_logs_dataset(stories_df)
        
        high_count = (logs_df["salience_level"] == "high").sum()
        low_count = (logs_df["salience_level"] == "low").sum()
        
        # Should be roughly 50/50
        assert abs(high_count - low_count) <= 2, "Salience levels are not balanced"