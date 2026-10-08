#!/usr/bin/env python
"""
Unit tests for T030b: Pilot Variance Calculation.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Import the module under test
# We need to mock the calculate_clip_score function to avoid actual image processing
from code.utils import metrics
from code import code_030_pilot_variance as pilot_variance_module

# Mock the calculate_clip_score function
original_calculate_clip_score = metrics.calculate_clip_score

def mock_calculate_clip_score(image_path_1, image_path_2):
    """Mock function that returns a deterministic score based on file names."""
    # Return a fixed score for testing
    return [0.85]

@pytest.fixture
def mock_clip_score():
    """Fixture to mock calculate_clip_score."""
    metrics.calculate_clip_score = mock_calculate_clip_score
    yield
    metrics.calculate_clip_score = original_calculate_clip_score

@pytest.fixture
def temp_pilot_dirs():
    """Create temporary directories with mock image files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        teacher_dir = tmpdir_path / "teacher_baseline_images_pilot"
        tree_dir = tmpdir_path / "tree_generated_images_pilot"
        teacher_dir.mkdir()
        tree_dir.mkdir()
        
        # Create mock image files (empty files are fine for this test)
        for i in range(10):
            (teacher_dir / f"image_{i:04d}.png").touch()
            (tree_dir / f"image_{i:04d}.png").touch()
        
        yield teacher_dir, tree_dir

def test_load_image_paths(temp_pilot_dirs):
    """Test that load_image_paths correctly loads and sorts image files."""
    teacher_dir, tree_dir = temp_pilot_dirs
    
    teacher_paths = pilot_variance_module.load_image_paths(teacher_dir)
    tree_paths = pilot_variance_module.load_image_paths(tree_dir)
    
    assert len(teacher_paths) == 10
    assert len(tree_paths) == 10
    
    # Check sorting
    assert teacher_paths[0].name == "image_0000.png"
    assert teacher_paths[-1].name == "image_0009.png"

def test_calculate_variance(mock_clip_score, temp_pilot_dirs, tmp_path):
    """Test the calculate_variance function."""
    teacher_dir, tree_dir = temp_pilot_dirs
    output_path = tmp_path / "pilot_variance.json"
    
    result = pilot_variance_module.calculate_variance(
        teacher_dir, tree_dir, output_path
    )
    
    # Check that the result is a dictionary
    assert isinstance(result, dict)
    
    # Check that the variance is calculated (should be 0 because all scores are 0.85)
    assert "variance" in result
    assert result["variance"] == 0.0  # All scores are the same
    
    # Check other fields
    assert result["n_samples"] == 10
    assert result["mean_clip_score"] == 0.85
    assert result["status"] == "complete"
    
    # Check that the output file was written
    assert output_path.exists()
    with open(output_path) as f:
        saved_result = json.load(f)
    assert saved_result["variance"] == 0.0

def test_calculate_variance_with_mismatched_counts(temp_pilot_dirs):
    """Test that calculate_variance raises an error for mismatched image counts."""
    teacher_dir, tree_dir = temp_pilot_dirs
    # Add an extra image to tree_dir
    (tree_dir / "extra_image.png").touch()
    
    output_path = Path(tempfile.gettempdir()) / "test_variance.json"
    
    with pytest.raises(ValueError, match="Image count mismatch"):
        pilot_variance_module.calculate_variance(
            teacher_dir, tree_dir, output_path
        )

def test_calculate_variance_with_no_images(tmp_path):
    """Test that calculate_variance raises an error for empty directories."""
    teacher_dir = tmp_path / "teacher_empty"
    tree_dir = tmp_path / "tree_empty"
    teacher_dir.mkdir()
    tree_dir.mkdir()
    
    output_path = tmp_path / "pilot_variance.json"
    
    with pytest.raises(ValueError, match="No images found"):
        pilot_variance_module.calculate_variance(
            teacher_dir, tree_dir, output_path
        )

def test_calculate_variance_with_non_finite_scores(mock_clip_score, temp_pilot_dirs, tmp_path):
    """Test handling of non-finite scores."""
    teacher_dir, tree_dir = temp_pilot_dirs
    
    # Mock to return non-finite score for one image
    def mock_non_finite(image_path_1, image_path_2):
        if "image_0005" in image_path_1:
            return [float('nan')]
        return [0.85]
    
    with patch.object(metrics, 'calculate_clip_score', mock_non_finite):
        output_path = tmp_path / "pilot_variance.json"
        result = pilot_variance_module.calculate_variance(
            teacher_dir, tree_dir, output_path
        )
        
        # Should have 9 samples instead of 10
        assert result["n_samples"] == 9

def test_main_function(mock_clip_score, temp_pilot_dirs, tmp_path, capsys):
    """Test the main function."""
    teacher_dir, tree_dir = temp_pilot_dirs
    output_path = tmp_path / "pilot_variance.json"
    
    # Mock sys.argv
    test_args = [
        "030_pilot_variance.py",
        "--teacher-dir", str(teacher_dir),
        "--tree-dir", str(tree_dir),
        "--output", str(output_path),
        "--timeout", "300"
    ]
    
    with patch('sys.argv', test_args):
        pilot_variance_module.main()
    
    # Check that the output file was created
    assert output_path.exists()
    
    # Check stdout for result
    captured = capsys.readouterr()
    assert "variance" in captured.out
    assert "n_samples" in captured.out