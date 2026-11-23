"""
Unit tests for baseline metrics calculation.
"""
import pytest
import json
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from metrics.baseline import (
    calculate_motion_artifact_score,
    generate_random_noise_video,
    save_baseline_scores,
    run_baseline_calculation,
    OUTPUT_FILE,
    DEFAULT_VIDEO_FRAMES,
    DEFAULT_VIDEO_WIDTH,
    DEFAULT_VIDEO_HEIGHT
)
from utils.errors import fail_loudly


class TestBaselineCalculation:
    """Test cases for baseline score calculation."""

    def test_motion_artifact_score_range(self, tmp_path):
        """Test that motion artifact score is in [0, 1] range."""
        # Generate a noise video
        video_path = generate_random_noise_video(
            output_path=tmp_path / "test_noise.mp4",
            num_frames=10
        )
        
        # Calculate score
        score = calculate_motion_artifact_score(video_path)
        
        # Assert score is in valid range
        assert 0.0 <= score <= 1.0, f"Score {score} is not in [0, 1] range"

    def test_noise_video_high_score(self, tmp_path):
        """Test that random noise video produces high motion artifact score."""
        # Generate a noise video
        video_path = generate_random_noise_video(
            output_path=tmp_path / "test_noise_high.mp4",
            num_frames=20
        )
        
        # Calculate score
        score = calculate_motion_artifact_score(video_path)
        
        # For random noise, score should be relatively high (> 0.5)
        # because consecutive frames are completely uncorrelated
        assert score > 0.5, f"Noise video should have high motion artifact score, got {score}"

    def test_save_baseline_scores(self, tmp_path):
        """Test that baseline scores are saved correctly."""
        test_score = 0.85
        output_file = tmp_path / "test_baseline.json"
        
        save_baseline_scores(test_score, output_file)
        
        # Verify file exists
        assert output_file.exists(), "Baseline scores file was not created"
        
        # Verify content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "baseline_score" in data, "Missing baseline_score in output"
        assert data["baseline_score"] == test_score, f"Score mismatch: expected {test_score}, got {data['baseline_score']}"
        assert "video_specs" in data, "Missing video_specs in output"

    def test_run_baseline_calculation(self, tmp_path, monkeypatch):
        """Test the full baseline calculation pipeline."""
        # Monkeypatch the output path
        monkeypatch.setattr("metrics.baseline.OUTPUT_FILE", tmp_path / "baseline_test.json")
        monkeypatch.setattr("metrics.baseline.TEMP_VIDEO_FILE", tmp_path / "temp_test.mp4")
        
        # Run the pipeline
        result = run_baseline_calculation()
        
        # Verify result structure
        assert "baseline_score" in result, "Missing baseline_score in result"
        assert "output_file" in result, "Missing output_file in result"
        
        # Verify score is valid
        assert 0.0 <= result["baseline_score"] <= 1.0, "Invalid baseline score"
        
        # Verify output file exists
        output_file = Path(result["output_file"])
        assert output_file.exists(), "Output file was not created"

    def test_baseline_score_consistency(self, tmp_path):
        """Test that baseline scores are consistent across runs for same seed."""
        # Set random seed for reproducibility
        np.random.seed(42)
        video_path1 = generate_random_noise_video(
            output_path=tmp_path / "test_consistent1.mp4",
            num_frames=15
        )
        score1 = calculate_motion_artifact_score(video_path1)
        
        # Reset seed and regenerate
        np.random.seed(42)
        video_path2 = generate_random_noise_video(
            output_path=tmp_path / "test_consistent2.mp4",
            num_frames=15
        )
        score2 = calculate_motion_artifact_score(video_path2)
        
        # Scores should be identical (or very close due to floating point)
        assert abs(score1 - score2) < 1e-6, f"Inconsistent scores: {score1} vs {score2}"

    def test_single_frame_video_fails(self, tmp_path):
        """Test that a single-frame video raises an error."""
        video_path = generate_random_noise_video(
            output_path=tmp_path / "test_single.mp4",
            num_frames=1
        )
        
        with pytest.raises(Exception) as exc_info:
            calculate_motion_artifact_score(video_path)
        
        assert "fewer than 2 frames" in str(exc_info.value).lower()

    def test_invalid_video_path_fails(self, tmp_path):
        """Test that an invalid video path raises an error."""
        invalid_path = tmp_path / "nonexistent.mp4"
        
        with pytest.raises(Exception) as exc_info:
            calculate_motion_artifact_score(invalid_path)
        
        assert "Failed to open" in str(exc_info.value)